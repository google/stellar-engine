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

"""Values that follow from the answers the way the stage code derives them.

Each function mirrors a Terraform expression and names it, so a change in
the stage code has one place to follow here.
"""

from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import models

ORGANIZATION_ADMINS = "gcp-organization-admins"
DEVOPS = "gcp-devops"
# The `deletion_policy` of `modules/project` that leaves the project in
# place when Terraform destroys the module.
ABANDON = "ABANDON"


def kms_protection_level(answers: models.Answers) -> str:
    """Returns the CMEK protection level Stage 0 uses.

    See `naming.kms_protection_level`.

    Args:
        answers: The environment answers.
    """
    return naming.kms_protection_level(
        answers.compliance.regime, answers.kms_protection_level
    )


def compliance_location(answers: models.Answers) -> str:
    """Returns the Assured Workloads location, defaulting to the region.

    Args:
        answers: The environment answers.
    """
    return answers.compliance.location or answers.region


def group_name(answers: models.Answers, repo: repo_lib.Repo, key: str) -> str:
    """Returns a Stage 0 group value: the renamed one or the repo default.

    Args:
        answers: The environment answers.
        repo: Repository that defines the default group names.
        key: Group key such as `gcp-devops`.

    Raises:
        KeyError: If the key is not a field of the Stage 0 `groups` type.
    """
    return naming.group_name(answers.groups, repo.default_groups(), key)


def group_principal(
    answers: models.Answers, repo: repo_lib.Repo, key: str
) -> str:
    """Returns the IAM principal of a group the way Stage 0 builds it.

    Mirrors `local.principals` in `0-bootstrap/main.tf`.

    Args:
        answers: The environment answers.
        repo: Repository that defines the default group names.
        key: Group key such as `gcp-devops`.

    Raises:
        KeyError: If the key is not a field of the Stage 0 `groups` type.
    """
    return naming.group_principal(
        group_name(answers, repo, key), answers.organization.domain
    )


def group_email(answers: models.Answers, repo: repo_lib.Repo, key: str) -> str:
    """Returns the email of a group, without the principal type.

    Args:
        answers: The environment answers.
        repo: Repository that defines the default group names.
        key: Group key such as `gcp-devops`.

    Raises:
        KeyError: If the key is not a field of the Stage 0 `groups` type.
    """
    return naming.principal_email(group_principal(answers, repo, key))


def env_admin(answers: models.Answers, repo: repo_lib.Repo, env: str) -> str:
    """Returns the admin email of a Stage 1 environment folder.

    The `1-resman` sample defaults every env to the organization admins
    group email.

    Args:
        answers: The environment answers.
        repo: Repository that defines the default group names.
        env: Env key, such as `Prod`.

    Raises:
        KeyError: If the env is not in the answers.
    """
    folder = answers.resman.envs[env]
    return folder.admin or group_email(answers, repo, ORGANIZATION_ADMINS)


def tenant_admin(
    answers: models.Answers, repo: repo_lib.Repo, tenant: str
) -> str:
    """Returns the admin principal of a Stage 1 tenant.

    The `1-resman` sample defaults it to the `gcp-devops` group principal.

    Args:
        answers: The environment answers.
        repo: Repository that defines the default group names.
        tenant: Tenant key, such as `ten1`.

    Raises:
        KeyError: If the tenant is not in the answers.
    """
    info = answers.resman.tenants[tenant]
    return info.admin_principal or group_principal(answers, repo, DEVOPS)


def tenant_locations(answers: models.Answers, tenant: str) -> dict[str, str]:
    """Returns the GCS and KMS locations of a tenant, defaulting to region.

    Args:
        answers: The environment answers.
        tenant: Tenant key, such as `ten1`.

    Raises:
        KeyError: If the tenant is not in the answers.
    """
    locations = answers.resman.tenants[tenant].locations
    if locations is None:
        return {"gcs": answers.region, "kms": answers.region}
    return {"gcs": locations.gcs, "kms": locations.kms}


def stage0_project_id(
    answers: models.Answers, project: repo_lib.Stage0Project
) -> str:
    """Returns the ID of a Stage 0 project, `<prefix>-prod-<name>`.

    Args:
        answers: The environment answers.
        project: A Stage 0 project from `Repo.stage0_projects`.
    """
    return naming.stage0_project_id(answers.prefix, project.name)


