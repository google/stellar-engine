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

"""Reviews a saved plan with the operator before it is applied.

Stage 0 manages organization roles authoritatively, so an apply removes
every grant it does not declare. `confirm_apply` saves a snapshot of the
live organization IAM policy, shows the grants the plan removes against
it, and the owners it replaces on imported projects, and asks the operator
to keep the grants, confirm or skip the review with the organization ID
typed, or abort. A plan that manages no organization IAM but replaces
owners asks about them alone. It then asks once per CONFIRM finding of the
plan guards and asks to apply. The policy etag is read again right before
the apply, and a changed policy repeats the review; a policy that changes
three times stops the deploy. `--yes` answers only the apply question.
"""

import functools
import pathlib

from stellar_engine import iam_diff
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import api
from stellar_engine.preflight import report
from stellar_engine.terraform import guards
from stellar_engine.terraform import plan as plan_lib
from stellar_engine.terraform import runner as runner_lib

# The finding the IAM review raises when a plan hides the members.
IAM_UNKNOWN = "iam_unknown"
_STAGE0 = "0"
_KEEP = "keep the removed grants in the answers and plan again"
_CONFIRM = "confirm"
_SKIP = "skip the review"
_ABORT = "abort"
# Stage 0 projects bind their owners authoritatively, which drops the owners
# of a project someone else created.
_PROJECT_BINDING_TYPE = "google_project_iam_binding"
_OWNER_ROLE = "roles/owner"
# A policy that someone keeps editing stops the deploy after this many
# etag changes, because each one repeats the review and its snapshot.
_MAX_ETAG_ROUNDS = 3


class ReplanError(Exception):
    """The review changed the answers, so the stage plans again."""


def confirm_apply(
    ctx: model.Context,
    step: model.Step,
    stage: str,
    plan: plan_lib.Plan,
    files: runner_lib.PlanFiles,
    findings: list[guards.Finding],
) -> None:
    """Reviews organization IAM and the findings, then asks to apply.

    The review runs whenever the plan manages organization IAM, and it
    comes first, so its snapshot exists even when the operator declines a
    finding. Owners that the plan replaces on imported projects need an
    answer whether or not the plan manages organization IAM. The policy
    etag is read again right before the apply; when it changed, the review
    repeats against the new policy, up to `_MAX_ETAG_ROUNDS` changes.

    Args:
        ctx: The deploy context.
        step: The step that applies.
        stage: Catalog stage `0` or `1`.
        plan: The parsed plan.
        files: The saved plan files.
        findings: The plan guard findings, none of them BLOCK.

    Raises:
        ReplanError: If the operator kept removed grants in the answers.
        model.DeployError: If the operator declines, aborts or may not be
            asked, the plan hides the organization IAM members, or the
            live policy keeps changing during the review.
    """
    target = _iam_target(plan)
    owners = _owner_bindings(ctx, plan)
    reviewed = iam_diff.manages_iam(plan)

    def review() -> str | None:
        """Runs the IAM review when the plan manages organization IAM."""
        if not reviewed:
            return None
        return _review(ctx, step, stage, target, files, owners)

    etag = review()
    if not reviewed:
        _confirm_owners(ctx, step, files, owners)
    _confirm_findings(ctx, step, findings, reviewed=reviewed)
    changes = 0
    while True:
        if not ctx.confirm(f"Apply {files.tfplan.name}?", routine=True):
            raise model.StoppedError(
                "The operator did not apply the plan.",
                remedy=f"The saved plan is {files.tfplan}.",
            )
        if etag is None or _live_policy(ctx).etag == etag:
            return
        changes += 1
        if changes == _MAX_ETAG_ROUNDS:
            raise model.StoppedError(
                "The organization IAM policy keeps changing during the review.",
                remedy=(
                    "Find out who changes it, then rerun stellar deploy. "
                    f"The snapshots in {ctx.env.iam_snapshots} hold each "
                    "policy the review saw."
                ),
            )
        ctx.say(
            "The organization IAM policy changed during the review; "
            "reviewing it again."
        )
        etag = review()


