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

"""Interface between preflight checks and Google Cloud.

Checks depend only on the `CloudApi` protocol defined here. The live
implementation in `live.py` calls Google Cloud client libraries, and tests
supply an in-memory fake, so no unit test touches the network.
"""

import dataclasses
import enum
from typing import Protocol


class CloudError(Exception):
    """Raised when a Google Cloud call fails."""


class AccessDeniedError(CloudError):
    """Raised when the caller lacks permission to read a resource."""


class ApiDisabledError(AccessDeniedError):
    """Raised when an API is disabled in the project used for quota.

    Attributes:
        service: Service name, for example `cloudbilling.googleapis.com`.
        project: Project, often a project number, that needs the service.
    """

    def __init__(self, service, project):
        """Initializes the error with the service and its consumer project."""
        self.service = service
        self.project = project
        super().__init__(
            f"The {service} API is disabled in project {project}, which "
            "these credentials use for quota. Run `gcloud services enable "
            f"{service} --project={project}`."
        )


class CredentialsError(Exception):
    """Raised when Application Default Credentials are missing or invalid."""


class PrincipalKind(enum.StrEnum):
    """Kinds of principal that Application Default Credentials can carry."""

    USER = "user"
    SERVICE_ACCOUNT = "serviceAccount"
    UNKNOWN = "unknown"


@dataclasses.dataclass(frozen=True)
class Principal:
    """Identity behind a set of credentials.

    Attributes:
        email: Email address, or None when it cannot be determined.
        kind: Whether the identity is a user or a service account.
    """

    email: str | None
    kind: PrincipalKind


@dataclasses.dataclass(frozen=True)
class Organization:
    """Subset of a Resource Manager organization.

    Attributes:
        org_id: Numeric organization ID as a string.
        domain: Primary domain, which is the organization display name.
        customer_id: Cloud Identity directory customer ID.
    """

    org_id: str
    domain: str
    customer_id: str


@dataclasses.dataclass(frozen=True)
class BillingAccount:
    """Subset of a Cloud Billing account.

    Attributes:
        account_id: Billing account ID in `XXXXXX-XXXXXX-XXXXXX` form.
        is_open: Whether the account can pay for resources.
    """

    account_id: str
    is_open: bool


@dataclasses.dataclass(frozen=True)
class ProjectBilling:
    """Billing link of a project.

    Attributes:
        account_id: Linked billing account ID, or None when unlinked.
        enabled: Whether billing is enabled on the project.
    """

    account_id: str | None
    enabled: bool


@dataclasses.dataclass(frozen=True)
class IamBinding:
    """One role binding from an IAM policy.

    Attributes:
        role: Role name, for example `roles/owner`.
        members: Principals bound to the role.
    """

    role: str
    members: tuple[str, ...]


class CloudApi(Protocol):
    """Read-only Google Cloud operations used by preflight checks.

    Methods raise `AccessDeniedError` when the caller lacks permission,
    `CloudError` for any other failed call, and return None or False when a
    resource does not exist.
    """

    def adc_principal(self) -> Principal:
        """Returns the identity behind Application Default Credentials."""
        ...

    def search_organizations(self) -> list[Organization]:
        """Returns the organizations visible to the caller."""
        ...

    def get_organization(self, org_id: str) -> Organization | None:
        """Returns an organization by numeric ID."""
        ...

    def role_permissions(self, role: str) -> list[str]:
        """Returns the permissions included in a predefined or basic role."""
        ...

    def testable_permissions(self, full_resource_name: str) -> set[str]:
        """Returns the permissions that can be tested on a resource."""
        ...

    def granted_org_permissions(
        self, org_id: str, permissions: list[str]
    ) -> set[str]:
        """Returns the subset of permissions the caller has on the org."""
        ...

    def org_iam_bindings(self, org_id: str) -> list[IamBinding]:
        """Returns the organization IAM policy bindings."""
        ...

    def get_billing_account(self, account_id: str) -> BillingAccount | None:
        """Returns a billing account by ID."""
        ...

    def list_billing_accounts(self) -> list[BillingAccount]:
        """Returns the billing accounts visible to the caller."""
        ...

    def granted_billing_permissions(
        self, account_id: str, permissions: list[str]
    ) -> set[str]:
        """Returns the subset of permissions the caller has on the account."""
        ...

    def project_billing(self, project_id: str) -> ProjectBilling:
        """Returns the billing link of a project."""
        ...

    def project_state(self, project_id: str) -> str | None:
        """Returns the lifecycle state of a project, or None if missing."""
        ...

    def enabled_services(self, project_id: str) -> set[str]:
        """Returns the services enabled on a project."""
        ...

    def visible_project_state(self, project_id: str) -> str | None:
        """Returns the state of a visible project with this exact ID.

        Returns `ACTIVE`, `DELETE_REQUESTED` for a soft-deleted project, or
        None. Resource Manager answers 403 for both missing and inaccessible
        projects, so a project outside the caller's view cannot be detected.
        """
        ...

    def bucket_exists(self, name: str) -> bool:
        """Returns whether a Cloud Storage bucket exists anywhere."""
        ...

    def find_folders(self, org_id: str, display_name: str) -> list[str]:
        """Returns active folder names in an org with an exact display name."""
        ...

    def custom_role_exists(self, org_id: str, role_id: str) -> bool:
        """Returns whether an organization custom role exists."""
        ...

    def custom_constraint_exists(self, org_id: str, name: str) -> bool:
        """Returns whether an organization custom constraint exists."""
        ...

    def list_org_policies(self, org_id: str) -> list[str]:
        """Returns the constraints of the policies set on an organization.

        Returns:
            Constraint names without the resource path, such as
            `iam.allowedPolicyMemberDomains`, sorted.
        """
        ...

    def log_sink_exists(self, org_id: str, name: str) -> bool:
        """Returns whether an organization log sink exists."""
        ...

    def group_exists(self, email: str) -> bool:
        """Returns whether a Cloud Identity group exists."""
        ...
