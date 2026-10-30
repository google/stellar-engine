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

"""Google Cloud changes that deploy steps make outside Terraform.

Each function replaces one helper script of the manual flow and keeps the
script as the documented fallback: `grant_roles` replaces
`0-bootstrap/setIAM.sh`, `enable_services` replaces
`0-bootstrap/enableServices.sh`, and `allow_bq_run` replaces
`scripts/allow_bq.sh`. Each reads before it writes, so a rerun that finds
nothing to do changes nothing.
"""

from collections.abc import Sequence
import dataclasses
import pathlib
import re

from stellar_engine import iam_diff
from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.preflight import result

# The BigQuery services that Stage 0 enables in projects under the Assured
# Workloads folder: `automation.tf` and `log-export.tf`.
BQ_SERVICES = (
    "bigquery.googleapis.com",
    "bigqueryreservation.googleapis.com",
    "bigquerystorage.googleapis.com",
)
# `billing.tf` also enables this one when Stage 0 creates the billing export
# project.
BQ_TRANSFER_SERVICE = "bigquerydatatransfer.googleapis.com"
# Assured Workloads applies an allow list change within about 2 minutes.
ALLOW_BQ_WAIT_SECONDS = 120
# The address of a `google_project_service` instance ends with its service,
# such as `module.x.google_project_service.project_services["a.com"]`.
_SERVICE_ADDRESS_RE = re.compile(
    r'(?:^|\.)google_project_service\.[\w-]+\["([^"]+)"\]$'
)
ALLOW_BQ_POLL_SECONDS = 15
# How often `grant_roles` reads the policy again after a concurrent change.
_CONFLICT_ATTEMPTS = 3
_MEMBER_TYPES = {
    api.PrincipalKind.USER: naming.USER,
    api.PrincipalKind.SERVICE_ACCOUNT: naming.SERVICE_ACCOUNT,
}


def snapshot(
    ctx: model.Context,
    policy: iam_diff.Policy,
    reason: str,
    *,
    plan: pathlib.Path | None = None,
) -> pathlib.Path:
    """Saves the organization IAM policy before a change and records it.

    Args:
        ctx: The deploy context.
        policy: The live policy.
        reason: Why, such as `gate` or `grant`.
        plan: The saved plan the snapshot reviews, if any.

    Returns:
        The snapshot file.
    """
    taken = ctx.now()
    path = iam_diff.write_snapshot(
        ctx.env,
        policy,
        iam_diff.snapshot_meta(
            ctx.repo,
            org_id=ctx.answers.organization.id,
            reason=reason,
            taken=taken,
            principal=ctx.principal(),
            plan=plan,
        ),
    )
    ctx.run_state.iam.snapshots.append(
        run_state_lib.SnapshotRecord(
            path=ctx.relative(path) or str(path),
            etag=policy.etag,
            taken=taken,
            reason=reason,
        )
    )
    ctx.save()
    return path


def member(principal: api.Principal) -> str | None:
    """Returns the IAM member of a principal, or None when unknown.

    `setIAM.sh` always grants `user:<email>`; a service account deployer
    needs `serviceAccount:<email>`.

    Args:
        principal: The identity behind the credentials.
    """
    kind = _MEMBER_TYPES.get(principal.kind)
    if kind is None or not principal.email:
        return None
    return naming.principal(kind, principal.email)


def missing_roles(
    policy: iam_diff.Policy, roles: list[str], grantee: str
) -> list[str]:
    """Returns the roles a member lacks in a policy.

    Args:
        policy: The organization policy.
        roles: The roles the member needs.
        grantee: The member, such as `user:admin@example.com`.
    """
    return [
        role
        for role in roles
        if grantee not in policy.bindings.get(iam_diff.BindingKey(role), ())
    ]


def _with_member(
    policy: iam_diff.Policy, roles: list[str], grantee: str
) -> iam_diff.Policy:
    """Returns the policy with a member added to each role."""
    bindings = dict(policy.bindings)
    for role in roles:
        key = iam_diff.BindingKey(role)
        bindings[key] = bindings.get(key, frozenset()) | {grantee}
    return dataclasses.replace(policy, bindings=bindings)


