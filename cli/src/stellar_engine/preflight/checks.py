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

"""Preflight checks for the prerequisites in `docs/ddg.md`.

Each check takes a `Context` and returns a list of `CheckResult`. Checks never
change anything; when a prerequisite is missing they explain how to fix it.
"""

from collections.abc import Mapping
import dataclasses
import re

from packaging import version

from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import tools as tools_lib
from stellar_engine.gcp import api
from stellar_engine.preflight import inputs as inputs_lib
from stellar_engine.preflight import regions
from stellar_engine.preflight import result

Category = result.Category
CheckResult = result.CheckResult
Status = result.Status

DDG_PREREQUISITES = "docs/ddg.md#prerequisites"
DOC_WORKSTATION = "docs/prerequisites.md#local-workstation"
DOC_ORGANIZATION = "docs/prerequisites.md#google-cloud-organization"
DOC_BOOTSTRAP = "docs/prerequisites.md#bootstrap-project"
DOC_APIS = "docs/prerequisites.md#required-apis"
DOC_IAM = "docs/prerequisites.md#initial-iam-grants"
DOC_GROUPS = "docs/prerequisites.md#administrative-groups"
DOC_FEATURES = "docs/prerequisites.md#organization-features-and-quotas"
DOC_TROUBLESHOOTING = "docs/ddg.md#appendices"
DDG_STAGE0 = "docs/ddg.md#stage-0---bootstrap"

# DDG prerequisite that enableServices.sh does not cover yet.
EXTRA_APIS = ("monitoring.googleapis.com",)
BILLING_ADMIN_ROLE = "roles/billing.admin"
# Lets Stage 0 create projects on a billing account whose IAM it does not
# manage, which is what Billing Account User grants.
BILLING_LINK_PERMISSION = "billing.resourceAssociations.create"
BILLING_ADMIN = "Billing Account Administrator (roles/billing.admin)"
BILLING_USER = "Billing Account User (roles/billing.user)"
BILLING_COSTS_MANAGER = (
    "Billing Account Costs Manager (roles/billing.costsManager)"
)
PRECREATE_CHECK = "billing.precreate"
# Points a billing FAIL at the check that lists what to pre-create instead.
_PRECREATE_HINT = (
    f"or pre-create the resources that the {PRECREATE_CHECK} check lists"
)
IMPERSONATION_ENV_VARS = (
    "GOOGLE_IMPERSONATE_SERVICE_ACCOUNT",
    "CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT",
)
_REGION_RE = re.compile(r"^us-[a-z]+[0-9]+$")
_MAX_LISTED = 10


@dataclasses.dataclass
class Context:
    """State shared by the checks of one preflight run.

    Attributes:
        inputs: Values supplied by the operator.
        cloud: Read-only Google Cloud facade.
        tools: Local tool queries.
        repo: Deployment facts parsed from the repository.
        environ: Process environment, for impersonation variables.
        org: Organization resolved by the organization check.
        principal: Identity resolved by the identity check.
        billing_access: Whether the deploying identity holds the billing
            permissions Stage 0 needs, as the billing role check or the
            project billing link check found. None when no check tested
            them or a test failed.
    """

    inputs: inputs_lib.PreflightInputs
    cloud: api.CloudApi
    tools: tools_lib.LocalTools
    repo: repo_lib.Repo
    environ: Mapping[str, str]
    org: api.Organization | None = None
    principal: api.Principal | None = None
    billing_access: bool | None = None

    @property
    def domain(self):
        """Returns the domain from the inputs or the resolved organization."""
        if self.inputs.domain:
            return self.inputs.domain
        return self.org.domain if self.org else None


def _skip(check_id, category, title, needs):
    return CheckResult(
        check_id,
        category,
        title,
        Status.SKIP,
        f"Not checked; pass {needs} to enable this check.",
    )


def _listed(items):
    items = sorted(items)
    shown = ", ".join(items[:_MAX_LISTED])
    if len(items) > _MAX_LISTED:
        shown += f", and {len(items) - _MAX_LISTED} more"
    return shown


def check_tools(ctx):
    """Checks that Terraform and the Google Cloud SDK are installed."""
    results = []
    minimum = ctx.repo.min_terraform_version()
    installed = ctx.tools.terraform_version()
    if installed is None:
        status, detail = Status.FAIL, "Terraform is not installed."
    elif version.Version(installed) < version.Version(minimum):
        status = Status.FAIL
        detail = f"Terraform {installed} is older than {minimum}."
    else:
        status = Status.PASS
        detail = f"Terraform {installed} meets the {minimum} minimum."
    results.append(
        CheckResult(
            "tools.terraform",
            Category.TOOLS,
            "Terraform version",
            status,
            detail,
            remedy=f"Install Terraform {minimum} or newer.",
            doc=DOC_WORKSTATION,
        )
    )
    jq = ctx.tools.jq_version()
    results.append(
        CheckResult(
            "tools.jq",
            Category.TOOLS,
            "jq",
            Status.PASS if jq else Status.WARN,
            f"{jq} is installed."
            if jq
            else "jq is not installed. The setIAM.sh and sa_lockdown.sh "
            "scripts in the manual DDG flow need it.",
            remedy="Install jq.",
            doc=DOC_WORKSTATION,
        )
    )
    gcloud = ctx.tools.gcloud_version()
    results.append(
        CheckResult(
            "tools.gcloud",
            Category.TOOLS,
            "Google Cloud SDK",
            Status.PASS if gcloud else Status.FAIL,
            f"Google Cloud SDK {gcloud} is installed."
            if gcloud
            else "The gcloud command is not installed.",
            remedy="Install the Google Cloud SDK.",
            doc=DOC_WORKSTATION,
        )
    )
    return results


