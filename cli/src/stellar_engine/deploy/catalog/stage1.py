# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Stage 1 steps of the deploy, from the DDG Stage 1 section.

Stage 1 reads the outputs that Stage 0 wrote, renders its workspace, needs
billing access for the stage service account or the tenant projects when
Stage 0 manages no billing IAM, applies, and writes the inputs of Stages 2
and 3. A billing step that the deployer cannot do hands off to another
identity instead of failing.
"""

from stellar_engine import fsutil
from stellar_engine import iam_diff
from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import derive
from stellar_engine.deploy import apply
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import remedies
from stellar_engine.deploy.catalog import common
from stellar_engine.gcp import api
from stellar_engine.preflight import checks

Status = model.StepStatus
Kind = model.StepKind
STAGE = "1"
DDG = "docs/ddg.md#stage-1---resource-management"
# Linking projects needs only Billing Account User; the DDG grants the
# broader Billing Account Administrator.
BILLING_ROLE = checks.BILLING_USER_ROLE
APPLY_REMEDIES = (
    remedies.STATE_LOCK,
    remedies.BACKEND_INIT_REQUIRED,
    remedies.SA_PROPAGATION,
    remedies.KMS_SERVICE_AGENT,
    remedies.IL5_GCS_SERVICE_AGENT,
    remedies.API_DISABLED,
    remedies.PROJECT_ID_TAKEN,
    remedies.BILLING_UNLINKED,
    remedies.ADC_QUOTA_PROJECT,
)


# s1.outputs


def _outputs_bucket(ctx: model.Context) -> str:
    """Returns the bucket that holds the Stage 0 outputs."""
    return naming.state_bucket(ctx.answers.prefix, "outputs")


def _inputs() -> tuple[str, ...]:
    """Returns the Stage 0 outputs that Stage 1 reads."""
    return workspace_lib.OUTPUT_LINKS[paths.RESMAN]


def _explain_outputs(ctx: model.Context) -> str:
    """Explains the copy of the Stage 0 outputs."""
    bucket = _outputs_bucket(ctx)
    return (
        "Copies the Stage 0 outputs that Stage 1 reads from "
        f"gs://{bucket} into {ctx.env.fast_config}, as the DDG Stage 1 "
        "gcloud storage cp step does. A deploy on the machine that applied "
        "Stage 0 finds them there already. Fallback: gcloud storage cp "
        f"gs://{bucket}/<file> into the same path under fast-config/ for "
        f"{', '.join(_inputs())}."
    )


def _check_outputs(ctx: model.Context) -> model.Verdict:
    """Checks that the Stage 0 outputs are under `fast-config/`."""
    missing = common.missing_outputs(ctx, _inputs())
    if missing:
        return model.Verdict(
            Status.PENDING, f"fast-config/ lacks {', '.join(missing)}."
        )
    return model.Verdict(
        Status.DONE, "The Stage 0 outputs are in fast-config/."
    )


def _read_output(ctx: model.Context, name: str) -> api.ObjectData:
    """Reads one Stage 0 output, as the deployer or the Stage 1 account."""
    bucket = _outputs_bucket(ctx)
    account = probe_lib.backend(ctx.answers.prefix, STAGE).service_account
    try:
        found = probe_lib.read_object_as(ctx.cloud, bucket, name, account)
    except api.AccessDeniedError as error:
        target = ctx.env.fast_config / name
        raise model.BlockedError(
            f"Cannot read gs://{bucket}/{name}: {error}",
            remedy=f"gcloud storage cp gs://{bucket}/{name} {target}",
        ) from error
    if found is None:
        raise model.BlockedError(
            f"gs://{bucket}/{name} does not exist.",
            remedy="Run the final Stage 0 apply, which writes it.",
        )
    return found


def _run_outputs(ctx: model.Context) -> None:
    """Copies the missing Stage 0 outputs into `fast-config/`."""
    for name in common.missing_outputs(ctx, _inputs()):
        found = _read_output(ctx, name)
        target = ctx.env.fast_config / name
        fsutil.write_private(target, found.data)
        ctx.say(f"Copied gs://{_outputs_bucket(ctx)}/{name} to {target}.")


# s1.billing_grant


def _resman_member(ctx: model.Context) -> str:
    """Returns the IAM member of the Stage 1 service account."""
    account = probe_lib.backend(ctx.answers.prefix, STAGE).service_account
    return naming.principal(naming.SERVICE_ACCOUNT, account)


def _grant_command(ctx: model.Context) -> str:
    """Returns the gcloud command that grants the billing role by hand."""
    return (
        "gcloud billing accounts add-iam-policy-binding "
        f"{ctx.answers.billing.account_id} --member={_resman_member(ctx)} "
        f"--role={BILLING_ROLE}"
    )


def _billing_mode(ctx: model.Context) -> str:
    """Describes who grants the stage service accounts billing access."""
    no_iam = ctx.answers.billing.no_iam
    is_org_level = ctx.answers.billing.is_org_level
    if repo_lib.billing_export_created(
        no_iam=no_iam, is_org_level=is_org_level
    ):
        return "Stage 0 grants the billing roles on the organization"
    if repo_lib.billing_iam_on_account(
        no_iam=no_iam, is_org_level=is_org_level
    ):
        return "Stage 0 grants the billing roles on the billing account"
    return (
        "billing.no_iam is true, so no stage grants billing roles and "
        "someone outside Terraform grants them"
    )


def _explain_billing_grant(ctx: model.Context) -> str:
    """Explains the billing grant and who grants billing roles here."""
    return (
        f"Grants {BILLING_ROLE} on billing account "
        f"{ctx.answers.billing.account_id} to {_resman_member(ctx)}, so "
        "Stage 1 can link its projects, as the DDG Stage 1 note on external "
        "billing accounts asks. The DDG names Billing Account "
        "Administrator, but linking projects needs only Billing Account "
        f"User. In this deployment {_billing_mode(ctx)}. Fallback: "
        f"{_grant_command(ctx)}."
    )


def _external_grant(ctx: model.Context) -> bool:
    """Returns whether someone outside Terraform grants billing access."""
    billing = ctx.answers.billing
    return billing.no_iam and billing.external_grant


def _check_billing_grant(ctx: model.Context) -> model.Verdict:
    """Checks that the Stage 1 account holds the billing role."""
    policy = ctx.cloud.billing_account_iam(ctx.answers.billing.account_id)
    member = _resman_member(ctx)
    holders = policy.bindings.get(iam_diff.BindingKey(BILLING_ROLE), ())
    if member in holders:
        return model.Verdict(Status.DONE, f"{member} holds {BILLING_ROLE}.")
    return model.Verdict(
        Status.PENDING,
        f"{member} lacks {BILLING_ROLE} on the billing account.",
        _grant_command(ctx),
    )


def _run_billing_grant(ctx: model.Context) -> None:
    """Grants the billing role with the operator's credentials."""
    ctx.cloud.add_billing_account_binding(
        ctx.answers.billing.account_id, BILLING_ROLE, _resman_member(ctx)
    )