def grant_commands(org_id: str, roles: list[str], grantee: str) -> str:
    """Returns the gcloud commands that grant roles by hand.

    Args:
        org_id: Organization ID.
        roles: The roles.
        grantee: The member.
    """
    return "\n".join(
        f"gcloud organizations add-iam-policy-binding {org_id} "
        f"--member={grantee} --role={role} --condition=None"
        for role in roles
    )


def grant_roles(ctx: model.Context) -> list[str]:
    """Grants the deployer the organization roles that preflight misses.

    Mirrors `0-bootstrap/setIAM.sh` for the roles it can fix: it reads the
    organization policy, adds the deployer to each role, and writes the
    policy with the etag of the read, so a concurrent change is never
    overwritten. Unlike the script, it grants a role only when a preflight
    row of the role fails and the deployer holds no direct binding of it,
    so a role held through a group is never granted again. It also types
    the member from the credentials and snapshots the policy before the
    write.

    Billing Account Administrator is never granted on the organization:
    with `billing.no_iam` Stage 0 needs no billing IAM, and otherwise
    preflight tests the role on the billing account, so the remedy is a
    grant there.

    Args:
        ctx: The deploy context.

    Returns:
        The roles granted; empty when the deployer lacks none of them
        directly.

    Raises:
        model.BlockedError: If preflight could not test the roles, the
            identity is unknown, the deployer lacks Billing Account
            Administrator on the billing account, or may not change the
            organization policy; the remedy lists the gcloud commands.
        model.StoppedError: If the operator declines.
        model.FailedError: If the policy kept changing during the write.
    """
    org_id = ctx.answers.organization.id
    failed = [
        row
        for row in ctx.preflight().rows("iam.")
        if row.status == result.Status.FAIL
    ]
    grantee = member(ctx.cloud.adc_principal())
    shown = grantee or naming.principal(naming.USER, "<deployer email>")
    untested = [row for row in failed if row.check_id == checks.IAM_ROLES_CHECK]
    if untested:
        raise model.BlockedError(
            untested[0].detail,
            remedy=grant_commands(org_id, ctx.repo.required_roles(), shown),
        )
    candidates = [row.check_id.removeprefix("iam.") for row in failed]
    billing = checks.BILLING_ADMIN_ROLE in candidates
    roles = [role for role in candidates if role != checks.BILLING_ADMIN_ROLE]
    granted: list[str] = []
    if roles:
        if grantee is None:
            raise model.BlockedError(
                "Cannot tell whether the credentials belong to a user or a "
                "service account.",
                remedy=grant_commands(org_id, roles, shown),
            )
        granted = _grant(ctx, org_id, roles, grantee)
    if billing and not ctx.answers.billing.no_iam:
        raise _billing_blocked(ctx, shown, granted)
    return granted


def _grant(
    ctx: model.Context, org_id: str, roles: list[str], grantee: str
) -> list[str]:
    """Adds the member to the roles it lacks directly, behind a snapshot.

    Returns:
        The roles granted.
    """
    agreed = False
    for _ in range(_CONFLICT_ATTEMPTS):
        policy = _read_policy(ctx, org_id, roles, grantee)
        missing = missing_roles(policy, roles, grantee)
        if not missing:
            return []
        if not agreed:
            _confirm_grant(ctx, grantee, missing, org_id)
            agreed = True
        snapshot(ctx, policy, "grant")
        try:
            ctx.cloud.set_org_iam_policy(
                org_id,
                _with_member(policy, missing, grantee),
                etag=policy.etag,
                update_mask=("bindings", "etag"),
            )
        except api.ConflictError:
            continue
        except api.AccessDeniedError as error:
            raise _grant_blocked(error, org_id, missing, grantee) from error
        return missing
    raise model.FailedError(
        f"The policy of organization {org_id} changed during each of "
        f"{_CONFLICT_ATTEMPTS} writes.",
        remedy=grant_commands(org_id, roles, grantee),
    )


def _billing_blocked(
    ctx: model.Context, grantee: str, granted: list[str]
) -> model.BlockedError:
    """Returns the stop that hands Billing Account Administrator over."""
    account = ctx.answers.billing.account_id
    done = (
        f" Granted {', '.join(granted)} on the organization." if granted else ""
    )
    return model.BlockedError(
        f"{grantee} lacks {checks.BILLING_ADMIN} on billing account "
        f"{account}.{done}",
        remedy=(
            "Ask a billing account administrator to run gcloud billing "
            f"accounts add-iam-policy-binding {account} --member={grantee} "
            f"--role={checks.BILLING_ADMIN_ROLE}, then rerun stellar deploy."
        ),
    )