def check_identity(ctx):
    """Checks the gcloud account and Application Default Credentials."""
    results = []
    account = ctx.tools.gcloud_account()
    results.append(
        CheckResult(
            "identity.gcloud",
            Category.IDENTITY,
            "Active gcloud account",
            Status.PASS if account else Status.FAIL,
            f"gcloud is signed in as {account}."
            if account
            else "gcloud has no active account.",
            remedy="Run `gcloud auth login`.",
            doc=DOC_WORKSTATION,
        )
    )
    try:
        ctx.principal = ctx.cloud.adc_principal()
    except api.CredentialsError as error:
        results.append(
            CheckResult(
                "identity.adc",
                Category.IDENTITY,
                "Application Default Credentials",
                Status.FAIL,
                f"Application Default Credentials are not usable: {error}",
                remedy="Run `gcloud auth application-default login`.",
                doc=DOC_WORKSTATION,
            )
        )
        return results
    principal = ctx.principal
    results.append(
        CheckResult(
            "identity.adc",
            Category.IDENTITY,
            "Application Default Credentials",
            Status.PASS if principal.email else Status.WARN,
            f"Terraform will run as {principal.email}."
            if principal.email
            else "The identity behind the credentials cannot be determined.",
            doc=DOC_WORKSTATION,
        )
    )
    if account and principal.email:
        same = account.lower() == principal.email.lower()
        results.append(
            CheckResult(
                "identity.match",
                Category.IDENTITY,
                "gcloud and Terraform use the same identity",
                Status.PASS if same else Status.FAIL,
                "Both use the same account."
                if same
                else (
                    f"gcloud uses {account} but Terraform uses "
                    f"{principal.email}."
                ),
                remedy=(
                    "Run `gcloud auth application-default login` as the "
                    "account that gcloud uses."
                ),
                doc=DOC_WORKSTATION,
            )
        )
    results.append(_bootstrap_user_result(ctx))
    project = ctx.inputs.bootstrap_project
    active_project = ctx.tools.gcloud_project()
    if project and active_project != project:
        results.append(
            CheckResult(
                "identity.project",
                Category.IDENTITY,
                "Active gcloud project",
                Status.WARN,
                f"The active gcloud project is {active_project or 'unset'}, "
                f"not the bootstrap project {project}.",
                remedy=f"Run `gcloud config set project {project}`.",
                doc=DOC_WORKSTATION,
            )
        )
    elif project:
        results.append(
            CheckResult(
                "identity.project",
                Category.IDENTITY,
                "Active gcloud project",
                Status.PASS,
                f"The active gcloud project is {project}.",
            )
        )
    impersonating = {
        name: ctx.environ[name]
        for name in IMPERSONATION_ENV_VARS
        if ctx.environ.get(name)
    }
    results.append(
        CheckResult(
            "identity.impersonation",
            Category.IDENTITY,
            "No stale service account impersonation",
            Status.WARN if impersonating else Status.PASS,
            "Impersonation is set: "
            + ", ".join(f"{k}={v}" for k, v in impersonating.items())
            if impersonating
            else "No impersonation environment variables are set.",
            remedy="Run `unset " + " ".join(IMPERSONATION_ENV_VARS) + "`.",
            doc=DOC_TROUBLESHOOTING,
        )
    )
    return results


def bootstrap_user(ctx):
    """Returns the user that the first Stage 0 apply grants as bootstrap_user.

    The operator can name any user account. Without one, the Application
    Default Credentials identity serves when it is a user account.
    """
    if ctx.inputs.bootstrap_user:
        return ctx.inputs.bootstrap_user
    principal = ctx.principal
    if principal and principal.kind == api.PrincipalKind.USER:
        return principal.email
    return None


def _bootstrap_user_result(ctx):
    """Checks that the first Stage 0 apply has a user for bootstrap_user.

    Stage 0 binds `user:<bootstrap_user>`, so the value must be a user
    account. Terraform itself may run as a service account.
    """
    principal = ctx.principal
    configured = ctx.inputs.bootstrap_user
    runs_as = (
        f" Terraform runs as {principal.email}."
        if principal and principal.email and principal.email != configured
        else ""
    )
    common = {
        "check_id": "identity.bootstrap_user",
        "category": Category.IDENTITY,
        "title": "Bootstrap user",
        "doc": DDG_STAGE0,
    }
    if configured and configured.endswith(naming.SERVICE_ACCOUNT_SUFFIX):
        return CheckResult(
            status=Status.FAIL,
            detail=(
                f"{configured} is a service account, but Stage 0 grants "
                "`bootstrap_user` as a `user:` principal."
            ),
            remedy="Pass --bootstrap-user with a user account email.",
            **common,
        )
    user = bootstrap_user(ctx)
    if user:
        return CheckResult(
            status=Status.PASS,
            detail=(
                f"The first Stage 0 apply grants {user} as `bootstrap_user`."
                f"{runs_as}"
            ),
            **common,
        )
    if principal and principal.kind == api.PrincipalKind.SERVICE_ACCOUNT:
        return CheckResult(
            status=Status.FAIL,
            detail=(
                f"Terraform runs as the service account {principal.email}, "
                "and Stage 0 needs a user account as `bootstrap_user`."
            ),
            remedy=(
                "Pass --bootstrap-user with a user account email, and set "
                "the same value as the `bootstrap_user` answer, which "
                "stellar render writes for the first Stage 0 apply."
            ),
            **common,
        )
    return CheckResult(
        status=Status.WARN,
        detail="The bootstrap user cannot be determined.",
        remedy="Pass --bootstrap-user with a user account email.",
        **common,
    )


def check_organization(ctx):
    """Resolves the organization and compares it with the inputs."""
    category = Category.ORGANIZATION
    org_id = ctx.inputs.org_id
    if org_id is None:
        try:
            orgs = ctx.cloud.search_organizations()
        except api.CloudError as error:
            orgs, detail = [], f"Cannot list organizations: {error}"
        else:
            detail = (
                "No organization is visible to this identity."
                if not orgs
                else "More than one organization is visible: "
                + _listed(org.org_id for org in orgs)
            )
        if len(orgs) != 1:
            return [
                CheckResult(
                    "org.access",
                    category,
                    "Organization access",
                    Status.FAIL,
                    detail,
                    remedy="Pass --org with the numeric organization ID.",
                    doc=DOC_ORGANIZATION,
                )
            ]
        ctx.org = orgs[0]
        found = f"Using organization {ctx.org.org_id} ({ctx.org.domain})."
    else:
        try:
            ctx.org = ctx.cloud.get_organization(org_id)
        except api.CloudError as error:
            ctx.org, found = None, f"Access denied: {error}"
        else:
            found = (
                f"Organization {org_id} is {ctx.org.domain}." if ctx.org else ""
            )
        if ctx.org is None:
            return [
                CheckResult(
                    "org.access",
                    category,
                    "Organization access",
                    Status.FAIL,
                    found or f"Organization {org_id} does not exist.",
                    remedy=(
                        "Check the organization ID with "
                        "`gcloud organizations list`."
                    ),
                    doc=DOC_ORGANIZATION,
                )
            ]
    results = [
        CheckResult(
            "org.access",
            category,
            "Organization access",
            Status.PASS,
            found,
            doc=DOC_ORGANIZATION,
        )
    ]
    for field, actual, label in (
        ("domain", ctx.org.domain, "Organization domain"),
        ("customer_id", ctx.org.customer_id, "Directory customer ID"),
    ):
        expected = getattr(ctx.inputs, field)
        if expected is None:
            continue
        same = expected.lower() == actual.lower()
        results.append(
            CheckResult(
                f"org.{field}",
                category,
                label,
                Status.PASS if same else Status.FAIL,
                f"{label} is {actual}."
                if same
                else f"{label} is {actual}, not {expected}.",
                remedy="Fix the value to match `gcloud organizations list`.",
                doc=DOC_ORGANIZATION,
            )
        )
    return results


