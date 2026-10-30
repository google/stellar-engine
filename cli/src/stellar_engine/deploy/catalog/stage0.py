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

"""The Stage 0 steps of the deploy, in the order of the DDG Stage 0 section.

Stage 0 renders its workspace, applies the Assured Workloads workload on
its own, applies the rest in the bootstrap phase, swaps in the remote
providers file, moves the state into the bootstrap bucket, switches to the
final phase and applies again. Each check reads the probe of
`deploy.probe`, run-state and Google Cloud, so a rerun skips every step
that is done.
"""

import pathlib

from stellar_engine import fsutil
from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import derive
from stellar_engine.config import models
from stellar_engine.config import validate
from stellar_engine.deploy import apply
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import remedies
from stellar_engine.deploy.catalog import common
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.render import phase as phase_lib
from stellar_engine.render import pipeline
from stellar_engine.terraform import runner as runner_lib
from stellar_engine.wizard import prompts

Status = model.StepStatus
Kind = model.StepKind
STAGE = "0"
DDG = checks.DDG_STAGE0
_PROVIDERS = workspace_lib.BOOTSTRAP_PROVIDERS
# The remedies that any Stage 0 apply may meet, most specific first.
APPLY_REMEDIES = (
    remedies.STATE_LOCK,
    remedies.BACKEND_INIT_REQUIRED,
    remedies.BQ_RESTRICT_SERVICE_USAGE,
    remedies.SA_PROPAGATION,
    remedies.KMS_SERVICE_AGENT,
    remedies.API_DISABLED,
    remedies.LOG_BUCKET_TIMEOUT,
    remedies.IMPORT_REPLACE_15725,
    remedies.CMEK_FOLDER_SETTINGS,
    remedies.CUSTOM_ROLE_EXISTS,
    remedies.SINK_EXISTS,
    remedies.PROJECT_ID_TAKEN,
    remedies.BILLING_UNLINKED,
    remedies.ADC_QUOTA_PROJECT,
)


def _workload_created(ctx: model.Context) -> bool:
    """Returns whether Stage 0 creates an Assured Workloads workload."""
    return ctx.repo.assured_workload().created(ctx.answers.compliance.regime)


def _bootstrap_imports(ctx: model.Context) -> dict[str, str]:
    """Returns the Stage 0 import IDs of the answers by address."""
    return ctx.answers.imports.get(paths.BOOTSTRAP, {})


# s0.render


def _check_render(ctx: model.Context) -> model.Verdict:
    """Checks the workspace; a phase file stellar did not write blocks."""
    if ctx.stage0().foreign_phase_file:
        target = ctx.workspace(STAGE) / phase_lib.FILENAME
        return model.Verdict(
            Status.BLOCKED,
            f"stellar did not write {target}.",
            "Move the file away or delete it, then rerun stellar deploy.",
        )
    return common.render_verdict(ctx, STAGE)


# s0.ready


def _render_warnings(ctx: model.Context) -> list[str]:
    """Returns the Stage 0 render warnings, without the phase warning.

    The phase warning only fires once the remote providers file is in the
    workspace, which the deploy itself causes before s0.phase_final.
    """
    return pipeline.warnings(
        [STAGE], ctx.answers, ctx.repo, ctx.env, phase=False
    )


def _workload_verdict(ctx: model.Context) -> model.Verdict:
    """Checks that Stage 0 can create the workload or imports it.

    Raises:
        api.CloudError: If the remote state cannot be read, which the
            engine reports as UNKNOWN instead of asking for a workload.
    """
    workload = ctx.repo.assured_workload()
    if not workload.created(ctx.answers.compliance.regime):
        return model.Verdict(Status.DONE, "Stage 0 creates no workload.")
    state = ctx.stage0().readable_state()
    if state is not None and workload.address in state.addresses:
        return model.Verdict(
            Status.DONE, "The Stage 0 state holds the workload."
        )
    import_id = _bootstrap_imports(ctx).get(workload.address)
    if import_id:
        return _imported_verdict(workload, import_id)
    return _billing_verdict(ctx)