def _confirm_grant(
    ctx: model.Context, grantee: str, missing: list[str], org_id: str
) -> None:
    """Asks once to grant the missing roles; `--yes` answers it.

    Raises:
        model.StoppedError: If the operator declines.
    """
    ctx.say(f"{grantee} lacks these roles: {', '.join(missing)}")
    question = f"Grant them on organization {org_id}?"
    if not ctx.confirm(question, routine=True):
        raise model.StoppedError("The operator declined the grant.")


def _read_policy(
    ctx: model.Context, org_id: str, roles: list[str], grantee: str
) -> iam_diff.Policy:
    """Reads the organization policy, or blocks with the manual grants."""
    try:
        return ctx.cloud.get_org_iam_policy(org_id)
    except api.AccessDeniedError as error:
        raise _grant_blocked(error, org_id, roles, grantee) from error


def _grant_blocked(
    error: api.CloudError, org_id: str, roles: list[str], grantee: str
) -> model.BlockedError:
    """Returns the stop that hands the grant to an administrator."""
    email = naming.principal_email(grantee)
    return model.BlockedError(
        f"Cannot change the policy of organization {org_id}: {error}",
        remedy=(
            "Ask an organization administrator to run "
            f"fast/stages-aw/0-bootstrap/setIAM.sh {email} {org_id}, or "
            f"these commands:\n{grant_commands(org_id, roles, grantee)}"
        ),
    )


def missing_services(ctx: model.Context, project: str) -> list[str]:
    """Returns the required services that a project has not enabled.

    The required services are those `checks.required_services` lists for
    the preflight `project.apis` check.

    Args:
        ctx: The deploy context.
        project: The project ID.

    Raises:
        api.CloudError: If the services cannot be listed.
    """
    enabled = ctx.cloud.enabled_services(project)
    required = checks.required_services(ctx.repo)
    return [name for name in required if name not in enabled]


def enable_services(ctx: model.Context, project: str) -> list[str]:
    """Enables the required services that a project lacks.

    Mirrors `0-bootstrap/enableServices.sh` on an explicit project, where
    the script uses the gcloud default project, and adds the DDG
    prerequisites the script lacks.

    Args:
        ctx: The deploy context.
        project: The project ID, usually the bootstrap project.

    Returns:
        The services enabled; empty when none was missing.

    Raises:
        api.CloudError: If the services cannot be listed or enabled.
    """
    missing = missing_services(ctx, project)
    if missing:
        ctx.say(f"Enabling {', '.join(missing)} on {project}.")
        ctx.cloud.enable_services(project, missing)
    return missing


@dataclasses.dataclass(frozen=True)
class BqStatus:
    """Whether projects under the workload folder may use BigQuery.

    Attributes:
        workload: The workload name, or None when unknown.
        folder: The workload folder as `folders/<id>`, or None before the
            workload exists.
        missing: The BigQuery services Stage 0 enables that the folder's
            `gcp.restrictServiceUsage` policy blocks.
    """

    workload: str | None
    folder: str | None
    missing: tuple[str, ...]

    @property
    def done(self) -> bool:
        """Whether the folder exists and allows every service."""
        return self.folder is not None and not self.missing


def bq_services(ctx: model.Context) -> tuple[str, ...]:
    """Returns the BigQuery services Stage 0 enables under the folder."""
    billing = ctx.answers.billing
    created = repo_lib.billing_export_created(
        no_iam=billing.no_iam, is_org_level=billing.is_org_level
    )
    return (*BQ_SERVICES, BQ_TRANSFER_SERVICE) if created else BQ_SERVICES


def bq_enabled_in_state(ctx: model.Context) -> bool:
    """Returns whether the Stage 0 state already enables every service.

    The `gcp.restrictServiceUsage` policy only stops new enablements, so
    once an apply enabled the BigQuery services, as on projects that were
    created before they moved into the folder, the policy no longer blocks
    Stage 0.

    Args:
        ctx: The deploy context.

    Raises:
        api.CloudError: If the remote Stage 0 state cannot be read.
    """
    state = ctx.stage0().state
    addresses = state.addresses if state else frozenset()
    enabled = {
        match.group(1)
        for address in addresses
        if (match := _SERVICE_ADDRESS_RE.search(address))
    }
    return set(bq_services(ctx)) <= enabled