def stage0_projects(
    answers: models.Answers, repo: repo_lib.Repo
) -> list[repo_lib.Stage0Project]:
    """Returns the Stage 0 projects that Stage 0 creates for these answers.

    The billing export project only exists when Stage 0 manages billing IAM
    on an organization-level account; see `repo.stage0_project_created`.

    Args:
        answers: The environment answers.
        repo: The engine checkout.
    """
    return repo.created_stage0_projects(
        no_iam=answers.billing.no_iam,
        is_org_level=answers.billing.is_org_level,
    )


def tenant_project_ids(answers: models.Answers) -> dict[str, list[str]]:
    """Returns the project IDs Stage 1 creates for each tenant.

    See `naming.tenant_project_ids`.

    Args:
        answers: The environment answers.

    Returns:
        Tenant key to project IDs, in env order, iac-core before main.
    """
    return {
        tenant: naming.tenant_project_ids(
            answers.prefix, answers.resman.envs, tenant
        )
        for tenant in answers.resman.tenants
    }


def tenant_project_imports(answers: models.Answers) -> list[tuple[str, str]]:
    """Returns the import address and ID of every tenant project.

    See `naming.tenant_project_imports`.

    Args:
        answers: The environment answers.

    Returns:
        `(address, project ID)` pairs, tenant by tenant, in env order.
    """
    return [
        pair
        for tenant in answers.resman.tenants
        for pair in naming.tenant_project_imports(
            answers.prefix, answers.resman.envs, tenant
        )
    ]


def tenant_service_account_ids(
    answers: models.Answers,
) -> dict[str, list[str]]:
    """Returns the service account IDs Stage 1 creates for each tenant.

    See `naming.tenant_service_account_ids`.

    Args:
        answers: The environment answers.

    Returns:
        Tenant key to service account IDs, in env order.
    """
    return {
        tenant: naming.tenant_service_account_ids(
            answers.prefix, answers.resman.envs, tenant
        )
        for tenant in answers.resman.tenants
    }


def kept_stage0_projects(
    answers: models.Answers, repo: repo_lib.Repo
) -> list[repo_lib.Stage0Project]:
    """Returns the imported Stage 0 projects that Stage 0 destroy keeps.

    A project counts when `keep_imported_projects` is true, Stage 0
    creates it for these answers, and `imports.0-bootstrap` adopts its
    `google_project` resource.

    Args:
        answers: The environment answers.
        repo: The engine checkout.
    """
    if not answers.keep_imported_projects:
        return []
    imported = answers.imports.get(paths.BOOTSTRAP, {})
    return [
        project
        for project in stage0_projects(answers, repo)
        if project.address in imported
    ]


def project_deletion_policies(
    answers: models.Answers, repo: repo_lib.Repo
) -> dict[str, str]:
    """Returns the Stage 0 `project_deletion_policies` value to write.

    Args:
        answers: The environment answers.
        repo: The engine checkout.

    Returns:
        Variable key to ABANDON for each kept project, such as
        `{"automation": "ABANDON"}`. Empty when no project is kept or the
        Stage 0 version declares no `project_deletion_policies` variable.
    """
    keys = repo.project_deletion_policy_keys()
    return {
        keys[project.module]: ABANDON
        for project in kept_stage0_projects(answers, repo)
        if project.module in keys
    }


def stage0_deletion_policies(
    answers: models.Answers, repo: repo_lib.Repo
) -> dict[str, str]:
    """Returns the deletion policy of each Stage 0 project for these answers.

    Args:
        answers: The environment answers.
        repo: The engine checkout.

    Returns:
        Project ID to deletion policy, such as `{"abc-prod-iac-core-0":
        "ABANDON"}`, for the projects Stage 0 creates.
    """
    keys = repo.project_deletion_policy_keys()
    defaults = repo.stage0_deletion_policies()
    kept = {
        project.module
        for project in kept_stage0_projects(answers, repo)
        if project.module in keys
    }
    return {
        stage0_project_id(answers, project): (
            ABANDON if project.module in kept else defaults[project.module]
        )
        for project in stage0_projects(answers, repo)
    }