def _imported_verdict(
    workload: repo_lib.AssuredWorkload, import_id: str
) -> model.Verdict:
    """Checks that the import adopts the workload without a replacement."""
    if workload.replaced_on_import:
        return model.Verdict(
            Status.BLOCKED,
            f"The import of {import_id} would replace the workload, "
            "because the Stage 0 code leaves "
            f"{', '.join(workload.replaced_on_import)} out of "
            "lifecycle.ignore_changes.",
            "Update the engine checkout to a release that ignores them.",
        )
    return model.Verdict(Status.DONE, f"Stage 0 imports {import_id}.")


def _billing_verdict(ctx: model.Context) -> model.Verdict:
    """Checks that the deployer may create the workload with billing."""
    access = ctx.preflight().billing_access
    if access:
        return model.Verdict(
            Status.DONE, "The deployer can create the workload with billing."
        )
    if access is None:
        return model.Verdict(
            Status.UNKNOWN,
            "Preflight could not test the billing access that creating the "
            "workload needs; see the billing checks of stellar preflight.",
        )
    return model.Verdict(
        Status.PENDING,
        "The deployer cannot use the billing account, so an administrator "
        "pre-creates the workload.",
        workload_card(ctx),
    )


def _check_ready(ctx: model.Context) -> model.Verdict:
    """Checks the warnings, the environment, the phase and the workload."""
    blocked = [*ctx.terraform.child_env.problems, *_render_warnings(ctx)]
    if blocked:
        return model.Verdict(
            Status.BLOCKED,
            " ".join(blocked),
            "Fix the answers or the environment, then rerun stellar deploy.",
        )
    if _final_before_first_apply(ctx):
        return model.Verdict(
            Status.BLOCKED,
            "stage0_phase is final, but the first Stage 0 apply has not "
            "run; it needs the bootstrap phase.",
            _phase_bootstrap_remedy(ctx),
        )
    return _workload_verdict(ctx)


def _final_before_first_apply(ctx: model.Context) -> bool:
    """Returns whether `stage0_phase: final` precedes the first apply.

    The first apply writes the remote providers file and the migration
    moves the state; without either, no apply ran in the bootstrap phase,
    and the catalog has no step that runs one in the final phase. The
    bootstrap bucket must also hold no state that can be read, so a
    workspace that lost the providers file of earlier applies never
    hears that it should return to the bootstrap phase.
    """
    probe = ctx.stage0()
    return (
        ctx.answers.stage0_phase == models.STAGE0_FINAL
        and not probe.outputs_providers
        and not probe.migrated
        and probe.remote.readable
        and probe.remote.empty
    )


def _phase_bootstrap_remedy(ctx: model.Context) -> str:
    """Returns how to return to the bootstrap phase before the first apply.

    `stellar init` allows the change until a final apply succeeded.
    """
    command = answers_lib.set_command(
        ctx.answers.prefix, ["stage0_phase"], models.STAGE0_BOOTSTRAP
    )
    return f"{command}, then rerun stellar deploy --stage 0"


def _location(ctx: model.Context) -> str:
    """Returns the Assured Workloads location of the regime."""
    return derive.compliance_location(ctx.answers)


def _set_workload(ctx: model.Context, name: str) -> str:
    """Returns the `stellar init` line that records a workload name."""
    address = ctx.repo.assured_workload().address
    return answers_lib.set_command(
        ctx.answers.prefix, ["imports", paths.BOOTSTRAP, address], name
    )


def workload_card(ctx: model.Context) -> str:
    """Returns the request to an administrator who pre-creates the workload.

    The fields mirror `google_assured_workloads_workload.primary` in
    `0-bootstrap/organization.tf`.

    Args:
        ctx: The deploy context.
    """
    answers = ctx.answers
    folder = naming.workload_folder_name(answers.prefix)
    return "\n".join(
        [
            "Ask an administrator who can use the billing account to create "
            "the Assured Workloads workload:",
            f"  organization: {answers.organization.id}",
            f"  location: {_location(ctx)}",
            f"  complianceRegime: {answers.compliance.regime}",
            f"  displayName: {folder}",
            f"  billingAccount: billingAccounts/{answers.billing.account_id}",
            f"  resourceSettings: CONSUMER_FOLDER named {folder}",
            "  violationNotificationsEnabled: true",
            "  labels: goog-terraform-provisioned=true",
            "Then record the workload name that the API returns:",
            f"  {_set_workload(ctx, validate.workload_name_pattern(answers))}",
        ]
    )