def _count(items, noun):
    """Returns a count with a singular or plural noun, like `1 permission`."""
    return f"{len(items)} {noun}{'' if len(items) == 1 else 's'}"


def _role_result(role, testable, granted, scope):
    missing = sorted(testable - granted)
    if not testable:
        return CheckResult(
            f"iam.{role}",
            Category.IAM,
            role,
            Status.WARN,
            f"None of this role's permissions can be tested on the {scope}.",
            remedy="Confirm the grant in the console.",
            doc=DOC_IAM,
        )
    if missing:
        return CheckResult(
            f"iam.{role}",
            Category.IAM,
            role,
            Status.FAIL,
            f"Missing {len(missing)} of {_count(testable, 'permission')} on "
            f"the {scope}, including {_listed(missing[:3])}.",
            remedy=(
                "Grant the role at the organization level, for example with "
                "`fast/stages-aw/0-bootstrap/setIAM.sh <email> <org_id>`."
            ),
            doc=DOC_IAM,
        )
    return CheckResult(
        f"iam.{role}",
        Category.IAM,
        role,
        Status.PASS,
        "The deploying identity holds "
        + (
            "the only testable permission"
            if len(testable) == 1
            else f"all {len(testable)} testable permissions"
        )
        + f" on the {scope}.",
        doc=DOC_IAM,
    )


def check_iam_roles(ctx):
    """Checks that the caller holds every role that `setIAM.sh` grants.

    The check tests effective permissions with testIamPermissions, so it is
    correct whether a role is granted directly, through a group, or by
    inheritance. Billing Account Administrator may be granted on the billing
    account instead of the organization, so it is tested there when a
    billing account is given. With `billing_no_iam`, Stage 0 never manages
    billing IAM, so the role is not required and `check_billing` tests
    project linking instead.
    """
    if ctx.org is None:
        return [_skip("iam.roles", Category.IAM, "Organization roles", "--org")]
    try:
        return _role_results(ctx)
    except api.CloudError as error:
        return [
            CheckResult(
                "iam.roles",
                Category.IAM,
                "Organization roles",
                Status.FAIL,
                f"Cannot test the organization roles: {error}",
                doc=DOC_IAM,
            )
        ]


def _role_results(ctx):
    org_resource = (
        f"//cloudresourcemanager.googleapis.com/organizations/{ctx.org.org_id}"
    )
    org_testable = ctx.cloud.testable_permissions(org_resource)
    roles = [
        role
        for role in ctx.repo.required_roles()
        if not (role == BILLING_ADMIN_ROLE and ctx.inputs.billing_no_iam)
    ]
    billing_account = ctx.inputs.billing_account
    per_role = {}
    for role in roles:
        if role == BILLING_ADMIN_ROLE and billing_account:
            continue
        per_role[role] = set(ctx.cloud.role_permissions(role)) & org_testable
    wanted = sorted(set().union(*per_role.values())) if per_role else []
    granted = ctx.cloud.granted_org_permissions(ctx.org.org_id, wanted)
    results = []
    for role in roles:
        if role in per_role:
            results.append(
                _role_result(role, per_role[role], granted, "organization")
            )
            continue
        billing_resource = (
            f"//cloudbilling.googleapis.com/billingAccounts/{billing_account}"
        )
        testable = set(ctx.cloud.role_permissions(role)) & (
            ctx.cloud.testable_permissions(billing_resource)
        )
        try:
            billing_granted = ctx.cloud.granted_billing_permissions(
                billing_account, sorted(testable)
            )
        except api.CloudError as error:
            results.append(
                CheckResult(
                    f"iam.{role}",
                    Category.IAM,
                    role,
                    Status.FAIL,
                    f"Cannot test this role on the billing account: {error}",
                    doc=DOC_IAM,
                )
            )
            continue
        if testable:
            ctx.billing_access = testable <= set(billing_granted)
        item = _role_result(role, testable, billing_granted, "billing account")
        # With billing_mode "org", Stage 0 grants billing roles on the
        # organization, so it needs the role only to create resources.
        if (
            item.status == Status.FAIL
            and ctx.billing_access is False
            and _stage0_precreated(ctx)
        ):
            item = _downgraded(item)
        results.append(item)
    return results


def check_billing(ctx):
    """Checks the billing account, project linking and pre-created resources.

    The `billing.precreate` result lists the Stage 0 resources that need
    billing access at creation when the deploying identity lacks it. When
    import blocks adopt every one of them, Stage 0 needs no billing access,
    so the account and link failures become warnings.
    """
    category = Category.BILLING
    account_id = ctx.inputs.billing_account
    if account_id is None:
        return [
            _skip(
                "billing.account",
                category,
                "Billing account",
                "--billing-account",
            ),
            _skip(
                PRECREATE_CHECK,
                category,
                "Pre-created resources",
                "--billing-account",
            ),
        ]
    account, denied = _billing_account_result(ctx, account_id)
    covers = [account] if denied else []
    results = [account]
    if ctx.inputs.billing_no_iam:
        link = _billing_link_result(ctx, account_id)
        if ctx.billing_access is False:
            covers.append(link)
        results.append(link)
    results.append(_billing_project_result(ctx, account_id))
    precreate, covered = _precreate_result(ctx, account_id)
    if covered:
        results = [
            _downgraded(item) if item in covers else item for item in results
        ]
    results.append(precreate)
    return results


