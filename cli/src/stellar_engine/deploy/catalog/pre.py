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

"""The prerequisite steps of the deploy, from the DDG Prerequisites section.

They enable the bootstrap project APIs, grant the deployer the organization
roles, record the existing organization policies, run preflight and ask for
the confirmations that no API can check. The IAM grant, preflight and the
manual confirmations apply only before the first Stage 0 apply: afterwards
Stage 0 manages the organization roles authoritatively, so a grant outside
Terraform would only be removed again.
"""

from collections.abc import Callable
import dataclasses

from stellar_engine import org_policies
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import model
from stellar_engine.deploy import remedies
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.deploy.catalog import common
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.preflight import result
from stellar_engine.render import imports as imports_lib

Status = model.StepStatus
Kind = model.StepKind
STAGE = model.PRE_STAGE
# When the steps that `common.first_apply_pending` gates apply.
_BEFORE_STAGE0 = "no Stage 0 apply has created resources yet"
# IAM takes seconds to minutes to show a new grant to testIamPermissions,
# so `pre.iam_roles` checks again on this schedule before it gives up.
GRANT_WAIT_SECONDS = 120
GRANT_POLL_SECONDS = 15


# pre.apis


def _project(ctx: model.Context) -> str:
    """Returns the bootstrap project."""
    return ctx.answers.bootstrap_project


def _explain_apis(ctx: model.Context) -> str:
    """Explains the API step with its gcloud fallback."""
    project = _project(ctx)
    services = checks.required_services(ctx.repo)
    return (
        f"Enables the APIs that Stage 0 needs in the bootstrap project "
        f"{project}, as the DDG Google Cloud Setup section does with "
        "fast/stages-aw/0-bootstrap/enableServices.sh, plus the Cloud "
        "Monitoring API that the DDG adds. Fallback: "
        f"{checks.enable_command(project, services)}."
    )


def _check_apis(ctx: model.Context) -> model.Verdict:
    """Checks that the bootstrap project has every required API."""
    project = _project(ctx)
    missing = cloud_ops.missing_services(ctx, project)
    if not missing:
        return model.Verdict(
            Status.DONE, f"{project} has every required API enabled."
        )
    return model.Verdict(
        Status.PENDING,
        f"{project} lacks {', '.join(missing)}.",
        remedy=checks.enable_command(project, missing),
    )


def _run_apis(ctx: model.Context) -> None:
    """Enables the missing APIs, or hands them to a project owner."""
    project = _project(ctx)
    try:
        cloud_ops.enable_services(ctx, project)
    except api.AccessDeniedError as error:
        missing = cloud_ops.missing_services(ctx, project)
        raise model.BlockedError(
            f"Cannot enable the APIs of {project}: {error}",
            remedy=(
                "Ask a project owner to run "
                f"{checks.enable_command(project, missing)}, or "
                "fast/stages-aw/0-bootstrap/enableServices.sh."
            ),
        ) from error


# pre.iam_roles


def _explain_iam_roles(ctx: model.Context) -> str:
    """Explains the organization role grant with its fallback."""
    org = ctx.answers.organization.id
    return (
        "Grants the deploying identity the organization roles of "
        "fast/stages-aw/0-bootstrap/setIAM.yaml.sample on organization "
        f"{org}, as the DDG Google Cloud Setup section does with setIAM.sh. "
        "The step grants only the roles that preflight finds missing and "
        "that the identity lacks directly, leaves Billing Account "
        "Administrator to the billing account, saves an IAM snapshot "
        "before it writes, and asks first. Fallback: "
        f"fast/stages-aw/0-bootstrap/setIAM.sh <email> {org}, or one gcloud "
        "organizations add-iam-policy-binding command per role."
    )


def _rows_verdict(
    rows: list[result.CheckResult], passed: str, doc: str
) -> model.Verdict:
    """Turns preflight rows into a verdict: any failure is pending.

    A pending verdict keeps every row in `results`, so a caller can tell
    which checks failed.
    """
    failed = [row for row in rows if row.status == result.Status.FAIL]
    if failed:
        return model.Verdict(
            Status.PENDING,
            f"Preflight fails {', '.join(row.check_id for row in failed)}.",
            remedy="\n".join(
                f"{row.check_id}: {row.remedy or row.detail}" for row in failed
            ),
            doc=failed[0].doc or doc,
            results=tuple(rows),
        )
    if not rows or all(row.status == result.Status.SKIP for row in rows):
        return model.Verdict(
            Status.UNKNOWN,
            "Preflight skipped these checks.",
            doc=doc,
            results=tuple(rows),
        )
    return model.Verdict(Status.DONE, passed, doc=doc, results=tuple(rows))