def locate_workload(ctx: model.Context) -> probe_lib.WorkloadRef:
    """Finds the Assured Workloads workload and its folder.

    It reads the Stage 0 state first, then the workload import ID in the
    answers, then the folder by its exact display name. `allow_bq.sh`
    matched a substring of the display name, which a shorter prefix also
    matches.

    Args:
        ctx: The deploy context.

    Returns:
        What was found; both fields are None before the workload exists.

    Raises:
        api.CloudError: If a Google Cloud read fails.
    """
    state = ctx.stage0().state
    found = state.workload if state else None
    if found is not None and found.name and found.folder:
        return found
    imports = ctx.answers.imports.get(paths.BOOTSTRAP, {})
    name = (found.name if found else None) or imports.get(
        ctx.repo.assured_workload().address
    )
    if name:
        workload = ctx.cloud.assured_workload(name)
        if workload is not None and workload.folder:
            return probe_lib.WorkloadRef(name, workload.folder)
    folders = ctx.cloud.find_folders(
        ctx.answers.organization.id,
        naming.workload_folder_name(ctx.answers.prefix),
    )
    folder = folders[0] if len(folders) == 1 else None
    return probe_lib.WorkloadRef(name, folder)


def allow_bq_check(ctx: model.Context) -> BqStatus:
    """Checks the effective `gcp.restrictServiceUsage` on the folder.

    Args:
        ctx: The deploy context.

    Raises:
        api.CloudError: If a Google Cloud read fails.
    """
    ref = locate_workload(ctx)
    if ref.folder is None:
        return BqStatus(ref.name, None, bq_services(ctx))
    restriction = ctx.cloud.effective_service_restriction(ref.folder)
    missing = tuple(
        service
        for service in bq_services(ctx)
        if not restriction.allows(service)
    )
    return BqStatus(ref.name, ref.folder, missing)


def allow_bq_card(folder: str) -> str:
    """Returns the console steps that allow BigQuery by hand.

    They restate the DDG note of the Stage 0 steps; `scripts/allow_bq.sh`
    is the scripted fallback.

    Args:
        folder: The workload folder name, from `naming.workload_folder_name`.
    """
    return "\n".join(
        [
            "Open https://console.cloud.google.com/compliance/assuredworkloads",
            f"Click the {folder} workload, then Review Available Updates.",
            "Under Allowed Services, allow the BigQuery family of services.",
            "Wait about 2 minutes, then rerun stellar deploy.",
            "Fallback: scripts/allow_bq.sh",
        ]
    )


def workload_bq_card(ctx: model.Context) -> str:
    """Returns `allow_bq_card` for the workload folder of this deployment.

    Args:
        ctx: The deploy context.
    """
    return allow_bq_card(naming.workload_folder_name(ctx.answers.prefix))


def _wait_allowed(ctx: model.Context) -> bool:
    """Waits until the folder allows the services, or the time is up."""
    waited = 0
    while True:
        if not allow_bq_check(ctx).missing:
            return True
        if waited >= ALLOW_BQ_WAIT_SECONDS:
            return False
        ctx.sleep(ALLOW_BQ_POLL_SECONDS)
        waited += ALLOW_BQ_POLL_SECONDS


