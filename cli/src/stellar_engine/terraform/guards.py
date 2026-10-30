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

"""Decides whether a saved plan may be applied.

`evaluate` reads a parsed plan and returns findings. A BLOCK finding
refuses the apply, and no flag overrides it. A CONFIRM finding needs the
operator's explicit answer, which `--yes` never gives. An INFO finding is
shown only. The finding keys match the remedy keys of the deploy steps, so
`stellar status` and `stellar deploy` print one remedy per problem.

The rules come from the plans of real Stage 0 failures: a bootstrap-phase
plan after a final apply deletes the managed organization policies, an
imported log bucket plans a replacement because of provider bug #15725,
and organization automation that reverts organization policies makes
every later plan revert them back.
"""

from collections.abc import Sequence
import dataclasses
import enum
from typing import Protocol

from stellar_engine import iam_diff
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.render import phase as phase_lib
from stellar_engine.terraform import plan as plan_lib


class Level(enum.StrEnum):
    """How a finding affects the apply."""

    BLOCK = "block"
    CONFIRM = "confirm"
    INFO = "info"


# Finding keys.
PLAN_INTEGRITY = "plan_integrity"
NO_CHANGES = "no_changes"
PHASE_BOOTSTRAP_AFTER_FINAL = "phase_bootstrap_after_final"
IMPORT_REPLACE_15725 = "import_replace_15725"
WORKLOAD_INPUT_ONLY = "workload_input_only"
IMPORT_REPLACE = "import_replace"
PROTECTED_DELETE = "protected_delete"
TARGETED_SCOPE = "targeted_scope"
DELETE_CONFIRM = "delete_confirm"
IAM_MEMBER_REMOVAL = "iam_member_removal"
IAM_POLICY_REPLACE = "iam_policy_replace"
ORG_POLICY_DRIFT_REVERT = "org_policy_drift_revert"

ORG_POLICY_TYPE = "google_org_policy_policy"
LOG_BUCKET_TYPE = "google_logging_project_bucket_config"
# Stage 0 types whose loss is permanent or reserves the name: KMS key rings
# are never deleted, log bucket names stay reserved for 7 days, and project
# IDs for about 30 days.
PROTECTED_TYPES = frozenset(
    {
        "google_project",
        repo_lib.WORKLOAD_RESOURCE,
        "google_kms_key_ring",
        "google_kms_crypto_key",
        LOG_BUCKET_TYPE,
        "google_storage_bucket",
        "google_folder",
    }
)
# Authoritative organization IAM: members missing from the configuration
# lose the role. `iam_diff.BINDING_TYPE` is the binding resource.
ORG_IAM_POLICY_TYPE = "google_organization_iam_policy"
# A targeted workload or folder plan also applies the organization logging
# settings that both depend on, which set the default log storage location
# of new projects across the organization.
ORG_LOGGING_SETTINGS = (
    "module.organization-logging."
    "google_logging_organization_settings.default[0]"
)
_LEVEL_ORDER = (Level.BLOCK, Level.CONFIRM, Level.INFO)


@dataclasses.dataclass(frozen=True)
class Finding:
    """One guard result.

    Attributes:
        level: How the finding affects the apply.
        key: The guard key, such as `protected_delete`.
        address: The resource address the finding is about, or None.
        detail: What the plan does and how to fix it.
        remedy_key: The deploy remedy that fixes the finding, or None.
    """

    level: Level
    key: str
    address: str | None
    detail: str
    remedy_key: str | None = None

    def label(self) -> str:
        """Returns `BLOCK <key> <address>`, as run-state records it."""
        address = f" {self.address}" if self.address else ""
        return f"{self.level.upper()} {self.key}{address}"

    def line(self) -> str:
        """Returns the finding as `BLOCK <key> <address>: <detail>`."""
        return f"{self.label()}: {self.detail}"


