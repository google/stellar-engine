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

"""Names that the stage code derives from the prefix and other answers.

Each function mirrors one Terraform expression and names it, so the answers
model, the wizard and preflight build every name the same way, and a change
in the stage code has one place to follow here. The functions take plain
values, so callers with incomplete answers, such as the wizard, use them
too.
"""

from collections.abc import Iterable, Mapping
import re

# Service account emails end in this domain, and Stage 0 grants
# `bootstrap_user` as a `user:` principal, so it must not be one.
SERVICE_ACCOUNT_SUFFIX = ".gserviceaccount.com"
# `0-bootstrap/main.tf` local.principals keeps values that already carry a
# principal type, such as `user:admin@example.com`.
PRINCIPAL_TYPE_RE = re.compile(r"^[a-zA-Z]+:")
# The `name` of the automation project in `0-bootstrap/automation.tf`,
# which hosts the automation service accounts and state buckets.
AUTOMATION_PROJECT_NAME = "iac-core-0"
# The state buckets of `0-bootstrap/automation.tf`.
STATE_BUCKET_NAMES = ("bootstrap", "outputs", "resman")
# The IAM principal types that `principal` prefixes, as in `user:<email>`.
USER = "user"
SERVICE_ACCOUNT = "serviceAccount"
DOMAIN = "domain"
# The `google_project` instance of `modules/project`, which ends the address
# of every project a module call creates.
PROJECT_ADDRESS_SUFFIX = "google_project.project[0]"
# The Stage 1 modules in `1-resman/branch-tenants.tf` that create each
# tenant's projects, in the order of `tenant_project_ids`.
TENANT_PROJECT_MODULES = (
    "tenant-self-iac-projects",
    "tenant-self-main-projects",
)


def kms_protection_level(regime: str, explicit: str | None = None) -> str:
    """Returns the CMEK protection level Stage 0 uses.

    Mirrors `local.kms_protection_level` in `0-bootstrap/kms.tf`: an
    explicit value wins, else SOFTWARE for FEDRAMP_MODERATE and HSM for
    every other regime.

    Args:
        regime: Assured Workloads regime, such as `IL5`.
        explicit: The `kms_protection_level` answer, or None.
    """
    if explicit:
        return explicit
    if regime == "FEDRAMP_MODERATE":
        return "SOFTWARE"
    return "HSM"


def stage0_project_id(prefix: str, name: str) -> str:
    """Returns the ID of a Stage 0 project, `<prefix>-prod-<name>`.

    Mirrors the `modules/project` calls in `0-bootstrap`, which join
    `local.prefix`, `<prefix>-prod`, and the `name` with a hyphen.

    Args:
        prefix: Deployment prefix.
        name: Project name, such as `iac-core-0`.
    """
    return f"{prefix}-prod-{name}"


def automation_project_id(prefix: str) -> str:
    """Returns the ID of the automation project, `<prefix>-prod-iac-core-0`.

    It holds the automation service accounts and the state buckets.

    Args:
        prefix: Deployment prefix.
    """
    return stage0_project_id(prefix, AUTOMATION_PROJECT_NAME)


def automation_sa_email(prefix: str, name: str) -> str:
    """Returns the email of a Stage 0 automation service account.

    Mirrors the `modules/iam-service-account` calls in
    `0-bootstrap/automation.tf`, which live in the automation project.

    Args:
        prefix: Deployment prefix.
        name: Service account name, such as `bootstrap-0`.
    """
    account = stage0_project_id(prefix, name)
    project = automation_project_id(prefix)
    return f"{account}@{project}.iam{SERVICE_ACCOUNT_SUFFIX}"


def state_bucket(prefix: str, name: str) -> str:
    """Returns the name of a Stage 0 state bucket.

    Mirrors the `modules/gcs` calls in `0-bootstrap/automation.tf`, whose
    `iac-core-<name>-0` names get the `<prefix>-prod` prefix.

    Args:
        prefix: Deployment prefix.
        name: Bucket name from `STATE_BUCKET_NAMES`, such as `outputs`.
    """
    return f"{prefix}-prod-iac-core-{name}-0"


def group_name(
    groups: Mapping[str, str], defaults: Mapping[str, str], key: str
) -> str:
    """Returns a Stage 0 group value: the renamed one or the repo default.

    Args:
        groups: The `groups` answers, which rename some groups.
        defaults: The default group values from the Stage 0 `groups` type.
        key: Group key such as `gcp-devops`.

    Raises:
        KeyError: If the key is not a field of the Stage 0 `groups` type.
    """
    if key not in defaults:
        raise KeyError(key)
    return groups.get(key) or defaults[key]