def _billing_account_result(ctx, account_id):
    """Checks that the billing account exists and is open.

    Returns:
        The result, and whether the lookup failed for lack of access.
    """
    # The ID hint only helps when the lookup worked; a failed lookup already
    # explains its own fix in the detail.
    remedy = "Check the ID with `gcloud billing accounts list`."
    denied = False
    try:
        account = ctx.cloud.get_billing_account(account_id)
    except api.ApiDisabledError as error:
        account, remedy = None, None
        detail = f"Cannot read billing account {account_id}: {error}"
    except api.AccessDeniedError as error:
        account, denied = None, True
        detail = f"Cannot read billing account {account_id}: {error}"
        remedy = (
            "Grant the deploying identity access to the billing account, "
            f"{_PRECREATE_HINT}."
        )
    except api.CloudError as error:
        account, remedy = None, None
        detail = f"Cannot read billing account {account_id}: {error}"
    else:
        detail = f"Billing account {account_id} does not exist."
    if account is not None and account.is_open:
        return CheckResult(
            "billing.account",
            Category.BILLING,
            "Billing account",
            Status.PASS,
            f"Billing account {account_id} is open.",
            doc=DOC_BOOTSTRAP,
        ), denied
    if account is not None:
        detail = f"Billing account {account_id} is closed."
    return CheckResult(
        "billing.account",
        Category.BILLING,
        "Billing account",
        Status.FAIL,
        detail,
        remedy=remedy,
        doc=DOC_BOOTSTRAP,
    ), denied


def _billing_project_result(ctx, account_id):
    """Checks that the bootstrap project bills to the billing account."""
    category = Category.BILLING
    project = ctx.inputs.bootstrap_project
    if project is None:
        return _skip(
            "billing.project",
            category,
            "Bootstrap project billing",
            "--project",
        )
    try:
        link = ctx.cloud.project_billing(project)
    except api.CloudError as error:
        return CheckResult(
            "billing.project",
            category,
            "Bootstrap project billing",
            Status.FAIL,
            f"Cannot read the billing link of {project}: {error}",
            doc=DOC_BOOTSTRAP,
        )
    linked = link.enabled and link.account_id == account_id
    if linked:
        detail = f"{project} is billed to {account_id}."
    elif link.enabled:
        detail = f"{project} is billed to {link.account_id}, not {account_id}."
    else:
        detail = f"{project} has no billing account."
    return CheckResult(
        "billing.project",
        category,
        "Bootstrap project billing",
        Status.PASS if linked else Status.FAIL,
        detail,
        remedy=(
            f"Run `gcloud billing projects link {project} "
            f"--billing-account={account_id}`."
        ),
        doc=DOC_BOOTSTRAP,
    )


def _billing_link_result(ctx, account_id):
    """Checks that the caller can link new projects to the billing account.

    testIamPermissions works without read access to the account, so this
    check runs even when the account lookup fails.
    """
    try:
        granted = ctx.cloud.granted_billing_permissions(
            account_id, [BILLING_LINK_PERMISSION]
        )
    except api.CloudError as error:
        return CheckResult(
            "billing.link",
            Category.BILLING,
            "Project billing link",
            Status.FAIL,
            f"Cannot test project linking on the billing account: {error}",
            doc=DOC_BOOTSTRAP,
        )
    ctx.billing_access = BILLING_LINK_PERMISSION in granted
    if ctx.billing_access:
        return CheckResult(
            "billing.link",
            Category.BILLING,
            "Project billing link",
            Status.PASS,
            f"The deploying identity can link new projects to {account_id}.",
            doc=DOC_BOOTSTRAP,
        )
    return CheckResult(
        "billing.link",
        Category.BILLING,
        "Project billing link",
        Status.FAIL,
        f"The deploying identity cannot link new projects to {account_id}, "
        f"because it lacks {BILLING_LINK_PERMISSION}.",
        remedy=(
            f"Ask a billing account administrator to grant {BILLING_USER} "
            f"on the billing account, {_PRECREATE_HINT}."
        ),
        doc=DOC_BOOTSTRAP,
    )


def _downgraded(item):
    """Turns a billing access FAIL into a WARN once Stage 0 needs no access."""
    return dataclasses.replace(
        item,
        status=Status.WARN,
        detail=(
            f"{item.detail.rstrip('.')}. Stage 0 needs no billing access, "
            "because the resources that need it are pre-created. Stages 1 "
            "to 3 still link new projects to the billing account, see "
            f"{PRECREATE_CHECK}."
        ),
        remedy=None,
    )


def _billing_requirement(ctx):
    """Returns the billing role and permission wording Stage 0 needs."""
    if ctx.inputs.billing_no_iam:
        return BILLING_USER, BILLING_LINK_PERMISSION
    return BILLING_ADMIN, BILLING_ADMIN


def _later_stages_note(ctx):
    """Names the later stages that link projects to the billing account.

    Stage 1 creates the tenant projects, and Stages 2 and 3 create the
    networking and security projects, each through the `google.billing`
    provider that the `billing_override` answer moves to a user account.
    """
    imported = set(ctx.inputs.imported_project_ids)
    tenants = [
        pid for pid in ctx.inputs.tenant_project_ids if pid not in imported
    ]
    note = ""
    if tenants:
        note = (
            " Stage 1 also links these tenant projects to the billing "
            f"account: {', '.join(tenants)}."
        )
    return note + (
        " Stages 2 and 3 link their networking and security projects to the "
        "billing account too, so set the billing_override answer for these "
        "stages to run the linkage as a user with billing access."
    )


def _billing_resources(ctx):
    """Returns the Stage 0 resources that need billing access to create."""
    inputs = ctx.inputs
    return ctx.repo.billing_resources(
        prefix=inputs.prefix,
        regime=inputs.regime,
        location=inputs.compliance_location or inputs.region or "<location>",
        no_iam=inputs.billing_no_iam,
        is_org_level=inputs.billing_is_org_level,
        org_id=ctx.org.org_id if ctx.org else inputs.org_id,
    )


def _precreate_blockers(ctx, resources):
    """Returns why Stage 0 needs billing access even when imports adopt all.

    Args:
        ctx: The preflight context.
        resources: Result of `_billing_resources`.

    Returns:
        One sentence per Stage 0 use of the billing account that
        pre-creation cannot replace, empty when there is none.
    """
    inputs = ctx.inputs
    found = []
    if repo_lib.billing_iam_on_account(
        no_iam=inputs.billing_no_iam, is_org_level=inputs.billing_is_org_level
    ):
        found.append(
            "Stage 0 grants roles on the billing account itself, because "
            "billing.no_iam is false and billing.is_org_level is false, "
            f"which needs {BILLING_ADMIN}."
        )
    if inputs.billing_budget:
        found.append(
            f"Stage 0 creates the {repo_lib.BUDGET_MODULE} budget on the "
            "billing account, because the budget.amount answer is set, which "
            f"needs {BILLING_ADMIN} or {BILLING_COSTS_MANAGER}."
        )
    workload = ctx.repo.assured_workload()
    if workload.replaced_on_import and any(
        item.address == workload.address for item in resources
    ):
        fields = ", ".join(workload.replaced_on_import)
        found.append(
            "Stage 0 cannot adopt a pre-created Assured Workloads workload, "
            f"because organization.tf sets {fields} without listing it in "
            "lifecycle.ignore_changes, and the Assured Workloads API never "
            "returns it, so the import plans a replacement that needs "
            "billing access."
        )
    return found