class History(Protocol):
    """What the guards read from the deployment's run-state."""

    @property
    def final_applied(self) -> bool:
        """Whether a Stage 0 final apply has succeeded."""
        ...

    @property
    def last_tfvars_sha256(self) -> str | None:
        """The hash of the stage's tfvars at its last successful apply."""
        ...

    @property
    def tfvars_sha256(self) -> str | None:
        """The hash of the stage's tfvars that the plan used."""
        ...

    @property
    def last_engine_sha256(self) -> str | None:
        """The hash of the engine and provider versions at the last apply."""
        ...

    @property
    def engine_sha256(self) -> str | None:
        """The hash of the engine and provider versions of the plan.

        None when the engine checkout has uncommitted changes.
        """
        ...


@dataclasses.dataclass(frozen=True)
class HistoryView:
    """A `History` built from plain values.

    Attributes:
        final_applied: Whether a Stage 0 final apply has succeeded.
        last_tfvars_sha256: The tfvars hash at the last successful apply.
        tfvars_sha256: The tfvars hash that the plan used.
        last_engine_sha256: The engine hash at the last successful apply.
        engine_sha256: The engine hash of the plan.
    """

    final_applied: bool = False
    last_tfvars_sha256: str | None = None
    tfvars_sha256: str | None = None
    last_engine_sha256: str | None = None
    engine_sha256: str | None = None


def blocks(findings: Sequence[Finding]) -> list[Finding]:
    """Returns the findings that refuse the apply.

    Args:
        findings: Findings of `evaluate`.
    """
    return [finding for finding in findings if finding.level == Level.BLOCK]


def confirmations(findings: Sequence[Finding]) -> list[Finding]:
    """Returns the findings that need the operator's answer.

    Args:
        findings: Findings of `evaluate`.
    """
    return [finding for finding in findings if finding.level == Level.CONFIRM]


def integrity_finding(error: plan_lib.PlanError) -> Finding:
    """Returns the BLOCK finding for a plan that `plan.parse` refused.

    Args:
        error: The parse error.
    """
    return Finding(
        Level.BLOCK,
        PLAN_INTEGRITY,
        None,
        f"{error}. Upgrade stellar, or apply this plan by hand after "
        "reviewing it.",
    )


def _integrity(plan: plan_lib.Plan, *, targeted: bool) -> list[Finding]:
    """Blocks plans that failed or do not converge.

    `plan.parse` already refused a format it cannot read. Terraform marks
    every plan made with `-target` incomplete, because its apply leaves the
    rest of the configuration unconverged, so only an untargeted incomplete
    plan is refused.
    """
    problems = []
    if plan.errored:
        problems.append(
            "Planning failed part way, so the plan is incomplete. Fix the "
            "errors in the plan log and plan again."
        )
    if not plan.complete and not targeted:
        problems.append(
            "The plan defers changes that need another plan after this "
            "apply. Apply it by hand, or plan again once the deferred "
            "values are known."
        )
    return [
        Finding(Level.BLOCK, PLAN_INTEGRITY, None, problem)
        for problem in problems
    ]


def _phase(
    plan: plan_lib.Plan, history: History | None, explained: set[str]
) -> list[Finding]:
    """Blocks a bootstrap-phase plan once the final phase was reached.

    The plan's own `bootstrap_user` value shows the phase, whatever the
    files say. In the bootstrap phase Stage 0 drops its organization
    policies, so a plan that deletes them comes from the wrong phase.
    """
    if plan.variable(phase_lib.VARIABLE) is None:
        return []
    deletes = [
        change
        for change in plan.changes
        if change.managed and change.type == ORG_POLICY_TYPE and change.deletes
    ]
    final = history is not None and history.final_applied
    if not deletes and not final:
        return []
    explained.update(change.address for change in deletes)
    reasons = []
    if final:
        reasons.append("run-state records a final apply")
    if deletes:
        reasons.append(f"it deletes {len(deletes)} organization policies")
    return [
        Finding(
            Level.BLOCK,
            PHASE_BOOTSTRAP_AFTER_FINAL,
            deletes[0].address if deletes else None,
            f"The plan runs Stage 0 in the bootstrap phase, because "
            f"{phase_lib.VARIABLE} is set, but {' and '.join(reasons)}. "
            "Run `stellar init --set stage0_phase=final`, then deploy "
            "again, which renders the final phase.",
        )
    ]