def _check_iam_roles(ctx: model.Context) -> model.Verdict:
    """Checks the organization roles through the preflight IAM rows."""
    return _rows_verdict(
        ctx.preflight().rows("iam."),
        "The deploying identity holds every role of setIAM.yaml.sample.",
        checks.DOC_IAM,
    )


def _failed_checks(verdict: model.Verdict) -> list[str]:
    """Returns the IDs of the preflight rows that a verdict fails."""
    return [
        row.check_id
        for row in verdict.results
        if row.status == result.Status.FAIL
    ]


def _run_iam_roles(ctx: model.Context) -> None:
    """Grants the missing organization roles and waits for IAM to apply them.

    A deployer that already holds every failing role directly gets no
    grant, which happens on a rerun soon after an earlier grant or under
    an IAM deny policy, so the step says that it only waits.

    Raises:
        model.StoppedError: If preflight still finds a role that this run
            granted missing after `GRANT_WAIT_SECONDS`.
        model.BlockedError: If preflight still finds a role missing that
            the deployer held directly before the run.
    """
    granted = cloud_ops.grant_roles(ctx)
    wait = f"Waiting up to {GRANT_WAIT_SECONDS} seconds for IAM to apply them."
    if granted:
        ctx.say(f"Granted {', '.join(granted)}. {wait}")
    elif _failed_checks(_check_iam_roles(ctx)):
        ctx.say(f"The deployer holds the failing roles directly. {wait}")
    verdict = _wait_for_roles(ctx)
    if verdict.status != Status.PENDING:
        return
    if granted:
        raise model.StoppedError(
            "IAM has not applied the grants yet.",
            remedy="Rerun stellar deploy in a few minutes.",
        )
    raise model.BlockedError(
        f"Preflight still fails {', '.join(_failed_checks(verdict))}, "
        "although the deployer holds each of these roles directly and this "
        "run granted none.",
        remedy=(
            "An earlier grant may still be propagating, so rerun stellar "
            "deploy in a few minutes. If the check keeps failing, look for "
            "an IAM deny policy that withholds a permission of these roles, "
            "which no grant fixes."
        ),
    )


def _wait_for_roles(ctx: model.Context) -> model.Verdict:
    """Checks the roles again until they pass or the wait is over.

    Returns:
        The last verdict of the role check.
    """
    waited = 0
    while True:
        ctx.invalidate()
        verdict = _check_iam_roles(ctx)
        if verdict.status != Status.PENDING or waited >= GRANT_WAIT_SECONDS:
            return verdict
        ctx.sleep(GRANT_POLL_SECONDS)
        waited += GRANT_POLL_SECONDS


# pre.org_policies


def _unrecorded(ctx: model.Context, kept: tuple[str, ...]) -> list[str]:
    """Returns the kept policies that neither the answers nor state hold.

    Raises:
        api.CloudError: If the remote state cannot be read, which the
            engine reports as UNKNOWN instead of recording every policy.
    """
    state = ctx.stage0().readable_state()
    managed = state.addresses if state else frozenset()
    listed = set(ctx.answers.existing_org_policies)
    return [
        name
        for name in kept
        if name not in listed
        and f'{imports_lib.ORG_POLICY_ADDRESS}["{name}"]' not in managed
    ]


def _check_org_policies(ctx: model.Context) -> model.Verdict:
    """Checks that the answers or the state hold each existing policy."""
    scanned = org_policies.scan(ctx.answers, ctx.repo, ctx.cloud)
    missing = _unrecorded(ctx, scanned.kept)
    if not missing:
        return model.Verdict(
            Status.DONE,
            f"existing_org_policies or the Stage 0 state holds each of the "
            f"{len(scanned.kept)} existing policies that Stage 0 declares.",
        )
    return model.Verdict(
        Status.PENDING,
        f"existing_org_policies lacks {', '.join(missing)}.",
        remedy="stellar imports scan",
        doc=checks.DDG_STAGE0,
    )


def _run_org_policies(ctx: model.Context) -> None:
    """Records the existing policies in `existing_org_policies`."""
    scanned = org_policies.scan(ctx.answers, ctx.repo, ctx.cloud)
    ctx.update_answers(
        org_policies.keep_scanned(scanned),
        source="stellar deploy pre.org_policies",
    )
    ctx.say(
        f"Recorded {len(scanned.kept)} existing organization policies in "
        "existing_org_policies."
    )