def _stage0_precreated(ctx):
    """Returns whether Stage 0 needs no billing access for these inputs.

    That holds when import blocks adopt every resource that needs billing
    access at creation and nothing else in Stage 0 uses the account.
    """
    inputs = ctx.inputs
    if inputs.prefix is None or inputs.regime is None:
        return False
    resources = _billing_resources(ctx)
    imported = set(inputs.imported_addresses)
    return all(
        item.address in imported for item in resources
    ) and not _precreate_blockers(ctx, resources)


def _precreate_result(ctx, account_id):
    """Lists the Stage 0 resources to pre-create without billing access.

    Each Stage 0 project links to the billing account, and the Assured
    Workloads API only creates a workload for a caller that can use the
    billing account. A deployer without that access needs someone who has
    it to create these resources, so Stage 0 imports them instead.

    Returns:
        The result, and whether Stage 0 needs no billing access because
        import blocks adopt every listed resource while the deploying
        identity lacks that access, which makes the billing access failures
        harmless for Stage 0.
    """
    check_id, title = PRECREATE_CHECK, "Pre-created resources"
    category = Category.BILLING
    inputs = ctx.inputs
    role, requirement = _billing_requirement(ctx)
    if ctx.billing_access:
        return CheckResult(
            check_id,
            category,
            title,
            Status.PASS,
            "No pre-creation is needed, because the deploying identity "
            f"holds {requirement} on {account_id}.",
            doc=DDG_STAGE0,
        ), False
    if inputs.prefix is None or inputs.regime is None:
        return _skip(check_id, category, title, "--prefix and --regime"), False
    if ctx.billing_access is None:
        if not inputs.billing_no_iam and ctx.org is None:
            return _skip(check_id, category, title, "--org"), False
        tested = (
            "billing.link"
            if inputs.billing_no_iam
            else f"iam.{BILLING_ADMIN_ROLE}"
        )
        return CheckResult(
            check_id,
            category,
            title,
            Status.SKIP,
            "Not checked, because preflight could not test the billing "
            f"permissions; see the {tested} check.",
        ), False
    resources = _billing_resources(ctx)
    imported = set(inputs.imported_addresses)
    missing = [item for item in resources if item.address not in imported]
    blockers = _precreate_blockers(ctx, resources)
    lacks = f"The deploying identity lacks {requirement} on {account_id}"
    if not missing and not blockers:
        return CheckResult(
            check_id,
            category,
            title,
            Status.PASS,
            f"{lacks}, and import blocks adopt every Stage 0 resource that "
            "needs it: "
            + ", ".join(item.name for item in resources)
            + "."
            + _later_stages_note(ctx),
            doc=DDG_STAGE0,
        ), True
    listed = "; ".join(
        f"{item.create}, imported as {item.address} with ID {item.import_id}"
        for item in missing
    )
    detail = (
        lacks
        + (
            f", so Stage 0 cannot create these resources: {listed}."
            if missing
            else ". Import blocks adopt every Stage 0 resource that needs it."
        )
        + "".join(f" {sentence}" for sentence in blockers)
        + _later_stages_note(ctx)
    )
    who = (
        ctx.principal.email
        if ctx.principal and ctx.principal.email
        else "the deploying identity"
    )
    remedy = (
        f"Grant {role} on billing account {account_id} to {who}, or have "
        "someone with that access pre-create the listed resources, add each "
        f"one to imports.{paths.BOOTSTRAP} in answers.yaml with its import "
        "ID, and run `stellar render`."
    )
    workload = ctx.repo.assured_workload()
    if any(item.address == workload.address for item in missing):
        remedy += (
            " Create the Assured Workloads workload with the billing account, "
            "because the API requires one, and with violation notifications "
            "enabled to match organization.tf."
        )
    if workload.replaced_on_import and any(
        item.address == workload.address for item in resources
    ):
        remedy += (
            " A pre-created workload helps only once organization.tf lists "
            f"{', '.join(workload.replaced_on_import)} in the "
            "lifecycle.ignore_changes of the workload."
        )
    if repo_lib.billing_iam_on_account(
        no_iam=inputs.billing_no_iam, is_org_level=inputs.billing_is_org_level
    ):
        remedy += (
            " Set billing.no_iam to true so Stage 0 manages no billing IAM, "
            "unless you grant that role."
        )
    if inputs.billing_budget:
        remedy += (
            " Remove the budget.amount answer and create the budget after "
            "Stage 0 as a user with billing access, unless you grant that "
            "role."
        )
    return CheckResult(
        check_id,
        category,
        title,
        Status.FAIL,
        detail,
        remedy=remedy,
        doc=DDG_STAGE0,
    ), False


def check_project(ctx):
    """Checks that the bootstrap project exists and has the required APIs."""
    category = Category.PROJECT
    project = ctx.inputs.bootstrap_project
    if project is None:
        return [
            _skip("project.state", category, "Bootstrap project", "--project")
        ]
    try:
        state = ctx.cloud.project_state(project)
    except api.CloudError:
        state = None
    if state != "ACTIVE":
        return [
            CheckResult(
                "project.state",
                category,
                "Bootstrap project",
                Status.FAIL,
                f"{project} does not exist, is not active, or is not "
                "visible to this identity.",
                remedy="Create the project or fix --project.",
                doc=DOC_BOOTSTRAP,
            )
        ]
    results = [
        CheckResult(
            "project.state",
            category,
            "Bootstrap project",
            Status.PASS,
            f"{project} is active.",
            doc=DOC_BOOTSTRAP,
        )
    ]
    required = [*ctx.repo.required_apis(), *EXTRA_APIS]
    try:
        enabled = ctx.cloud.enabled_services(project)
    except api.CloudError as error:
        results.append(
            CheckResult(
                "project.apis",
                category,
                "Required APIs",
                Status.FAIL,
                f"Cannot list the enabled services: {error}",
                doc=DOC_APIS,
            )
        )
        return results
    missing = [api_name for api_name in required if api_name not in enabled]
    results.append(
        CheckResult(
            "project.apis",
            category,
            "Required APIs",
            Status.FAIL if missing else Status.PASS,
            f"Not enabled: {_listed(missing)}."
            if missing
            else f"All {len(required)} required APIs are enabled.",
            remedy=(
                f"Run `gcloud services enable {' '.join(missing)} "
                f"--project={project}`."
            ),
            doc=DOC_APIS,
        )
    )
    return results