def _workload_problem(ctx: model.Context) -> prompts.Validator:
    """Returns a validator for a workload name; empty text stops.

    The name passes the check of `validate.workload_name_problem`, which
    the answers model runs again when the name is recorded.
    """

    def problem(text: str) -> str | None:
        name = text.strip()
        if not name:
            return None
        found = validate.workload_name_problem(name, ctx.answers)
        if found is None:
            return None
        return f"{found}. Enter that name, or nothing to stop."

    return problem


def _record_workload(ctx: model.Context, name: str) -> None:
    """Records a pre-created workload in `imports.0-bootstrap`."""
    address = ctx.repo.assured_workload().address

    def adopt(data):
        imports = data.setdefault("imports", {})
        imports.setdefault(paths.BOOTSTRAP, {})[address] = name

    ctx.update_answers(adopt, source="stellar deploy s0.ready")


def _run_ready(ctx: model.Context) -> None:
    """Records the pre-created workload, then renders its import block."""
    card = workload_card(ctx)
    if not ctx.interactive:
        raise model.InputRequiredError(
            "s0.ready needs the name of the pre-created workload.",
            remedy=card,
        )
    ctx.say(card)
    name = ctx.text(
        "Workload name, or nothing to stop:", _workload_problem(ctx)
    ).strip()
    if not name:
        raise model.StoppedError(
            "s0.ready waits for the pre-created workload.", remedy=card
        )
    _record_workload(ctx, name)
    engine.render(ctx, STAGE)


# s0.apply_workload


def _workload_target(ctx: model.Context) -> str:
    """Returns the address the targeted apply creates."""
    if _workload_created(ctx):
        return ctx.repo.assured_workload().address
    return ctx.repo.no_compliance_folder_address()


def _explain_apply_workload(ctx: model.Context) -> str:
    """Explains the targeted apply of the workload or its stand-in folder."""
    target = _workload_target(ctx)
    fallback = common.manual_apply(ctx, STAGE, "workload.tfplan", (target,))
    return (
        f"Applies only {target} first, so the Assured Workloads folder "
        "exists before the rest of Stage 0 needs it. The plan uses -target, "
        "and the apply applies the saved plan. It needs s0.ready, which "
        "checks that the deployer can create the workload with billing. "
        f"Fallback: {fallback}."
    )


def _check_apply_workload(ctx: model.Context) -> model.Verdict:
    """Checks that the Stage 0 state holds the target."""
    target = _workload_target(ctx)
    state = ctx.stage0().readable_state()
    addresses = state.addresses if state else frozenset()
    if any(
        address == target or address.startswith(f"{target}.")
        for address in addresses
    ):
        return model.Verdict(Status.DONE, f"The Stage 0 state holds {target}.")
    return model.Verdict(Status.PENDING, f"The Stage 0 state lacks {target}.")


def _run_apply_workload(ctx: model.Context) -> None:
    """Plans, reviews and applies the target alone."""
    apply.apply_pipeline(
        ctx, APPLY_WORKLOAD, STAGE, targets=(_workload_target(ctx),)
    )


# s0.allow_bq


def _check_allow_bq(ctx: model.Context) -> model.Verdict:
    """Checks that the workload folder allows the BigQuery services."""
    if cloud_ops.bq_enabled_in_state(ctx):
        return model.Verdict(
            Status.DONE,
            "The Stage 0 state already enables the BigQuery services, so "
            "the folder policy no longer blocks Stage 0.",
        )
    found = cloud_ops.allow_bq_check(ctx)
    if found.done:
        return model.Verdict(
            Status.DONE, f"{found.folder} allows the BigQuery services."
        )
    if found.folder is None:
        return model.Verdict(
            Status.PENDING,
            "Cannot find the workload folder.",
            cloud_ops.workload_bq_card(ctx),
        )
    return model.Verdict(
        Status.PENDING,
        f"The gcp.restrictServiceUsage policy of {found.folder} blocks "
        f"{', '.join(found.missing)}.",
        cloud_ops.workload_bq_card(ctx),
    )


