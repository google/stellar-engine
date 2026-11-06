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

"""Interface between the CLI and Google Cloud.

Preflight checks and deploy step checks depend only on the read-only
`CloudApi` protocol defined here; deploy steps that change Google Cloud
also take the `CloudWriter` protocol. The live implementation in `live.py`
calls Google Cloud client libraries, and tests supply an in-memory fake,
so no unit test touches the network.
"""

from collections.abc import Sequence
import dataclasses
import enum
from typing import Protocol

from stellar_engine import iam_diff


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


class ConflictError(CloudError):
    """Raised when a write lost a race with another change.

    The resource changed after the read, so the etag the write sent is
    stale. Read again, reapply the change and retry.
    """


class CredentialsError(Exception):
    """Raised when Application Default Credentials are missing or invalid."""


# Every error a Google Cloud call raises, for `except api.CLOUD_ERRORS`.
CLOUD_ERRORS = (CloudError, CredentialsError)


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
class AdcInfo:
    """Application Default Credentials as read locally, without a call.

    Attributes:
        kind: Whether the credentials belong to a user or a service
            account.
        quota_project: Project the credentials bill API quota to, or None.
    """

    kind: PrincipalKind
    quota_project: str | None


@dataclasses.dataclass(frozen=True)
class ServiceRestriction:
    """The effective `gcp.restrictServiceUsage` policy on a resource.

    Attributes:
        allow_all: Whether a rule allows every service.
        deny_all: Whether a rule denies every service.
        allowed: Services that the rules allow, without `is:` prefixes.
        denied: Services that the rules deny, without `is:` prefixes.
    """

    allow_all: bool = False
    deny_all: bool = False
    allowed: tuple[str, ...] = ()
    denied: tuple[str, ...] = ()

    def allows(self, service: str) -> bool:
        """Returns whether projects under the resource may use a service.

        A deny wins over an allow. Without any allow list the constraint
        allows every service, as its default does.

        Args:
            service: Service name, such as `bigquery.googleapis.com`.
        """
        service = service.removeprefix("is:")
        if self.deny_all or service in self.denied:
            return False
        return self.allow_all or not self.allowed or service in self.allowed


@dataclasses.dataclass(frozen=True)
class WorkloadInfo:
    """Subset of an Assured Workloads workload.

    Attributes:
        name: Workload name,
            `organizations/<org>/locations/<location>/workloads/<id>`.
        regime: Compliance regime, such as `IL5`.
        folder: Consumer folder as `folders/<id>`, or None.
        compliant_but_disallowed: Services the regime supports that the
            workload's `gcp.restrictServiceUsage` policy still blocks.
    """

    name: str
    regime: str
    folder: str | None
    compliant_but_disallowed: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class ObjectData:
    """Content of a Cloud Storage object.

    Attributes:
        data: Object bytes.
        generation: Object generation that the bytes belong to.
    """

    data: bytes
    generation: int


@dataclasses.dataclass(frozen=True)
class ServiceAccount:
    """Subset of an IAM service account.

    Attributes:
        email: Service account email.
        disabled: Whether the account is disabled.
    """

    email: str
    disabled: bool


class CloudApi(Protocol):
    """Read-only Google Cloud operations.

    Preflight checks and the `check()` of every deploy step use only these
    calls, so neither changes anything. Methods raise `AccessDeniedError`
    when the caller lacks permission, `CloudError` for any other failed
    call, and return None or False when a resource does not exist.
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

    def get_org_iam_policy(self, org_id: str) -> iam_diff.Policy:
        """Returns the organization IAM policy, conditions included."""
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

    def adc_info(self) -> AdcInfo:
        """Returns the kind and quota project of the local credentials."""
        ...

    def effective_service_restriction(
        self, resource: str
    ) -> ServiceRestriction:
        """Returns the effective `gcp.restrictServiceUsage` on a resource.

        Args:
            resource: Resource such as `folders/123456789012`.
        """
        ...

    def assured_workload(self, name: str) -> WorkloadInfo | None:
        """Returns an Assured Workloads workload by name.

        Args:
            name: Workload name,
                `organizations/<org>/locations/<location>/workloads/<id>`.
        """
        ...

    def read_object(
        self, bucket: str, name: str, *, impersonate: str | None = None
    ) -> ObjectData | None:
        """Returns a Cloud Storage object, or None when it does not exist.

        Args:
            bucket: Bucket name.
            name: Object name.
            impersonate: Service account email to read as, or None to read
                with Application Default Credentials.
        """
        ...

    def billing_account_iam(self, account_id: str) -> iam_diff.Policy:
        """Returns the IAM policy of a billing account."""
        ...

    def service_accounts(self, project_id: str) -> list[ServiceAccount]:
        """Returns the service accounts of a project."""
        ...

    def gcs_service_agent(self, project_id: str) -> str:
        """Returns the Cloud Storage service agent email of a project.

        Cloud Storage creates the agent on this first read, which some
        regimes need before a CMEK bucket can be created.
        """
        ...


class CloudWriter(Protocol):
    """Google Cloud changes that deploy steps make outside Terraform.

    Only `run()` of a deploy step calls these, after the operator agreed.
    Methods raise `AccessDeniedError` when the caller lacks permission,
    `ConflictError` when a concurrent change made an etag stale, and
    `CloudError` for any other failed call.
    """

    def set_org_iam_policy(
        self,
        org_id: str,
        policy: iam_diff.Policy,
        *,
        etag: str,
        update_mask: Sequence[str],
    ) -> iam_diff.Policy:
        """Replaces fields of the organization IAM policy.

        Args:
            org_id: Organization ID.
            policy: The policy to write; it is sent as version 3.
            etag: Etag of the read the policy is based on. It must not be
                empty, so a concurrent change fails the write.
            update_mask: Policy fields to replace, such as
                `("bindings", "etag", "auditConfigs")`.

        Returns:
            The policy as written.
        """
        ...

    def enable_services(self, project_id: str, services: Sequence[str]) -> None:
        """Enables services on a project and waits until they are enabled.

        Mirrors `0-bootstrap/enableServices.sh`.
        """
        ...

    def restrict_allowed_resources(self, name: str) -> None:
        """Allows the compliant services of a workload on its folder.

        Calls `restrictAllowedResources` with `APPEND_COMPLIANT_RESOURCES`,
        which adds the services the regime supports to the existing allow
        list, replacing `scripts/allow_bq.sh`.

        Args:
            name: Workload name.
        """
        ...

    def add_billing_account_binding(
        self, account_id: str, role: str, member: str
    ) -> None:
        """Grants a role on a billing account, keeping the other grants.

        Mirrors `gcloud billing accounts add-iam-policy-binding`.
        """
        ...

    def generate_service_identity(
        self, project_id: str, service: str
    ) -> str | None:
        """Creates the service agent of a service in a project.

        Mirrors `gcloud beta services identity create`.

        Returns:
            The agent email, or None when the operation did not report it.
        """
        ...