def _group_members(ctx):
    """Resolves Stage 0 group keys to IAM members like `main.tf` does.

    A value with a `scheme:` prefix is already a principal. Any other value
    is a group name in the organization domain.
    """
    names = {**ctx.repo.default_groups(), **ctx.inputs.groups}
    return {
        key: naming.group_principal(value, ctx.domain)
        for key, value in names.items()
    }


def _group_emails(ctx):
    members = _group_members(ctx).values()
    return sorted(
        {m.removeprefix("group:") for m in members if m.startswith("group:")}
    )


def check_groups(ctx):
    """Checks that the Stage 0 administrative groups exist."""
    category = Category.GROUPS
    if ctx.domain is None:
        return [_skip("groups", category, "Administrative groups", "--domain")]
    results = []
    for email in _group_emails(ctx):
        try:
            exists = ctx.cloud.group_exists(email)
        except api.CloudError as error:
            return [
                CheckResult(
                    "groups",
                    category,
                    "Administrative groups",
                    Status.MANUAL,
                    f"Cloud Identity cannot be queried ({error}). Confirm "
                    "that these groups exist: " + _listed(_group_emails(ctx)),
                    remedy=(
                        "Create missing groups in the Cloud Setup wizard "
                        "or the Google Admin console."
                    ),
                    doc=DOC_GROUPS,
                )
            ]
        results.append(
            CheckResult(
                f"groups.{email}",
                category,
                email,
                Status.PASS if exists else Status.FAIL,
                "The group exists." if exists else "The group does not exist.",
                remedy="Create the group in the Cloud Setup wizard.",
                doc=DOC_GROUPS,
            )
        )
    return results


def _check_region(ctx):
    region = ctx.inputs.region
    if region is None:
        return _skip("naming.region", Category.NAMING, "Region", "--region")
    regime = ctx.inputs.regime
    supported = regions.supported_regions(regime) if regime else None
    if supported is not None:
        ok = region in supported
        detail = (
            f"{regime} is available in {region}."
            if ok
            else f"{regime} is not available in {region}. Use one of "
            + _listed(supported)
            + "."
        )
    else:
        ok = bool(_REGION_RE.match(region))
        detail = (
            f"{region} is a single US region."
            if ok
            else f"{region} is not a single US region."
        )
        if regime and regime != regions.Regime.COMPLIANCE_REGIME_UNSPECIFIED:
            detail += f" No region table is recorded for {regime}."
    return CheckResult(
        "naming.region",
        Category.NAMING,
        "Region",
        Status.PASS if ok else Status.FAIL,
        detail,
        remedy=f"Pick a supported region, see {regions.LOCATIONS_DOC}.",
        doc=DDG_PREREQUISITES,
    )


def _guarded(check_id, title, run):
    """Runs one sub-check and reports a Google Cloud error as a warning."""
    try:
        return run()
    except api.CloudError as error:
        return CheckResult(
            check_id,
            Category.NAMING,
            title,
            Status.WARN,
            f"Cannot check for existing resources: {error}",
        )


@dataclasses.dataclass(frozen=True)
class _ProjectGroup:
    """Check ids and wording for one set of project IDs a stage creates."""

    check_id: str
    title: str
    deleted_id: str
    deleted_title: str
    stage: str


_STAGE0_PROJECTS = _ProjectGroup(
    "naming.projects",
    "Project IDs",
    "naming.deleted_projects",
    "Soft-deleted projects",
    "Stage 0",
)
_TENANT_PROJECTS = _ProjectGroup(
    "naming.tenant_projects",
    "Tenant project IDs",
    "naming.deleted_tenant_projects",
    "Soft-deleted tenant projects",
    "Stage 1",
)


def _project_states(ctx, project_ids):
    return {pid: ctx.cloud.visible_project_state(pid) for pid in project_ids}


def _undelete(project_ids):
    return " ".join(f"`gcloud projects undelete {pid}`" for pid in project_ids)


def _project_results(ctx, project_ids, group=_STAGE0_PROJECTS):
    """Checks a stage's project IDs for active and soft-deleted holders.

    A deleted project keeps its ID for 30 days, so a soft-deleted holder
    blocks the stage even on a redeploy. See issue #50.
    """
    try:
        states = _project_states(ctx, project_ids)
    except api.CloudError as error:
        return [
            CheckResult(
                group.check_id,
                Category.NAMING,
                group.title,
                Status.WARN,
                f"Cannot check for existing resources: {error}",
            )
        ]
    active = [pid for pid, state in states.items() if state == "ACTIVE"]
    deleted = [
        pid for pid, state in states.items() if state == "DELETE_REQUESTED"
    ]
    results = [
        _collision(
            ctx,
            group.check_id,
            group.title,
            active,
            "projects",
            unseen_note=(
                " Project IDs are global, so a project outside this "
                f"identity's view can still own one, which {group.stage} "
                "reports as a conflict."
            ),
        )
    ]
    if deleted:
        results.append(
            CheckResult(
                group.deleted_id,
                Category.NAMING,
                group.deleted_title,
                Status.FAIL,
                "Soft-deleted projects still hold these IDs for up to 30 "
                f"days after deletion: {_listed(deleted)}.",
                remedy=(
                    "Pick a different prefix, or restore the projects with "
                    f"{_undelete(deleted)} if they belong to this deployment."
                ),
                doc=DDG_PREREQUISITES,
            )
        )
    else:
        results.append(
            CheckResult(
                group.deleted_id,
                Category.NAMING,
                group.deleted_title,
                Status.PASS,
                "No visible soft-deleted project holds a "
                f"{group.stage} project ID.",
            )
        )
    return results