def _explain_allow_bq(ctx: model.Context) -> str:
    """Explains the BigQuery allow list change with its console fallback."""
    return (
        "Allows the BigQuery services on the workload folder, whose "
        "gcp.restrictServiceUsage policy blocks them, as the DDG Stage 0 "
        "note on the 403 error describes. The step calls the Assured "
        "Workloads restrictAllowedResources method, which allows every "
        "service the regime supports that the folder blocks, so the step "
        "lists them before it asks. By hand:\n"
        f"{cloud_ops.workload_bq_card(ctx)}"
    )


def _run_allow_bq(ctx: model.Context) -> None:
    """Allows the BigQuery services, or stops when that takes long."""
    if not cloud_ops.allow_bq_run(ctx):
        raise model.StoppedError(
            "Assured Workloads has not applied the change within "
            f"{cloud_ops.ALLOW_BQ_WAIT_SECONDS} seconds.",
            remedy="Wait a few minutes, then rerun stellar deploy.",
        )


# s0.apply_bootstrap


def _bootstrap_phase(ctx: model.Context) -> bool:
    """Returns whether Stage 0 still runs in the bootstrap phase."""
    return (
        ctx.answers.stage0_phase == models.STAGE0_BOOTSTRAP
        and not ctx.stage0().migrated
    )


def _explain_apply_bootstrap(ctx: model.Context) -> str:
    """Explains the first Stage 0 apply."""
    return (
        "Runs the first Stage 0 apply in the bootstrap phase, which grants "
        "the bootstrap user and skips the organization policies. The phase "
        "file sets bootstrap_user, so no command passes the -var option of "
        "the DDG terraform apply step. The deploy reviews the organization "
        "IAM changes against a live snapshot before it applies the saved "
        f"plan. Fallback: {common.manual_apply(ctx, STAGE, 's0.tfplan')}."
    )


def _check_apply_bootstrap(ctx: model.Context) -> model.Verdict:
    """Checks that run-state records a bootstrap apply."""
    return common.applied_verdict(ctx, APPLY_BOOTSTRAP.id, STAGE, exact=False)


def _run_apply_bootstrap(ctx: model.Context) -> None:
    """Plans, reviews and applies Stage 0 in the bootstrap phase."""
    apply.apply_pipeline(ctx, APPLY_BOOTSTRAP, STAGE)


# s0.remote_providers


def _providers(ctx: model.Context) -> tuple[pathlib.Path, pathlib.Path]:
    """Returns the remote providers file and the workspace providers file."""
    return (
        workspace_lib.remote_bootstrap_providers(ctx.env),
        ctx.workspace(STAGE) / _PROVIDERS,
    )


def _check_remote_providers(ctx: model.Context) -> model.Verdict:
    """Checks that the workspace uses the remote providers file."""
    probe = ctx.stage0()
    if probe.providers_match:
        return model.Verdict(
            Status.DONE, "The workspace uses the remote providers file."
        )
    source, _ = _providers(ctx)
    if not probe.outputs_providers:
        if ctx.answers.stage0_phase == models.STAGE0_FINAL:
            remedy = _phase_bootstrap_remedy(ctx)
        else:
            remedy = (
                "The first Stage 0 apply writes it; run "
                f"{ctx.deploy_command(APPLY_BOOTSTRAP.id)}."
            )
        return model.Verdict(
            Status.PENDING, f"{source} does not exist yet.", remedy
        )
    return model.Verdict(
        Status.PENDING, "The workspace providers file is not the remote one."
    )


def _run_remote_providers(ctx: model.Context) -> None:
    """Backs up the workspace providers file and copies the remote one."""
    source, target = _providers(ctx)
    data = fsutil.read_bytes_or_none(source)
    if data is None:
        raise model.BlockedError(
            f"{source} does not exist yet.",
            remedy="Run the first Stage 0 apply, which writes it.",
        )
    current = fsutil.read_bytes_or_none(target)
    if current is not None:
        backup = runner_lib.providers_backup_path(
            ctx.env.plans, target.name, now=ctx.now()
        )
        fsutil.write_private(backup, current)
        ctx.say(f"Saved the local providers file to {backup}.")
    # A real file, never a link: the file belongs to the environment.
    fsutil.write_private(target, data)
    ctx.say(f"Copied {source} to {target}.")