def allow_bq_run(ctx: model.Context) -> bool:
    """Allows the BigQuery services on the workload folder.

    Replaces `scripts/allow_bq.sh`, which overwrote the folder policy
    without an etag. This calls the Assured Workloads
    `restrictAllowedResources` method with `APPEND_COMPLIANT_RESOURCES`,
    which only adds services the regime supports, the API form of the
    console's Allowed Services button. That method allows every compliant
    service the folder blocks, not only BigQuery, so the deploy lists them
    all first, and `--yes` answers the question only when they are all
    BigQuery services. It then waits up to 120 seconds for the effective
    policy to allow them.

    Args:
        ctx: The deploy context.

    Returns:
        Whether the effective policy allows every service in time.

    Raises:
        model.BlockedError: If the workload is unknown, a missing service
            is not compliant for the regime, or the caller may not change
            the workload; the remedy holds the console steps.
        model.StoppedError: If the operator declines.
        api.CloudError: If a read fails.
    """
    status = allow_bq_check(ctx)
    if status.done:
        return True
    if status.workload is None or status.folder is None:
        raise model.BlockedError(
            "Cannot find the Assured Workloads workload to allow BigQuery.",
            remedy=workload_bq_card(ctx),
        )
    added = _check_compliant(ctx, status.workload, status.missing)
    ctx.say(
        f"Assured Workloads allows every compliant service that "
        f"{status.folder} blocks: {', '.join(added)}"
    )
    question = (
        f"Allow these {len(added)} services on {status.folder} through "
        f"{status.workload}?"
    )
    bigquery_only = set(added) <= {*BQ_SERVICES, BQ_TRANSFER_SERVICE}
    if not ctx.confirm(question, routine=bigquery_only):
        raise model.StoppedError("The operator declined to allow BigQuery.")
    try:
        ctx.cloud.restrict_allowed_resources(status.workload)
    except api.AccessDeniedError as error:
        raise model.BlockedError(
            f"Cannot change the workload: {error}", remedy=workload_bq_card(ctx)
        ) from error
    return _wait_allowed(ctx)


def _check_compliant(
    ctx: model.Context, name: str, missing: tuple[str, ...]
) -> tuple[str, ...]:
    """Returns every service the change allows; refuses non-compliant ones.

    Adding a service the regime does not support would raise an Assured
    Workloads violation.

    Returns:
        The workload's compliant services that its folder blocks, which
        `APPEND_COMPLIANT_RESOURCES` allows all at once.
    """
    workload = ctx.cloud.assured_workload(name)
    allowed = workload.compliant_but_disallowed if workload else ()
    blocked = [service for service in missing if service not in allowed]
    if blocked:
        raise model.BlockedError(
            f"{', '.join(blocked)} are not compliant services of {name}, "
            "so allowing them would be a violation.",
            remedy=workload_bq_card(ctx),
        )
    return tuple(allowed)


@dataclasses.dataclass(frozen=True)
class AccountCheck:
    """Whether the stage service accounts are enabled.

    Attributes:
        project: The automation project that holds them.
        disabled: Emails of the disabled stage accounts.
        error: Why the accounts could not be listed, or None.
    """

    project: str
    disabled: tuple[str, ...] = ()
    error: str | None = None

    @property
    def enabled(self) -> bool | None:
        """Whether all are enabled; None when they could not be listed."""
        return None if self.error else not self.disabled

    @property
    def remedy(self) -> str:
        """The gcloud commands that enable the disabled accounts."""
        return enable_accounts_command(self.project, self.disabled)


def enable_accounts_command(project: str, emails: Sequence[str]) -> str:
    """Returns the gcloud commands that enable service accounts by hand.

    Args:
        project: The project that holds the accounts.
        emails: The account emails, or placeholders such as `<email>`.
    """
    return "\n".join(
        f"gcloud iam service-accounts enable {email} --project={project}"
        for email in emails
    )


def quota_command(project: str) -> str:
    """Returns the gcloud command that sets the quota project of the ADC.

    Args:
        project: The project that user credentials bill API quota to.
    """
    return f"gcloud auth application-default set-quota-project {project}"


def service_accounts_enabled(ctx: model.Context) -> AccountCheck:
    """Checks that the Stage 0 automation service accounts are enabled.

    Terraform impersonates them, and `3-security/sa_lockdown.sh` disables
    them after a deployment. Before the first apply the project or the
    accounts do not exist yet, which counts as enabled.

    Args:
        ctx: The deploy context.
    """
    prefix = ctx.answers.prefix
    project = naming.automation_project_id(prefix)
    stage_accounts = {
        naming.automation_sa_email(prefix, name)
        for name in ctx.repo.automation_service_accounts().values()
    }
    try:
        accounts = ctx.cloud.service_accounts(project)
    except api.CLOUD_ERRORS as error:
        return AccountCheck(project, error=str(error))
    disabled = sorted(
        account.email
        for account in accounts
        if account.disabled and account.email in stage_accounts
    )
    return AccountCheck(project, tuple(disabled))