def _imported_result(ctx, project_ids):
    """Checks that the projects import blocks adopt exist and are active.

    Some organizations pre-create projects because only a human can link
    them to billing. Terraform then imports them, so an active
    holder is expected, and a missing or soft-deleted one makes the import
    fail.
    """
    check_id = "naming.imported_projects"
    title = "Imported projects"
    try:
        states = _project_states(ctx, project_ids)
    except api.CloudError as error:
        return CheckResult(
            check_id,
            Category.NAMING,
            title,
            Status.WARN,
            f"Cannot check the pre-created projects: {error}",
        )
    deleted = [
        pid for pid, state in states.items() if state == "DELETE_REQUESTED"
    ]
    missing = [pid for pid, state in states.items() if state is None]
    if not deleted and not missing:
        return CheckResult(
            check_id,
            Category.NAMING,
            title,
            Status.PASS,
            f"Pre-created and active, so import blocks adopt them: "
            f"{_listed(project_ids)}.",
        )
    problems = []
    remedies = []
    if missing:
        problems.append(
            "these projects do not exist or this identity cannot see "
            f"them: {_listed(missing)}"
        )
        remedies.append(
            "Pre-create the missing projects and grant this identity access "
            "to them, or remove their entries from `imports` in answers.yaml."
        )
    if deleted:
        problems.append(f"these projects are soft-deleted: {_listed(deleted)}")
        remedies.append(f"Restore the projects with {_undelete(deleted)}.")
    return CheckResult(
        check_id,
        Category.NAMING,
        title,
        Status.FAIL,
        "Import blocks adopt projects that Terraform cannot import, because "
        + "; ".join(problems)
        + ".",
        remedy=" ".join(remedies),
        doc=DDG_STAGE0,
    )


def _collision(ctx, check_id, title, taken, what, unseen_note=""):
    if not taken:
        return CheckResult(
            check_id,
            Category.NAMING,
            title,
            Status.PASS,
            f"No existing {what} use this prefix.{unseen_note}",
        )
    redeploy = ctx.inputs.redeploy
    return CheckResult(
        check_id,
        Category.NAMING,
        title,
        Status.WARN if redeploy else Status.FAIL,
        f"These {what} already exist: {_listed(taken)}.",
        remedy=(
            "Pick a different prefix, or pass --redeploy if this is your own "
            "earlier deployment with the same prefix."
        ),
        doc=DDG_PREREQUISITES,
    )


def check_naming(ctx):
    """Checks the prefix format, region choice and name collisions."""
    results = [_check_region(ctx)]
    prefix = ctx.inputs.prefix
    if prefix is None:
        results.append(
            _skip("naming.prefix", Category.NAMING, "Prefix", "--prefix")
        )
        return results
    limit = ctx.repo.prefix_max_length()
    valid = bool(paths.PREFIX_RE.match(prefix)) and len(prefix) <= limit
    results.append(
        CheckResult(
            "naming.prefix",
            Category.NAMING,
            "Prefix format",
            Status.PASS if valid else Status.FAIL,
            f"{prefix} is a valid prefix."
            if valid
            else (
                f"{prefix} must start with a lowercase letter, use only "
                f"lowercase letters, digits and hyphens, and be at most "
                f"{limit} characters."
            ),
            doc=DDG_PREREQUISITES,
        )
    )
    if not valid:
        return results
    # Import blocks adopt pre-created projects, so an active holder of one of
    # these IDs is expected rather than a collision.
    imported = sorted(set(ctx.inputs.imported_project_ids))
    # Stage 0 skips the billing export project for some billing answers, so
    # a holder of that ID is no collision then.
    created = ctx.repo.created_stage0_projects(
        no_iam=ctx.inputs.billing_no_iam,
        is_org_level=ctx.inputs.billing_is_org_level,
    )
    project_ids = [
        pid
        for project in created
        if (pid := naming.stage0_project_id(prefix, project.name))
        not in imported
    ]
    results.extend(_project_results(ctx, project_ids))
    tenant_ids = [
        pid for pid in ctx.inputs.tenant_project_ids if pid not in imported
    ]
    if tenant_ids:
        results.extend(_project_results(ctx, tenant_ids, _TENANT_PROJECTS))
    if imported:
        results.append(_imported_result(ctx, imported))
    buckets = [
        naming.state_bucket(prefix, name) for name in naming.STATE_BUCKET_NAMES
    ]
    results.append(
        _guarded(
            "naming.buckets",
            "State buckets",
            lambda: _collision(
                ctx,
                "naming.buckets",
                "State buckets",
                [name for name in buckets if ctx.cloud.bucket_exists(name)],
                "buckets",
            ),
        )
    )
    if ctx.org is not None:
        results.append(
            _guarded(
                "naming.folder",
                "Assured Workloads folder",
                lambda: _folder_result(ctx, prefix),
            )
        )
    return results


def _folder_result(ctx, prefix):
    """Checks the Assured Workloads folder name for a collision.

    The workload creates the folder, so when an import block adopts a
    pre-created workload, an existing folder of that name is expected.
    """
    check_id, title = "naming.folder", "Assured Workloads folder"
    folder = naming.workload_folder_name(prefix)
    exists = bool(ctx.cloud.find_folders(ctx.org.org_id, folder))
    address = ctx.repo.assured_workload().address
    if address not in ctx.inputs.imported_addresses:
        return _collision(
            ctx, check_id, title, [folder] if exists else [], "folders"
        )
    if exists:
        return CheckResult(
            check_id,
            Category.NAMING,
            title,
            Status.PASS,
            f"{folder} is pre-created; Stage 0 imports the workload.",
        )
    return CheckResult(
        check_id,
        Category.NAMING,
        title,
        Status.WARN,
        f"imports.{paths.BOOTSTRAP} adopts the workload {address}, but no "
        f"folder named {folder} is visible to this identity.",
        remedy=(
            "Confirm that the pre-created workload exists and that its "
            f"consumer folder is named {folder}, because the import fails "
            "otherwise."
        ),
        doc=DDG_STAGE0,
    )


def _holder_member(ctx, holder, groups):
    """Resolves a Stage 0 role holder to the IAM member it grants."""
    prefix = ctx.inputs.prefix
    match holder.kind:
        case repo_lib.HolderKind.GROUP:
            return groups.get(holder.key)
        case repo_lib.HolderKind.SERVICE_ACCOUNT if prefix:
            email = naming.automation_sa_email(prefix, holder.key)
            return f"serviceAccount:{email}"
        case repo_lib.HolderKind.BOOTSTRAP_USER if bootstrap_user(ctx):
            return f"user:{bootstrap_user(ctx)}"
        case repo_lib.HolderKind.DOMAIN if ctx.domain:
            return f"domain:{ctx.domain}"
    return None