# s0.quota_project


def _quota_project(ctx: model.Context) -> str:
    """Returns the project the user credentials should bill quota to."""
    return naming.automation_project_id(ctx.answers.prefix)


def _user_credentials(ctx: model.Context) -> bool:
    """Returns whether Application Default Credentials belong to a user."""
    return ctx.cloud.adc_info().kind == api.PrincipalKind.USER


def _explain_quota_project(ctx: model.Context) -> str:
    """Explains the quota project check."""
    project = _quota_project(ctx)
    return (
        f"Checks that your user credentials bill API quota to {project}, "
        "as the DDG Additional Notes advise, because the remote backend "
        "and the providers need a quota project. Fallback: "
        f"{cloud_ops.quota_command(project)}."
    )


def _check_quota_project(ctx: model.Context) -> model.Verdict:
    """Checks the quota project of the credentials."""
    project = _quota_project(ctx)
    found = ctx.cloud.adc_info().quota_project
    if found == project:
        return model.Verdict(Status.DONE, f"The quota project is {project}.")
    return model.Verdict(
        Status.PENDING,
        f"The quota project is {found or 'unset'}, not {project}.",
        cloud_ops.quota_command(project),
    )


# s0.migrate_state


def _explain_migrate(ctx: model.Context) -> str:
    """Explains the state migration into the bootstrap bucket."""
    target = probe_lib.backend(ctx.answers.prefix, STAGE)
    migrate = runner_lib.manual(
        ctx.workspace(STAGE), ("init",), ("-migrate-state",)
    )
    return (
        f"Moves the Stage 0 state into {target.state_uri}, as the DDG "
        "terraform init --migrate-state step does. The deploy backs up the "
        "local state under plans/ first, copies it only when the bucket "
        "holds no newer state of the same lineage, and refuses otherwise. "
        f"Fallback: {migrate}."
    )


def _check_migrate(ctx: model.Context) -> model.Verdict:
    """Checks that the Stage 0 state lives in the bootstrap bucket."""
    probe = ctx.stage0()
    migrated = probe.migrated
    where = probe.backend.state_uri
    if migrated:
        return model.Verdict(Status.DONE, f"The state lives in {where}.")
    if migrated is None:
        return model.Verdict(
            Status.UNKNOWN, f"Cannot read {where}: {probe.remote.error}"
        )
    if not probe.providers_remote:
        return model.Verdict(
            Status.PENDING,
            "The workspace providers file declares no remote backend yet.",
            f"Run {ctx.deploy_command(REMOTE_PROVIDERS.id)}.",
        )
    decision = probe_lib.migrate_decision(probe)
    if decision.action == probe_lib.MigrateAction.REFUSE:
        return model.Verdict(
            Status.BLOCKED,
            decision.reason,
            probe_lib.refusal_remedy(probe, decision),
        )
    return model.Verdict(Status.PENDING, decision.reason)


def _run_migrate(ctx: model.Context) -> None:
    """Initializes the workspace as the migration decision says."""
    apply.init_workspace(ctx, MIGRATE_STATE, STAGE)


# s0.phase_final


def _check_phase_final(ctx: model.Context) -> model.Verdict:
    """Checks the answer and that the phase file is gone."""
    if ctx.answers.stage0_phase != models.STAGE0_FINAL:
        return model.Verdict(
            Status.PENDING, f"stage0_phase is {ctx.answers.stage0_phase}."
        )
    if ctx.stage0().phase_file:
        return model.Verdict(
            Status.PENDING,
            "stage0_phase is final, but the phase file is still in the "
            "workspace.",
        )
    return model.Verdict(Status.DONE, "stage0_phase is final.")