# pre.preflight


def _check_preflight(ctx: model.Context) -> model.Verdict:
    """Turns the preflight results into a verdict."""
    return _rows_verdict(
        list(ctx.preflight().results),
        "No preflight check fails.",
        checks.DDG_PREREQUISITES,
    )


# pre.super_admin, pre.access_transparency, pre.project_quota


@dataclasses.dataclass(frozen=True)
class _Manual:
    """A manual confirmation, from `checks.check_manual`."""

    step_id: str
    check_id: str
    title: str


_MANUAL = (
    _Manual("pre.super_admin", "manual.super_admin", "Confirm Super Admin"),
    _Manual(
        "pre.access_transparency",
        "manual.access_transparency",
        "Confirm Access Transparency",
    ),
    _Manual("pre.project_quota", "manual.quota", "Confirm the project quota"),
)


def _manual_row(check_id: str) -> result.CheckResult:
    """Returns the preflight row of a manual confirmation."""
    # The manual checks read nothing from the context.
    rows = checks.check_manual(None)
    return next(row for row in rows if row.check_id == check_id)


def _check_manual(
    step_id: str, check_id: str
) -> Callable[[model.Context], model.Verdict]:
    """Returns the check of a manual confirmation step."""

    def check(ctx: model.Context) -> model.Verdict:
        """Returns DONE once a person confirmed the step."""
        if ctx.run_state.confirmed(step_id, run_state_lib.MANUAL):
            return model.Verdict(Status.DONE, "A person confirmed it.")
        row = _manual_row(check_id)
        return model.Verdict(Status.UNKNOWN, row.detail, doc=row.doc)

    return check


def _manual_step(item: _Manual) -> model.Step:
    """Returns the step of a manual confirmation."""
    return model.Step(
        id=item.step_id,
        stage=STAGE,
        kind=Kind.MANUAL,
        title=item.title,
        doc_anchor=_manual_row(item.check_id).doc or checks.DDG_PREREQUISITES,
        explain=model.static(
            f"{_manual_row(item.check_id).detail} No API shows this to the "
            "deployer, so the deploy records your confirmation."
        ),
        check=_check_manual(item.step_id, item.check_id),
        applies_when=common.first_apply_pending,
        when=_BEFORE_STAGE0,
    )


APIS = model.Step(
    id="pre.apis",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Enable the bootstrap project APIs",
    doc_anchor=checks.DOC_APIS,
    explain=_explain_apis,
    check=_check_apis,
    run=_run_apis,
    remedies=(remedies.API_DISABLED,),
)
IAM_ROLES = model.Step(
    id="pre.iam_roles",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Grant the deployer the organization roles",
    doc_anchor=checks.DOC_IAM,
    explain=_explain_iam_roles,
    check=_check_iam_roles,
    run=_run_iam_roles,
    applies_when=common.first_apply_pending,
    when=_BEFORE_STAGE0,
)
ORG_POLICIES = model.Step(
    id="pre.org_policies",
    stage=STAGE,
    kind=Kind.AUTO,
    title="Record the existing organization policies",
    doc_anchor=checks.DDG_STAGE0,
    explain=model.static(
        "Records the existing organization policies that Stage 0 declares "
        "in the existing_org_policies answer, so the final Stage 0 apply "
        "imports them instead of failing to create them. It replaces "
        "fast/stages-aw/0-bootstrap/import.sh and only reads Google Cloud. "
        "Fallback: stellar imports scan."
    ),
    check=_check_org_policies,
    run=_run_org_policies,
)
PREFLIGHT = model.Step(
    id="pre.preflight",
    stage=STAGE,
    kind=Kind.CHECK,
    title="Preflight checks",
    doc_anchor=checks.DDG_PREREQUISITES,
    explain=model.static(
        "Runs every stellar preflight check against the answers and stops "
        "at a failed check. Warnings and manual confirmations pass, so "
        "review them in the preflight report. Fallback: stellar preflight "
        "prints the same checks as a table."
    ),
    check=_check_preflight,
    applies_when=common.first_apply_pending,
    when=_BEFORE_STAGE0,
)

STEPS = (
    APIS,
    IAM_ROLES,
    ORG_POLICIES,
    PREFLIGHT,
    *(_manual_step(item) for item in _MANUAL),
)