def _removed_grants(ctx, bindings):
    """Lists existing grants that the first Stage 0 apply removes."""
    authoritative = ctx.repo.authoritative_bindings()
    groups = _group_members(ctx)
    removed = []
    for binding in bindings:
        if binding.role not in authoritative:
            continue
        kept = {
            _holder_member(ctx, holder, groups)
            for holder in authoritative[binding.role]
        }
        removed.extend(
            f"{binding.role} {member}"
            for member in binding.members
            if member not in kept and not member.startswith("deleted:")
        )
    return sorted(removed)


def check_shared_org(ctx):
    """Flags org-wide resources and IAM grants that Stage 0 would change."""
    category = Category.SHARED_ORG
    if ctx.org is None:
        return [_skip("shared", category, "Shared organization", "--org")]
    org_id = ctx.org.org_id
    results = []
    try:
        existing = [
            f"custom role {role_id}"
            for role_id in ctx.repo.custom_role_ids()
            if ctx.cloud.custom_role_exists(org_id, role_id)
        ]
        existing += [
            f"custom constraint {name}"
            for name in ctx.repo.custom_constraint_names()
            if ctx.cloud.custom_constraint_exists(org_id, name)
        ]
        existing += [
            f"log sink {name}"
            for name in ctx.repo.log_sink_names()
            if ctx.cloud.log_sink_exists(org_id, name)
        ]
    except api.CloudError as error:
        results.append(
            CheckResult(
                "shared.resources",
                category,
                "Organization-wide names",
                Status.WARN,
                f"Cannot check organization-wide resources: {error}",
            )
        )
    else:
        results.append(
            CheckResult(
                "shared.resources",
                category,
                "Organization-wide names",
                Status.WARN if existing else Status.PASS,
                (
                    "Stage 0 creates these organization-wide resources, and "
                    f"they already exist: {_listed(existing)}."
                )
                if existing
                else "No Stage 0 organization-wide resources exist yet.",
                remedy=(
                    "Another deployment or an earlier run created them. "
                    "Import them into Stage 0 state before the first apply, "
                    "or delete them if nothing uses them."
                ),
                doc=DDG_PREREQUISITES,
            )
        )
    results.append(_org_policy_result(ctx, org_id))
    try:
        bindings = ctx.cloud.org_iam_bindings(org_id)
    except api.CloudError as error:
        results.append(
            CheckResult(
                "shared.iam",
                category,
                "Authoritative IAM roles",
                Status.WARN,
                f"Cannot read the organization IAM policy: {error}",
            )
        )
        return results
    removed = _removed_grants(ctx, bindings)
    results.append(
        CheckResult(
            "shared.iam",
            category,
            "Authoritative IAM roles",
            Status.WARN if removed else Status.PASS,
            (
                f"The first Stage 0 apply removes {len(removed)} existing "
                f"grants from roles it manages authoritatively: "
                f"{_listed(removed)}."
            )
            if removed
            else "No existing grants would be removed by Stage 0.",
            remedy=(
                "Review these grants with the organization administrators "
                "before Stage 0, because Terraform removes them."
            ),
            doc=DOC_IAM,
        )
    )
    return results


def _policies(names):
    noun = "policy" if len(names) == 1 else "policies"
    return f"{len(names)} existing organization {noun}"


def _org_policy_result(ctx, org_id):
    """Checks that answers.yaml lists the policies Stage 0 must import.

    The final Stage 0 apply creates every policy that it declares, and
    creating a policy that already exists fails, so each existing one needs
    an import block. Without answers.yaml, or on a redeploy, the check
    only counts the existing policies.
    """
    check_id = "shared.org_policies"
    title = "Existing organization policies"
    try:
        existing = ctx.cloud.list_org_policies(org_id)
    except api.CloudError as error:
        return CheckResult(
            check_id,
            Category.SHARED_ORG,
            title,
            Status.WARN,
            f"Cannot list the organization policies: {error}",
        )
    kept = ctx.repo.scan_org_policies(existing, ctx.inputs.regime).kept
    if not kept:
        return CheckResult(
            check_id,
            Category.SHARED_ORG,
            title,
            Status.PASS,
            "No organization policy that Stage 0 declares exists yet.",
        )
    listed = ctx.inputs.existing_org_policies
    if listed is None or ctx.inputs.redeploy:
        # Without answers.yaml there is no list to compare, and after a
        # Stage 0 apply its state already holds the policies it created,
        # so only report the count.
        return CheckResult(
            check_id,
            Category.SHARED_ORG,
            title,
            Status.PASS,
            f"Stage 0 declares {_policies(kept)}. "
            + (
                "This is a redeploy, so Stage 0 state already holds the "
                "policies it created."
                if ctx.inputs.redeploy
                else "Run `stellar imports scan` after `stellar init` so "
                "the final Stage 0 apply imports them."
            ),
        )
    missing = sorted(set(kept) - set(listed))
    if not missing:
        return CheckResult(
            check_id,
            Category.SHARED_ORG,
            title,
            Status.PASS,
            f"Stage 0 declares {_policies(kept)}, and "
            "existing_org_policies lists every one for import.",
        )
    return CheckResult(
        check_id,
        Category.SHARED_ORG,
        title,
        Status.WARN,
        f"Stage 0 declares {_policies(kept)}, and existing_org_policies "
        f"does not list {len(missing)} of them for import: "
        f"{_listed(missing)}.",
        remedy=(
            "Run `stellar imports scan`, then `stellar render`, so the final "
            "Stage 0 apply imports these policies instead of failing to "
            "create them."
        ),
        doc=DDG_STAGE0,
    )


def check_manual(ctx):
    """Lists prerequisites that only a person can confirm."""
    del ctx  # Manual confirmations do not depend on inputs.
    items = (
        (
            "manual.super_admin",
            "Super Admin",
            "Confirm that the deploying user is a Google Workspace or Cloud "
            "Identity Super Admin at https://admin.google.com/ac/roles.",
            DOC_ORGANIZATION,
        ),
        (
            "manual.access_transparency",
            "Access Transparency",
            "Confirm that Access Transparency is enabled at "
            "https://console.cloud.google.com/iam-admin/settings.",
            DOC_FEATURES,
        ),
        (
            "manual.quota",
            "Project quota",
            "Confirm that the project quota allows at least 13 new projects.",
            DOC_FEATURES,
        ),
    )
    return [
        CheckResult(
            check_id, Category.MANUAL, title, Status.MANUAL, detail, doc=doc
        )
        for check_id, title, detail, doc in items
    ]


ALL_CHECKS = (
    check_tools,
    check_identity,
    check_organization,
    check_iam_roles,
    check_billing,
    check_project,
    check_groups,
    check_naming,
    check_shared_org,
    check_manual,
)