def group_principal(name: str, domain: str) -> str:
    """Returns the IAM principal of a Stage 0 group value.

    Mirrors `local.principals` in `0-bootstrap/main.tf`: a value with a
    principal type is kept, any other value is a group in the domain.

    Args:
        name: Group value, such as `gcp-devops` or `user:x@example.com`.
        domain: Organization domain.
    """
    if PRINCIPAL_TYPE_RE.match(name):
        return name
    return f"group:{name}@{domain}"


def principal(kind: str, name: str) -> str:
    """Returns the IAM member of a principal type and name.

    Args:
        kind: Principal type, such as `USER` or `SERVICE_ACCOUNT`.
        name: Email, or the domain of a `DOMAIN` principal.

    Returns:
        The member, such as `serviceAccount:x@example.com`.
    """
    return f"{kind}:{name}"


def principal_email(principal: str) -> str:
    """Returns the email of a principal, without the principal type.

    Args:
        principal: A typed principal such as `group:x@example.com`.
    """
    return principal.split(":", 1)[1]


def workload_folder_name(prefix: str) -> str:
    """Returns the display name of the Assured Workloads folder.

    Mirrors `display_name = "StellarEngine-${var.prefix}"` in
    `0-bootstrap/organization.tf`.

    Args:
        prefix: Deployment prefix.
    """
    return f"StellarEngine-{prefix}"


def _tenant_env_key(env, tenant):
    # `local.tenant_envs` in `1-resman/branch-tenants.tf` keys each pair as
    # "${e}-${t}", and every name built from it goes through lower().
    return f"{env}-{tenant}".lower()


def tenant_project_ids(
    prefix: str, envs: Iterable[str], tenant: str
) -> list[str]:
    """Returns the project IDs Stage 1 creates for a tenant.

    Mirrors `tenant-self-iac-projects` and `tenant-self-main-projects` in
    `1-resman/branch-tenants.tf`: one pair per env, named
    `<prefix>-<env>-<tenant>-iac-core-0` and `<prefix>-<env>-<tenant>-main-0`
    with the env and tenant lowercased.

    Args:
        prefix: Deployment prefix.
        envs: Stage 1 env keys, such as `Prod`.
        tenant: Tenant key.

    Returns:
        The IDs in env order, iac-core before main.
    """
    return [
        f"{prefix}-{_tenant_env_key(env, tenant)}-{suffix}"
        for env in envs
        for suffix in ("iac-core-0", "main-0")
    ]


def tenant_project_imports(
    prefix: str, envs: Iterable[str], tenant: str
) -> list[tuple[str, str]]:
    """Returns the import address and ID of each project of a tenant.

    Mirrors the same module calls as `tenant_project_ids`. The address key
    `<env>-<tenant>` keeps the case of the env key, as `local.tenant_envs`
    in `1-resman/branch-tenants.tf` does, while the ID lowercases it.

    Args:
        prefix: Deployment prefix.
        envs: Stage 1 env keys, such as `Prod`.
        tenant: Tenant key.

    Returns:
        `(address, project ID)` pairs in `tenant_project_ids` order.
    """
    found = []
    for env in envs:
        ids = tenant_project_ids(prefix, [env], tenant)
        for module, project_id in zip(TENANT_PROJECT_MODULES, ids, strict=True):
            address = f'module.{module}["{env}-{tenant}"]'
            found.append((f"{address}.{PROJECT_ADDRESS_SUFFIX}", project_id))
    return found


def tenant_service_account_ids(
    prefix: str, envs: Iterable[str], tenant: str
) -> list[str]:
    """Returns the service account IDs Stage 1 creates for a tenant.

    Mirrors `tenant-core-sa` (`tn-<env>-<tenant>-prod-0`) and
    `tenant-self-iac-sa` (`<env>-<tenant>-iac-0`) in
    `1-resman/branch-tenants.tf`, both prefixed and lowercased. Service
    account IDs share the 30-character limit of project IDs.

    Args:
        prefix: Deployment prefix.
        envs: Stage 1 env keys, such as `Prod`.
        tenant: Tenant key.

    Returns:
        The IDs in env order.
    """
    return [
        name
        for env in envs
        for name in (
            f"{prefix}-tn-{_tenant_env_key(env, tenant)}-prod-0",
            f"{prefix}-{_tenant_env_key(env, tenant)}-iac-0",
        )
    ]