def _run_phase_final(ctx: model.Context) -> None:
    """Sets `stage0_phase` to final and renders again."""

    def final(data):
        data["stage0_phase"] = models.STAGE0_FINAL

    ctx.update_answers(final, source="stellar deploy s0.phase_final")
    engine.render(ctx, STAGE)


# s0.apply_final


def _explain_apply_final(ctx: model.Context) -> str:
    """Explains the final Stage 0 apply."""
    return (
        "Runs the final Stage 0 apply without bootstrap_user, which "
        "manages the organization policies and imports the existing ones, "
        "replacing the DDG import.sh and terraform apply steps. The deploy "
        "reviews the organization IAM changes against a live snapshot "
        "before it applies the saved plan, and the bootstrap bucket keeps "
        "the earlier state versions. Fallback: "
        f"{common.manual_apply(ctx, STAGE, 's0.tfplan')}."
    )


def _check_apply_final(ctx: model.Context) -> model.Verdict:
    """Checks that run-state records a final apply at this state."""
    return common.applied_verdict(ctx, APPLY_FINAL.id, STAGE, exact=True)


def _run_apply_final(ctx: model.Context) -> None:
    """Plans, reviews and applies Stage 0 in the final phase."""
    probe = ctx.stage0()
    if probe.uses_remote and probe.remote.generation is not None:
        ctx.say(
            f"The remote state is at generation {probe.remote.generation}; "
            "the bucket keeps it as a noncurrent version after the apply."
        )
    apply.apply_pipeline(ctx, APPLY_FINAL, STAGE)


# s0.verify


def _explain_verify(ctx: model.Context) -> str:
    """Explains the Stage 0 verification."""
    target = probe_lib.backend(ctx.answers.prefix, STAGE)
    return (
        "Checks that Stage 0 wrote the Stage 1 inputs under fast-config/ "
        f"and that {target.state_uri} is readable."
    )


def _check_verify(ctx: model.Context) -> model.Verdict:
    """Checks the Stage 1 inputs and the remote Stage 0 state."""
    missing = common.missing_outputs(
        ctx, workspace_lib.OUTPUT_LINKS[paths.RESMAN]
    )
    probe = ctx.stage0()
    where = probe.backend.state_uri
    probe.remote.readable_summary(probe.backend)
    if missing:
        return model.Verdict(
            Status.PENDING,
            f"fast-config/ lacks {', '.join(missing)}.",
            "Run the final Stage 0 apply, which writes them.",
        )
    if not probe.remote.exists:
        return model.Verdict(Status.PENDING, f"{where} does not exist.")
    return model.Verdict(
        Status.DONE, f"The Stage 1 inputs exist, and {where} is readable."
    )