def _bucket_project_bug(change: plan_lib.Change) -> bool:
    """Returns whether a bucket replace is provider bug #15725.

    An imported bucket stores `project` as `projects/<id>`, while the
    configuration says `<id>`, and the provider replaces the bucket.
    """
    if ("project",) not in change.replace_paths:
        return False
    before = change.before if isinstance(change.before, dict) else {}
    after = change.after if isinstance(change.after, dict) else {}
    project = after.get("project")
    return isinstance(project, str) and (
        before.get("project") == f"projects/{project}"
    )


def _workload_fields(change: plan_lib.Change, repo: repo_lib.Repo) -> list[str]:
    fields = [
        str(path[0])
        for path in change.replace_paths
        if path and path[0] in repo_lib.WORKLOAD_INPUT_ONLY
    ]
    if fields:
        return fields
    try:
        return list(repo.assured_workload().replaced_on_import)
    except repo_lib.RepoError:
        return list(repo_lib.WORKLOAD_INPUT_ONLY)


def _import_replace(change: plan_lib.Change, repo: repo_lib.Repo) -> Finding:
    if change.type == LOG_BUCKET_TYPE and _bucket_project_bug(change):
        return Finding(
            Level.BLOCK,
            IMPORT_REPLACE_15725,
            change.address,
            "The imported log bucket would be destroyed and created again, "
            "because the provider stores its project as projects/<id> "
            "after an import, as terraform-provider-google issue 15725 "
            "describes. Bucket names stay reserved for 7 days after a "
            "delete. Let stellar fix the project attribute in the state, "
            "then plan again.",
            remedy_key=IMPORT_REPLACE_15725,
        )
    if change.type == repo_lib.WORKLOAD_RESOURCE:
        fields = ", ".join(_workload_fields(change, repo))
        return Finding(
            Level.BLOCK,
            WORKLOAD_INPUT_ONLY,
            change.address,
            "The import of the pre-created Assured Workloads workload "
            f"plans a replacement, because organization.tf sets {fields} "
            "without listing it in lifecycle.ignore_changes, and the "
            "Assured Workloads API never returns it. Use an engine "
            "checkout whose workload ignores these arguments.",
        )
    return Finding(
        Level.BLOCK,
        IMPORT_REPLACE,
        change.address,
        "The import would destroy the existing object and create it "
        f"again ({_describe(change)}). Fix the configuration or the import "
        "ID so the import adopts the object as it is.",
    )


def _import_replaces(
    plan: plan_lib.Plan, repo: repo_lib.Repo, explained: set[str]
) -> list[Finding]:
    found = []
    for change in plan.changes:
        if change.managed and change.importing and change.deletes:
            explained.add(change.address)
            found.append(_import_replace(change, repo))
    return found


def _protected(plan: plan_lib.Plan, explained: set[str]) -> list[Finding]:
    found = []
    for change in plan.changes:
        if (
            change.managed
            and change.deletes
            and change.type in PROTECTED_TYPES
            and change.address not in explained
        ):
            explained.add(change.address)
            found.append(
                Finding(
                    Level.BLOCK,
                    PROTECTED_DELETE,
                    change.address,
                    f"Stage 0 would {change.action} a {change.type} "
                    f"({_describe(change)}); its loss is permanent or "
                    "reserves the name. Find out why with the plan text "
                    "before you change the configuration or the state.",
                )
            )
    return found


def _targets(targeted_to: str | Sequence[str] | None) -> tuple[str, ...]:
    if targeted_to is None:
        return ()
    if isinstance(targeted_to, str):
        return (targeted_to,)
    return tuple(targeted_to)