def _confirm_findings(
    ctx: model.Context,
    step: model.Step,
    findings: list[guards.Finding],
    *,
    reviewed: bool,
) -> None:
    """Asks once per CONFIRM key; `--yes` never answers these.

    A member removal finding is skipped only when the organization IAM
    review showed the removed grants against the live policy.
    """
    grouped: dict[str, list[guards.Finding]] = {}
    for finding in guards.confirmations(findings):
        if reviewed and finding.key == guards.IAM_MEMBER_REMOVAL:
            continue
        grouped.setdefault(finding.key, []).append(finding)
    for key, found in grouped.items():
        question = f"The plan has {len(found)} {key} findings. Apply anyway?"
        if not ctx.confirm(question):
            raise model.StoppedError(
                f"The operator declined {len(found)} {key} findings.",
                remedy=found[0].detail,
            )
        addresses = ", ".join(finding.address or "" for finding in found)
        ctx.confirmed(step.id, key, addresses)
    ctx.save()


def _iam_target(plan: plan_lib.Plan) -> iam_diff.Target:
    """Returns what the plan sets on organization IAM, or fails the step."""
    try:
        return iam_diff.target_from_plan(plan)
    except iam_diff.UnknownMembersError as error:
        raise model.FailedError(
            f"{IAM_UNKNOWN}: the plan sets organization IAM members that "
            f"are known only after apply, at {error.address}, so the "
            "review cannot list the grants the apply removes.",
            remedy=(
                "Review the organization IAM policy by hand against the "
                "saved plan, then apply it with Terraform."
            ),
        ) from error
    except ValueError as error:
        raise model.FailedError(
            f"{IAM_UNKNOWN}: cannot read the organization IAM changes of "
            f"the plan: {error}"
        ) from error


def _live_policy(ctx: model.Context) -> iam_diff.Policy:
    """Reads the live organization policy, or blocks when it is denied."""
    org_id = ctx.answers.organization.id
    try:
        return ctx.cloud.get_org_iam_policy(org_id)
    except api.AccessDeniedError as error:
        raise model.BlockedError(
            f"Cannot read the IAM policy of organization {org_id} for the "
            f"review: {error}",
            remedy=(
                "Grant the deployer roles/resourcemanager."
                "organizationAdmin, which the prerequisites list."
            ),
        ) from error


def _review(
    ctx: model.Context,
    step: model.Step,
    stage: str,
    target: iam_diff.Target,
    files: runner_lib.PlanFiles,
    owners: list[tuple[str, str]],
) -> str:
    """Runs the organization IAM review and returns the reviewed etag.

    A snapshot of the live policy comes first. A plan that removes nothing
    and replaces no owner of an imported project passes without a
    question. Otherwise the operator keeps the removed grants, confirms,
    skips the review or aborts; confirming and skipping both need the
    organization ID typed.
    """
    live = _live_policy(ctx)
    snapshot = cloud_ops.snapshot(ctx, live, "gate", plan=files.tfplan)
    diff = iam_diff.diff(live, target)
    if not diff.needs_review and not owners:
        return live.etag
    _render_review(ctx, diff, snapshot, owners)
    keepable = [grant for grant in diff.removed if grant.key.condition is None]
    choices = [_CONFIRM, _SKIP, _ABORT]
    if keepable and stage == _STAGE0:
        choices.insert(0, _KEEP)
    choice = ctx.select("How do you want to go on?", choices)
    if choice == _KEEP:
        _keep_grants(ctx, step, keepable)
        raise ReplanError
    if choice == _ABORT:
        raise model.StoppedError(
            "The operator stopped at the organization IAM review.",
            remedy=f"The live policy is saved in {snapshot}.",
        )
    _typed_decision(ctx, step, choice, diff, owners, snapshot)
    return live.etag