RENDER = model.Step(
    id="s0.render",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Render the Stage 0 workspace",
    doc_anchor=DDG,
    explain=model.static(
        "Renders the Stage 0 workspace from the answers: "
        "terraform.tfvars, the import blocks and the phase file. "
        "It replaces the DDG steps that copy terraform.tfvars.sample and "
        "providers.tf.tmp. Fallback: stellar render --stage 0."
    ),
    check=_check_render,
    run=lambda ctx: engine.render(ctx, STAGE),
)
READY = model.Step(
    id="s0.ready",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Check that Stage 0 can apply",
    doc_anchor=DDG,
    explain=model.static(
        "Checks that Stage 0 can apply: the render reports no warnings, "
        "the Terraform environment has no problems, and Stage 0 can create "
        "or import the Assured Workloads workload. A deployer without "
        "billing access needs an administrator to pre-create the workload, "
        "and the step records the workload name in the imports.0-bootstrap "
        "answer. Fallback: stellar render --stage 0 prints the same "
        "warnings, and the CLI README describes the pre-creation."
    ),
    check=_check_ready,
    run=_run_ready,
    requires=(RENDER.id,),
)
APPLY_WORKLOAD = model.Step(
    id="s0.apply_workload",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Targeted Assured Workloads apply",
    doc_anchor=DDG,
    explain=_explain_apply_workload,
    check=_check_apply_workload,
    run=_run_apply_workload,
    requires=(READY.id,),
    remedies=(
        remedies.STATE_LOCK,
        remedies.API_DISABLED,
        remedies.WORKLOAD_CREATE_FAILED,
        remedies.ADC_QUOTA_PROJECT,
    ),
)
ALLOW_BQ = model.Step(
    id="s0.allow_bq",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Allow BigQuery on the workload folder",
    doc_anchor=DDG,
    explain=_explain_allow_bq,
    check=_check_allow_bq,
    run=_run_allow_bq,
    applies_when=_workload_created,
    when="the regime creates an Assured Workloads workload",
    remedies=(remedies.BQ_RESTRICT_SERVICE_USAGE,),
)
APPLY_BOOTSTRAP = model.Step(
    id="s0.apply_bootstrap",
    stage=STAGE,
    kind=Kind.AUTO,
    title="First Stage 0 apply in the bootstrap phase",
    doc_anchor=DDG,
    explain=_explain_apply_bootstrap,
    check=_check_apply_bootstrap,
    run=_run_apply_bootstrap,
    applies_when=_bootstrap_phase,
    when=(
        "stage0_phase is bootstrap and the state has not moved to the "
        "bootstrap bucket"
    ),
    remedies=APPLY_REMEDIES,
)
REMOTE_PROVIDERS = model.Step(
    id="s0.remote_providers",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Use the remote providers file",
    doc_anchor=DDG,
    explain=model.static(
        "Copies the remote providers file that the first apply wrote over "
        "the workspace providers file, after a backup under plans/, as the "
        "DDG gcloud storage cp step does. The remote file declares the "
        "bootstrap bucket as the backend. Fallback: copy fast-config/"
        f"{workspace_lib.REMOTE_BOOTSTRAP_PROVIDERS} of the environment over "
        f"{_PROVIDERS} in the Stage 0 workspace."
    ),
    check=_check_remote_providers,
    run=_run_remote_providers,
)
QUOTA_PROJECT = model.Step(
    id="s0.quota_project",
    stage=STAGE,
    kind=Kind.CHECK,
    title="Quota project of the user credentials",
    doc_anchor="docs/ddg.md#additional-notes",
    explain=_explain_quota_project,
    check=_check_quota_project,
    applies_when=_user_credentials,
    when="Application Default Credentials belong to a user",
)
MIGRATE_STATE = model.Step(
    id="s0.migrate_state",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Move the Stage 0 state to the bootstrap bucket",
    doc_anchor=DDG,
    explain=_explain_migrate,
    check=_check_migrate,
    run=_run_migrate,
    requires=(REMOTE_PROVIDERS.id,),
    remedies=(
        remedies.STATE_LOCK,
        remedies.MIGRATE_REFUSED,
        remedies.BACKEND_INIT_REQUIRED,
    ),
)
PHASE_FINAL = model.Step(
    id="s0.phase_final",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Switch Stage 0 to the final phase",
    doc_anchor=DDG,
    explain=model.static(
        "Sets the stage0_phase answer to final and renders again, which "
        "removes the phase file, so the next apply manages the "
        "organization policies. Fallback: stellar init --set "
        "stage0_phase=final, then stellar render --stage 0."
    ),
    check=_check_phase_final,
    run=_run_phase_final,
    requires=(MIGRATE_STATE.id,),
)
APPLY_FINAL = model.Step(
    id="s0.apply_final",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Final Stage 0 apply",
    doc_anchor=DDG,
    explain=_explain_apply_final,
    check=_check_apply_final,
    run=_run_apply_final,
    requires=(PHASE_FINAL.id,),
    remedies=APPLY_REMEDIES,
)
VERIFY = model.Step(
    id="s0.verify",
    stage=STAGE,
    kind=Kind.CHECK,
    title="Stage 0 outputs and remote state",
    doc_anchor=DDG,
    explain=_explain_verify,
    check=_check_verify,
)

STEPS = (
    RENDER,
    READY,
    APPLY_WORKLOAD,
    ALLOW_BQ,
    APPLY_BOOTSTRAP,
    REMOTE_PROVIDERS,
    QUOTA_PROJECT,
    MIGRATE_STATE,
    PHASE_FINAL,
    APPLY_FINAL,
    VERIFY,
)