def _targeted_scope(
    plan: plan_lib.Plan, targets: tuple[str, ...]
) -> list[Finding]:
    """Checks that a targeted plan changes only the target.

    No-op entries and data source reads change nothing, so they never
    count, whatever their address.
    """
    found = []
    for change in plan.changes:
        if not change.changes_something:
            continue
        if change.address in targets or change.module_address in targets:
            continue
        if change.address == ORG_LOGGING_SETTINGS:
            found.append(
                Finding(
                    Level.INFO,
                    TARGETED_SCOPE,
                    change.address,
                    "The targeted apply also sets the organization logging "
                    "settings, the default log storage location of new "
                    "projects across the organization.",
                )
            )
            continue
        found.append(
            Finding(
                Level.BLOCK,
                TARGETED_SCOPE,
                change.address,
                f"The plan targets {', '.join(targets)} but would "
                f"{change.action} this resource too.",
            )
        )
    return found


def _iam_detail(change: plan_lib.Change) -> str | None:
    """Describes how an authoritative IAM change can remove members."""
    if change.type == ORG_IAM_POLICY_TYPE:
        return (
            "The plan replaces the whole organization IAM policy; every "
            "grant missing from it is removed."
        )
    role = (change.after or change.before or {}).get("role", "the role")
    if change.deletes:
        return f"The plan deletes the binding, so every member loses {role}."
    if change.action == "create":
        return (
            f"The plan creates the authoritative binding of {role}; members "
            "that hold it today outside the configuration lose it."
        )
    if "members" in change.unknown_attributes:
        return f"The members of {role} are known only after apply."
    before = set((change.before or {}).get("members") or ())
    after = set((change.after or {}).get("members") or ())
    removed = sorted(before - after)
    if not removed:
        return None
    return f"The plan removes {', '.join(removed)} from {role}."


def _iam_removals(plan: plan_lib.Plan) -> list[Finding]:
    """Flags authoritative organization IAM changes.

    A binding change gets `IAM_MEMBER_REMOVAL`, which the organization IAM
    review shows against the live policy, which the state's `before`
    values may not match. A whole-policy resource gets
    `IAM_POLICY_REPLACE`, which the review does not model, so the deploy
    asks about it like any other finding.
    """
    found = []
    for change in plan.changes:
        if not change.changes_something or change.type not in (
            iam_diff.BINDING_TYPE,
            ORG_IAM_POLICY_TYPE,
        ):
            continue
        detail = _iam_detail(change)
        if detail:
            found.append(_iam_finding(change, detail))
    return found


def _iam_finding(change: plan_lib.Change, detail: str) -> Finding:
    if change.type == ORG_IAM_POLICY_TYPE:
        return Finding(
            Level.CONFIRM,
            IAM_POLICY_REPLACE,
            change.address,
            f"{detail} The organization IAM review covers bindings and "
            "audit configurations only, so compare the saved plan with "
            "the live policy by hand before you apply it.",
        )
    return Finding(
        Level.CONFIRM,
        IAM_MEMBER_REMOVAL,
        change.address,
        f"{detail} The organization IAM review shows the grants this "
        "apply removes from the live policy.",
    )


def _same_inputs(history: History | None) -> bool:
    """Returns whether the plan read the inputs and code of the last apply.

    A new engine commit, uncommitted changes or new provider versions can
    change a policy as much as new inputs, so each must match too.
    """
    if history is None:
        return False
    pairs = (
        (history.tfvars_sha256, history.last_tfvars_sha256),
        (history.engine_sha256, history.last_engine_sha256),
    )
    return all(current and current == last for current, last in pairs)


def _policy_updates(plan: plan_lib.Plan) -> list[plan_lib.Change]:
    """Returns the in-place updates of managed organization policies."""
    return [
        change
        for change in plan.changes
        if change.managed
        and change.type == ORG_POLICY_TYPE
        and change.actions == ("update",)
        and not change.importing
    ]


def _revert_reason(
    change: plan_lib.Change, drifted: set[str], unchanged: bool
) -> str | None:
    """Says why an update reverts an outside change, or returns None."""
    if change.address in drifted:
        return "The policy changed outside Terraform"
    if unchanged:
        return (
            "The stage inputs, the engine commit and the provider versions "
            "are unchanged since the last apply, so the policy changed "
            "outside Terraform"
        )
    return None