# s1.precreate_tenants


def _precreate_needed(ctx: model.Context) -> bool:
    """Returns whether only pre-created projects get billing here."""
    answers = ctx.answers
    return (
        answers.billing.no_iam
        and not answers.billing.external_grant
        and answers.billing_override is None
        and bool(answers.resman.tenants)
    )


def _linked(ctx: model.Context, project_id: str) -> bool:
    """Returns whether a project is linked to the billing account."""
    link = ctx.cloud.project_billing(project_id)
    return link.enabled and link.account_id == ctx.answers.billing.account_id


def _precreate_card(ctx: model.Context, missing: list[tuple[str, str]]) -> str:
    """Returns the request to pre-create projects and how to import them."""
    lines = [
        "Ask an administrator who can use the billing account to create "
        "these projects and link them to it:",
        *(f"  {project_id}" for _, project_id in missing),
        f"Then record them in the imports.{paths.RESMAN} answer:",
        *(
            "  "
            + answers_lib.set_command(
                ctx.answers.prefix,
                ["imports", paths.RESMAN, address],
                project_id,
            )
            for address, project_id in missing
        ),
    ]
    return "\n".join(lines)


def _check_precreate(ctx: model.Context) -> model.Verdict:
    """Checks that every tenant project is imported and linked."""
    imported = ctx.answers.imports.get(paths.RESMAN, {})
    projects = derive.tenant_project_imports(ctx.answers)
    missing = [item for item in projects if imported.get(item[0]) != item[1]]
    if not missing:
        missing = [item for item in projects if not _linked(ctx, item[1])]
    if missing:
        return model.Verdict(
            Status.PENDING,
            f"{len(missing)} tenant projects are not imported and linked: "
            f"{', '.join(project_id for _, project_id in missing)}.",
            _precreate_card(ctx, missing),
        )
    return model.Verdict(
        Status.DONE,
        f"Stage 1 imports {len(projects)} linked tenant projects.",
    )


# s1.apply


def _unlinked_tenants(ctx: model.Context) -> bool:
    """Returns whether a tenant project is not linked to the account."""
    for _, project_id in derive.tenant_project_imports(ctx.answers):
        try:
            if not _linked(ctx, project_id):
                return True
        except api.CloudError:
            # A project that does not exist yet is not linked.
            return True
    return False


def _apply_identity(ctx: model.Context) -> model.Identity:
    """Needs billing access when Terraform links projects as the deployer.

    With `billing_override`, the `google.billing` provider of Stage 1 runs
    as the credentials themselves, not as the stage service account.
    """
    if ctx.answers.billing_override is not None and _unlinked_tenants(ctx):
        return model.Identity.BILLING_LINKER
    return model.Identity.DEPLOYER