def _typed_decision(
    ctx: model.Context,
    step: model.Step,
    choice: str,
    diff: iam_diff.Diff,
    owners: list[tuple[str, str]],
    snapshot: pathlib.Path,
) -> None:
    """Asks for the organization ID, then records the review decision.

    Raises:
        model.StoppedError: If the typed organization ID does not match.
    """
    org_id = ctx.answers.organization.id
    question = f"This apply changes the IAM policy of organization {org_id}."
    if not diff.needs_review:
        question = (
            f"This apply replaces the owners of {len(owners)} imported "
            f"projects in organization {org_id}."
        )
    if not ctx.typed_confirm(question, org_id):
        raise model.StoppedError("The typed organization ID did not match.")
    decision = (
        run_state_lib.CONFIRMED if choice == _CONFIRM else run_state_lib.SKIPPED
    )
    detail = (
        f"{len(diff.removed)} removed, {len(diff.audit_overwrites)} audit "
        f"configs, {len(diff.conditional_replacements)} conditional "
        f"bindings, {len(owners)} imported project owners; snapshot "
        f"{snapshot}"
    )
    ctx.confirmed(step.id, run_state_lib.IAM_GATE, detail, decision)
    ctx.save()


def _owner_bindings(
    ctx: model.Context, plan: plan_lib.Plan
) -> list[tuple[str, str]]:
    """Returns the owner bindings the plan sets on imported projects.

    Stage 0 binds owners authoritatively, so the owners of a project that
    someone else created lose the role. The plan cannot show who they
    are, because the binding is new to the state.

    Returns:
        The project ID and the members that keep the role, per binding.
    """
    imported = {
        import_id
        for imports in ctx.answers.imports.values()
        for import_id in imports.values()
    }
    found = []
    for change in plan.changes:
        after = change.after if isinstance(change.after, dict) else {}
        if (
            change.type == _PROJECT_BINDING_TYPE
            and change.changes_something
            and after.get("role") == _OWNER_ROLE
            and after.get("project") in imported
        ):
            members = ", ".join(after.get("members") or ()) or "nobody"
            found.append((after["project"], members))
    return found


def _owner_rows(owners: list[tuple[str, str]]) -> list[tuple[str, str, str]]:
    """Returns the review table rows of the owners the apply replaces."""
    return [
        (
            "owners",
            f"{_OWNER_ROLE} on {project}",
            f"Only {members} keep the role on this imported project.",
        )
        for project, members in owners
    ]


def _confirm_owners(
    ctx: model.Context,
    step: model.Step,
    files: runner_lib.PlanFiles,
    owners: list[tuple[str, str]],
) -> None:
    """Asks before a plan without organization IAM replaces owners.

    `--yes` never answers it, as for a plan finding.

    Raises:
        model.StoppedError: If the operator declines.
    """
    if not owners:
        return
    table = report.iam_table("Imported project owners", _owner_rows(owners))
    ctx.console.print(table)
    question = (
        f"The apply replaces the owners of {len(owners)} imported projects. "
        "Apply anyway?"
    )
    if not ctx.confirm(question):
        raise model.StoppedError(
            "The operator declined the owner change.",
            remedy=f"The saved plan is {files.tfplan}.",
        )
    projects = ", ".join(project for project, _ in owners)
    ctx.confirmed(step.id, run_state_lib.OWNERS, projects)
    ctx.save()


def _render_review(
    ctx: model.Context,
    diff: iam_diff.Diff,
    snapshot: pathlib.Path,
    owners: list[tuple[str, str]],
) -> None:
    """Prints the grants the apply removes and the owners it replaces."""
    rows = iam_diff.rows(diff) + _owner_rows(owners)
    ctx.console.print(report.iam_table("Organization IAM review", rows))
    ctx.say(
        f"The apply keeps {len(diff.kept_foreign)} and adds "
        f"{len(diff.added)} grants. The live policy is saved in {snapshot}."
    )


def _keep_grants(
    ctx: model.Context, step: model.Step, grants: list[iam_diff.Grant]
) -> None:
    """Adds removed grants to `overrides.0-bootstrap.iam` and re-renders."""
    ctx.update_answers(
        functools.partial(iam_diff.keep_in_overrides, grants=grants),
        source="the organization IAM review",
    )
    engine.render(ctx, _STAGE0)
    ctx.confirmed(
        step.id,
        run_state_lib.IAM_GATE,
        f"kept {len(grants)} grants in overrides.0-bootstrap.iam",
        run_state_lib.KEPT,
    )
    ctx.save()