def _drift_reverts(
    plan: plan_lib.Plan, history: History | None
) -> list[Finding]:
    """Flags organization policy updates that revert outside changes.

    A policy that changed outside Terraform shows up in `resource_drift`
    with more than an etag difference. When the inputs, the engine commit
    and the provider versions are unchanged since the last apply, any plan
    of only policy updates reverts outside changes too.
    """
    updates = _policy_updates(plan)
    drifted = {
        change.address
        for change in plan.drift
        if change.type == ORG_POLICY_TYPE and change.material()
    }
    updated = {change.address for change in updates}
    only_updates = all(
        change.address in updated
        for change in plan.changes
        if change.changes_something
    )
    unchanged = only_updates and _same_inputs(history)
    found = []
    for change in updates:
        reason = _revert_reason(change, drifted, unchanged)
        if reason is not None:
            found.append(
                Finding(
                    Level.CONFIRM,
                    ORG_POLICY_DRIFT_REVERT,
                    change.address,
                    f"{reason}. Applying reverts it, and automation that "
                    "enforces the outside value, such as a managed test "
                    "organization, reverts it again. Answer no unless the "
                    "outside change was a mistake.",
                )
            )
    return found


def _describe(change: plan_lib.Change) -> str:
    parts = [f"actions {', '.join(change.actions)}"]
    if change.action_reason:
        parts.append(change.action_reason)
    forced = change.forced_paths
    if forced:
        parts.append(f"forced by {', '.join(forced)}")
    unknown = [name for name in forced if name in change.unknown_attributes]
    if unknown:
        parts.append(f"{', '.join(unknown)} known only after apply")
    return "; ".join(parts)


def _deletes(plan: plan_lib.Plan, explained: set[str]) -> list[Finding]:
    found = []
    for change in plan.changes:
        if (
            change.managed
            and change.destructive
            and change.address not in explained
        ):
            verb = (
                "removes from the state without destroying"
                if change.action == "forget"
                else f"would {change.action}"
            )
            found.append(
                Finding(
                    Level.CONFIRM,
                    DELETE_CONFIRM,
                    change.address,
                    f"The plan {verb} this resource ({_describe(change)}).",
                )
            )
    return found


def evaluate(
    plan: plan_lib.Plan,
    *,
    stage: str,
    run_state: History | None,
    repo: repo_lib.Repo,
    targeted_to: str | Sequence[str] | None = None,
) -> list[Finding]:
    """Returns the findings of every guard for a saved plan.

    A plan that failed, or an untargeted plan that is incomplete, only
    gets `plan_integrity` BLOCK findings. A plan that changes nothing only
    gets the `no_changes` INFO finding, and the step counts as done.

    Args:
        plan: The parsed plan.
        stage: The stage name or alias, such as `0` or `1-resman`.
        run_state: What run-state records, or None without run-state.
        repo: The engine checkout the plan was made from.
        targeted_to: The `-target` addresses of a targeted plan.

    Returns:
        The findings, BLOCK first, then CONFIRM, then INFO.

    Raises:
        ValueError: If the stage is unknown.
    """
    bootstrap = paths.resolve_stage(stage) == paths.BOOTSTRAP
    targets = _targets(targeted_to)
    integrity = _integrity(plan, targeted=bool(targets))
    if integrity:
        return integrity
    if not plan.applyable:
        return [
            Finding(
                Level.INFO,
                NO_CHANGES,
                None,
                "The plan changes nothing, so there is nothing to apply.",
            )
        ]
    explained: set[str] = set()
    findings = []
    if bootstrap:
        findings += _phase(plan, run_state, explained)
    findings += _import_replaces(plan, repo, explained)
    if bootstrap:
        findings += _protected(plan, explained)
    if targets:
        findings += _targeted_scope(plan, targets)
    findings += _deletes(plan, explained)
    findings += _iam_removals(plan)
    findings += _drift_reverts(plan, run_state)
    return sorted(
        findings, key=lambda finding: _LEVEL_ORDER.index(finding.level)
    )