def _explain_apply(ctx: model.Context) -> str:
    """Explains the Stage 1 apply."""
    return (
        "Applies Stage 1, which creates the environment and tenant "
        "folders, the tenant projects and the stage service accounts of "
        "Stages 2 and 3. With billing_override, Terraform links the tenant "
        "projects with your own credentials, so they need billing access "
        "on the account. The deploy reviews the plan before it applies the "
        f"saved plan. Fallback: {common.manual_apply(ctx, STAGE, 's1.tfplan')}."
    )


def _check_apply(ctx: model.Context) -> model.Verdict:
    """Checks that run-state records an apply at the current state."""
    return common.applied_verdict(ctx, APPLY.id, STAGE, exact=True)


def _run_apply(ctx: model.Context) -> None:
    """Plans, reviews and applies Stage 1."""
    apply.apply_pipeline(ctx, APPLY, STAGE)


# s1.verify


def _explain_verify(ctx: model.Context) -> str:
    """Explains the Stage 1 verification."""
    target = probe_lib.backend(ctx.answers.prefix, STAGE)
    return (
        "Checks that Stage 1 wrote the inputs of Stages 2 and 3 under "
        f"fast-config/ and keeps its state in {target.state_uri}. Stages 2 "
        "and 3 follow the DDG until stellar covers them."
    )


def _check_verify(ctx: model.Context) -> model.Verdict:
    """Checks that the inputs of Stages 2 and 3 exist."""
    missing = common.missing_outputs(ctx, workspace_lib.RESMAN_OUTPUTS)
    if missing:
        return model.Verdict(
            Status.PENDING,
            f"fast-config/ lacks {', '.join(missing)}.",
            "Run the Stage 1 apply, which writes them.",
        )
    return model.Verdict(Status.DONE, "The inputs of Stages 2 and 3 exist.")


OUTPUTS = model.Step(
    id="s1.outputs",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Copy the Stage 0 outputs",
    doc_anchor=DDG,
    explain=_explain_outputs,
    check=_check_outputs,
    run=_run_outputs,
)
RENDER = model.Step(
    id="s1.render",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Render the Stage 1 workspace",
    doc_anchor=DDG,
    explain=model.static(
        "Renders the Stage 1 workspace from the answers and links the "
        "Stage 0 outputs into it, replacing the DDG steps that copy "
        "terraform.tfvars.sample and the outputs. Fallback: stellar render "
        "--stage 1."
    ),
    check=lambda ctx: common.render_verdict(ctx, STAGE),
    run=lambda ctx: engine.render(ctx, STAGE),
    requires=(OUTPUTS.id,),
)
BILLING_GRANT = model.Step(
    id="s1.billing_grant",
    stage=STAGE,
    kind=Kind.MANUAL,
    title="Grant the Stage 1 account billing access",
    doc_anchor=DDG,
    explain=_explain_billing_grant,
    check=_check_billing_grant,
    run=_run_billing_grant,
    applies_when=_external_grant,
    when="billing.no_iam and billing.external_grant are both true",
    identity=model.fixed(model.Identity.BILLING_ADMIN),
)
PRECREATE_TENANTS = model.Step(
    id="s1.precreate_tenants",
    stage=STAGE,
    kind=Kind.MANUAL,
    title="Pre-create the tenant projects",
    doc_anchor=DDG,
    explain=model.static(
        "Stage 1 cannot link the tenant projects to the billing account "
        "when Stage 0 manages no billing IAM, so an administrator with "
        "billing access creates and links them, and Stage 1 imports them "
        "through the imports.1-resman answer. Stage 1 itself creates the "
        "tenant folders that parent these projects, so agree on the parent "
        "folder with the administrator before the first Stage 1 apply. "
        "Fallback: set billing_override, or billing.external_grant, and "
        "grant the billing role instead."
    ),
    check=_check_precreate,
    applies_when=_precreate_needed,
    when=(
        "billing.no_iam is true, Stage 1 has tenants, and neither "
        "billing_override nor billing.external_grant links their projects"
    ),
)
APPLY = model.Step(
    id="s1.apply",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Stage 1 apply",
    doc_anchor=DDG,
    explain=_explain_apply,
    check=_check_apply,
    run=_run_apply,
    requires=(RENDER.id,),
    identity=_apply_identity,
    remedies=APPLY_REMEDIES,
)
VERIFY = model.Step(
    id="s1.verify",
    stage=STAGE,
    kind=Kind.CHECK,
    title="Inputs of Stages 2 and 3",
    doc_anchor=DDG,
    explain=_explain_verify,
    check=_check_verify,
)

STEPS = (OUTPUTS, RENDER, BILLING_GRANT, PRECREATE_TENANTS, APPLY, VERIFY)
