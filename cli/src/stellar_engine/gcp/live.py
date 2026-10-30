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

"""Live `CloudApi` and `CloudWriter` backed by Google Cloud client libraries.

Every call uses Application Default Credentials. The `CloudApi` methods
only read; the `CloudWriter` methods change Google Cloud and run only from
a deploy step the operator agreed to. Clients are created lazily so that a
check which never runs never needs its API. Every public method translates
Google API errors into the facade's error types.
"""

from concurrent import futures
import functools
import re

from google.api_core import exceptions as api_exceptions
import google.auth
from google.auth import exceptions as auth_exceptions
from google.auth import impersonated_credentials
from google.auth.transport import requests as auth_requests
from google.cloud import billing_v1
from google.cloud import iam_admin_v1
from google.cloud import orgpolicy_v2
from google.cloud import resourcemanager_v3
from google.cloud import service_usage_v1
from google.cloud import storage
from google.iam.v1 import policy_pb2
from google.oauth2 import credentials as oauth2_credentials
from google.protobuf import field_mask_pb2
from google.protobuf import json_format
import requests

from stellar_engine import iam_diff
from stellar_engine.gcp import api

# The email scopes let tokeninfo report the user behind user credentials;
# without them, refreshed user tokens carry only cloud-platform.
_SCOPES = (
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
)
_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_CLOUD_IDENTITY_URL = "https://cloudidentity.googleapis.com/v1/groups:lookup"
_LOGGING_URL = "https://logging.googleapis.com/v2"
_SERVICE_USAGE_BETA_URL = "https://serviceusage.googleapis.com/v1beta1"
# Assured Workloads only serves a workload from its regional endpoint.
_WORKLOADS_URL = "https://{location}-assuredworkloads.googleapis.com/v1"
_WORKLOAD_NAME_RE = re.compile(
    r"^organizations/[^/]+/locations/(?P<location>[^/]+)/workloads/[^/]+$"
)
_CONSUMER_FOLDER = "CONSUMER_FOLDER"
_APPEND_COMPLIANT = "APPEND_COMPLIANT_RESOURCES"
_RESTRICT_SERVICE_USAGE = "gcp.restrictServiceUsage"
_TEST_PERMISSIONS_BATCH = 100
# The most services one batchEnable call accepts.
_ENABLE_BATCH = 20
_OPERATION_TIMEOUT_SECONDS = 600
_REST_TIMEOUT_SECONDS = 30
_MAX_WORKERS = 8
# Conditional bindings need version 3 on both read and write.
_POLICY_VERSION = 3
_HTTP_NOT_FOUND = 404
_HTTP_FORBIDDEN = (401, 403)
_HTTP_CONFLICT = 409


def _denied(error):
    """Converts a Google API error into a short facade error."""
    if error.reason == "SERVICE_DISABLED":
        metadata = error.metadata or {}
        return api.ApiDisabledError(
            metadata.get("service", "unknown"),
            metadata.get("consumer", "unknown").removeprefix("projects/"),
        )
    message = (getattr(error, "message", None) or str(error)).splitlines()[0]
    # api_core maps HTTP 403 and 401 to Forbidden and Unauthorized, the
    # parents of the gRPC PermissionDenied and Unauthenticated classes, so
    # a REST transport denial only matches the parent classes.
    if isinstance(
        error, api_exceptions.Forbidden | api_exceptions.Unauthorized
    ):
        return api.AccessDeniedError(message)
    # An IAM write with a stale etag fails with ABORTED.
    if isinstance(error, api_exceptions.Aborted):
        return api.ConflictError(message)
    return api.CloudError(message)


def _rest_denied(body, fallback):
    """Converts a REST error body into a short facade error."""
    error = (body or {}).get("error", {})
    for detail in error.get("details", []):
        if detail.get("reason") == "SERVICE_DISABLED":
            metadata = detail.get("metadata", {})
            return api.ApiDisabledError(
                metadata.get("service", "unknown"),
                metadata.get("consumer", "unknown").removeprefix("projects/"),
            )
    return api.AccessDeniedError(error.get("message") or fallback)


def _translated(method):
    """Decorates a facade method to translate Google API errors."""

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except api_exceptions.GoogleAPICallError as error:
            raise _denied(error) from error
        except requests.RequestException as error:
            raise api.CloudError(str(error)) from error

    return wrapper


def _batches(items, size):
    return [items[i : i + size] for i in range(0, len(items), size)]


def _to_policy(message):
    """Converts a `google.iam.v1` Policy message into an `iam_diff.Policy`."""
    return iam_diff.Policy.from_json(json_format.MessageToDict(message))


def _to_message(policy, etag):
    """Builds the version 3 Policy message that a write sends."""
    data = {**policy.to_json(), "version": _POLICY_VERSION, "etag": etag}
    return json_format.ParseDict(data, policy_pb2.Policy())


def _field_path(name):
    """Returns the protobuf path of a JSON field such as `auditConfigs`."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _workload_url(name):
    """Returns the regional REST URL of an Assured Workloads workload.

    Raises:
        ValueError: If the name is not a workload name.
    """
    match = _WORKLOAD_NAME_RE.match(name)
    if match is None:
        raise ValueError(f"{name} is not an Assured Workloads workload name.")
    return f"{_WORKLOADS_URL.format(location=match['location'])}/{name}"


def _workload_info(body):
    """Converts a workload resource of the REST API into a WorkloadInfo."""
    folder = next(
        (
            f"folders/{item['resourceId']}"
            for item in body.get("resources", [])
            if item.get("resourceType") == _CONSUMER_FOLDER
            and item.get("resourceId")
        ),
        None,
    )
    return api.WorkloadInfo(
        name=body["name"],
        regime=body.get("complianceRegime", ""),
        folder=folder,
        compliant_but_disallowed=tuple(
            body.get("compliantButDisallowedServices", [])
        ),
    )


def _restriction(policy):
    """Merges the rules of an effective orgpolicy v2 Policy."""
    rules = list(policy.spec.rules) if policy.spec else []
    allowed = {v for rule in rules for v in rule.values.allowed_values}
    denied = {v for rule in rules for v in rule.values.denied_values}
    return api.ServiceRestriction(
        allow_all=any(rule.allow_all for rule in rules),
        deny_all=any(rule.deny_all for rule in rules),
        allowed=tuple(sorted(v.removeprefix("is:") for v in allowed)),
        denied=tuple(sorted(v.removeprefix("is:") for v in denied)),
    )


class LiveCloudApi:
    """Calls Google Cloud with Application Default Credentials."""

    @functools.cached_property
    def _credentials(self):
        try:
            credentials, _ = google.auth.default(scopes=_SCOPES)
        except auth_exceptions.DefaultCredentialsError as error:
            raise api.CredentialsError(str(error)) from error
        return credentials

    @functools.cached_property
    def _session(self):
        return auth_requests.AuthorizedSession(self._credentials)

    @functools.cached_property
    def _organizations(self):
        return resourcemanager_v3.OrganizationsClient(
            credentials=self._credentials
        )

    @functools.cached_property
    def _projects(self):
        return resourcemanager_v3.ProjectsClient(credentials=self._credentials)

    @functools.cached_property
    def _folders(self):
        return resourcemanager_v3.FoldersClient(credentials=self._credentials)

    @functools.cached_property
    def _iam(self):
        return iam_admin_v1.IAMClient(credentials=self._credentials)

    @functools.cached_property
    def _billing(self):
        return billing_v1.CloudBillingClient(credentials=self._credentials)

    @functools.cached_property
    def _service_usage(self):
        return service_usage_v1.ServiceUsageClient(
            credentials=self._credentials
        )

    @functools.cached_property
    def _storage(self):
        return storage.Client(credentials=self._credentials, project="_")

    @functools.cached_property
    def _org_policy(self):
        return orgpolicy_v2.OrgPolicyClient(credentials=self._credentials)

    def _rest_call(self, method, url, *, params=None, body=None):
        """Issues a REST call and maps HTTP errors to the facade conventions.

        Args:
            method: HTTP method, such as `GET` or `POST`.
            url: Request URL.
            params: Optional query parameters.
            body: Optional JSON request body.

        Returns:
            The decoded JSON body, an empty dict for an empty body, or None
            for HTTP 404.

        Raises:
            AccessDeniedError: For HTTP 401 or 403.
            ConflictError: For HTTP 409.
            CloudError: For any other HTTP error.
        """
        response = self._session.request(
            method, url, params=params, json=body, timeout=_REST_TIMEOUT_SECONDS
        )
        if response.status_code == _HTTP_NOT_FOUND:
            return None
        if response.status_code in _HTTP_FORBIDDEN:
            try:
                error_body = response.json()
            except ValueError:
                error_body = None
            raise _rest_denied(error_body, f"HTTP {response.status_code}")
        detail = (
            f"HTTP {response.status_code} from {url}: {response.text[:200]}"
        )
        if response.status_code == _HTTP_CONFLICT:
            raise api.ConflictError(detail)
        if not response.ok:
            raise api.CloudError(detail)
        return response.json() if response.content else {}

    def adc_principal(self):
        """See `CloudApi.adc_principal`."""
        credentials = self._credentials
        email = getattr(credentials, "service_account_email", None)
        if email and email != "default":
            return api.Principal(email, api.PrincipalKind.SERVICE_ACCOUNT)
        try:
            credentials.refresh(auth_requests.Request())
        except auth_exceptions.RefreshError as error:
            raise api.CredentialsError(str(error)) from error
        if email == "default":
            return api.Principal(
                credentials.service_account_email,
                api.PrincipalKind.SERVICE_ACCOUNT,
            )
        try:
            info = self._rest_call(
                "GET",
                _TOKENINFO_URL,
                params={"access_token": credentials.token},
            )
        except api.CloudError, requests.RequestException:
            info = None
        if info and info.get("email"):
            return api.Principal(info["email"], api.PrincipalKind.USER)
        return api.Principal(None, api.PrincipalKind.UNKNOWN)

    @staticmethod
    def _to_organization(org):
        return api.Organization(
            org_id=org.name.removeprefix("organizations/"),
            domain=org.display_name,
            customer_id=org.directory_customer_id,
        )

    @_translated
    def search_organizations(self):
        """See `CloudApi.search_organizations`."""
        return [
            self._to_organization(org)
            for org in self._organizations.search_organizations()
        ]

    @_translated
    def get_organization(self, org_id):
        """See `CloudApi.get_organization`."""
        try:
            org = self._organizations.get_organization(
                name=f"organizations/{org_id}"
            )
        except api_exceptions.NotFound:
            return None
        return self._to_organization(org)

    @functools.cache  # noqa: B019 - the facade lives for one CLI run.
    @_translated
    def role_permissions(self, role):
        """See `CloudApi.role_permissions`."""
        role_info = self._iam.get_role(request={"name": role})
        return list(role_info.included_permissions)

    @functools.cache  # noqa: B019 - the facade lives for one CLI run.
    @_translated
    def testable_permissions(self, full_resource_name):
        """See `CloudApi.testable_permissions`."""
        pager = self._iam.query_testable_permissions(
            request={
                "full_resource_name": full_resource_name,
                "page_size": 1000,
            }
        )
        return {permission.name for permission in pager}

    @staticmethod
    def _granted(test, permissions):
        batches = _batches(sorted(permissions), _TEST_PERMISSIONS_BATCH)
        granted = set()
        with futures.ThreadPoolExecutor(_MAX_WORKERS) as pool:
            for result in pool.map(test, batches):
                granted.update(result)
        return granted

    @_translated
    def granted_org_permissions(self, org_id, permissions):
        """See `CloudApi.granted_org_permissions`."""
        # Build the client before the pool starts, so threads share one.
        client = self._organizations

        def test(batch):
            response = client.test_iam_permissions(
                resource=f"organizations/{org_id}", permissions=batch
            )
            return response.permissions

        return self._granted(test, permissions)

    @_translated
    def get_org_iam_policy(self, org_id):
        """See `CloudApi.get_org_iam_policy`."""
        policy = self._organizations.get_iam_policy(
            request={
                "resource": f"organizations/{org_id}",
                "options": {"requested_policy_version": _POLICY_VERSION},
            }
        )
        return _to_policy(policy)

    @_translated
    def get_billing_account(self, account_id):
        """See `CloudApi.get_billing_account`."""
        try:
            account = self._billing.get_billing_account(
                name=f"billingAccounts/{account_id}"
            )
        except api_exceptions.NotFound:
            return None
        return api.BillingAccount(account_id, account.open_)

    @_translated
    def list_billing_accounts(self):
        """See `CloudApi.list_billing_accounts`."""
        return [
            api.BillingAccount(
                account.name.removeprefix("billingAccounts/"), account.open_
            )
            for account in self._billing.list_billing_accounts()
        ]

    @_translated
    def granted_billing_permissions(self, account_id, permissions):
        """See `CloudApi.granted_billing_permissions`."""
        client = self._billing

        def test(batch):
            response = client.test_iam_permissions(
                resource=f"billingAccounts/{account_id}", permissions=batch
            )
            return response.permissions

        return self._granted(test, permissions)

    @_translated
    def project_billing(self, project_id):
        """See `CloudApi.project_billing`."""
        info = self._billing.get_project_billing_info(
            name=f"projects/{project_id}"
        )
        account = info.billing_account_name.removeprefix("billingAccounts/")
        return api.ProjectBilling(account or None, info.billing_enabled)

    @_translated
    def project_state(self, project_id):
        """See `CloudApi.project_state`."""
        try:
            project = self._projects.get_project(name=f"projects/{project_id}")
        except api_exceptions.NotFound:
            return None
        return project.state.name

    @_translated
    def enabled_services(self, project_id):
        """See `CloudApi.enabled_services`."""
        pager = self._service_usage.list_services(
            request={
                "parent": f"projects/{project_id}",
                "filter": "state:ENABLED",
                "page_size": 200,
            }
        )
        return {service.config.name for service in pager}

    @_translated
    def visible_project_state(self, project_id):
        """See `CloudApi.visible_project_state`."""
        # Query soft-deleted projects explicitly, so the result does not
        # depend on which states a plain ID search includes.
        for query in (
            f"id:{project_id}",
            f"id:{project_id} state:DELETE_REQUESTED",
        ):
            for project in self._projects.search_projects(query=query):
                if project.project_id == project_id:
                    return project.state.name
        return None

    @_translated
    def bucket_exists(self, name):
        """See `CloudApi.bucket_exists`.

        A bucket that exists but denies access still counts as existing,
        because its name is taken.
        """
        try:
            return self._storage.lookup_bucket(name) is not None
        except api_exceptions.Forbidden:
            return True

    @_translated
    def find_folders(self, org_id, display_name):
        """See `CloudApi.find_folders`."""
        # A deleted folder keeps its display name for 30 days but does not
        # block a new folder with the same name, so only active ones count.
        pager = self._folders.search_folders(
            query=(
                f'displayName="{display_name}" AND '
                f"parent=organizations/{org_id} AND state=ACTIVE"
            )
        )
        return [folder.name for folder in pager]

    @_translated
    def custom_role_exists(self, org_id, role_id):
        """See `CloudApi.custom_role_exists`."""
        try:
            self._iam.get_role(
                request={"name": f"organizations/{org_id}/roles/{role_id}"}
            )
        except api_exceptions.NotFound:
            return False
        return True

    @_translated
    def custom_constraint_exists(self, org_id, name):
        """See `CloudApi.custom_constraint_exists`."""
        try:
            self._org_policy.get_custom_constraint(
                name=f"organizations/{org_id}/customConstraints/{name}"
            )
        except api_exceptions.NotFound:
            return False
        return True

    @_translated
    def list_org_policies(self, org_id):
        """See `CloudApi.list_org_policies`."""
        pager = self._org_policy.list_policies(parent=f"organizations/{org_id}")
        # Policy names read `organizations/<id>/policies/<constraint>`.
        return sorted(policy.name.rpartition("/")[2] for policy in pager)

    @_translated
    def log_sink_exists(self, org_id, name):
        """See `CloudApi.log_sink_exists`."""
        url = f"{_LOGGING_URL}/organizations/{org_id}/sinks/{name}"
        return self._rest_call("GET", url) is not None

    @_translated
    def group_exists(self, email):
        """See `CloudApi.group_exists`."""
        found = self._rest_call(
            "GET", _CLOUD_IDENTITY_URL, params={"groupKey.id": email}
        )
        return found is not None

    def adc_info(self):
        """See `CloudApi.adc_info`."""
        credentials = self._credentials
        if getattr(credentials, "service_account_email", None):
            kind = api.PrincipalKind.SERVICE_ACCOUNT
        elif isinstance(credentials, oauth2_credentials.Credentials):
            kind = api.PrincipalKind.USER
        else:
            kind = api.PrincipalKind.UNKNOWN
        return api.AdcInfo(kind, getattr(credentials, "quota_project_id", None))

    @_translated
    def effective_service_restriction(self, resource):
        """See `CloudApi.effective_service_restriction`."""
        policy = self._org_policy.get_effective_policy(
            name=f"{resource}/policies/{_RESTRICT_SERVICE_USAGE}"
        )
        return _restriction(policy)

    @_translated
    def assured_workload(self, name):
        """See `CloudApi.assured_workload`."""
        body = self._rest_call("GET", _workload_url(name))
        return None if body is None else _workload_info(body)

    def _storage_client(self, impersonate):
        if impersonate is None:
            return self._storage
        credentials = impersonated_credentials.Credentials(
            source_credentials=self._credentials,
            target_principal=impersonate,
            target_scopes=[_SCOPES[0]],
        )
        return storage.Client(credentials=credentials, project="_")

    @_translated
    def read_object(self, bucket, name, *, impersonate=None):
        """See `CloudApi.read_object`."""
        client = self._storage_client(impersonate)
        try:
            blob = client.bucket(bucket).get_blob(name)
            if blob is None:
                return None
            # The precondition keeps the bytes and the generation in step.
            generation = blob.generation
            data = blob.download_as_bytes(if_generation_match=generation)
        except api_exceptions.NotFound:
            return None
        except auth_exceptions.RefreshError as error:
            if impersonate is None:
                raise api.CredentialsError(str(error)) from error
            # The IAM Credentials API refuses the impersonated token this
            # way when the caller lacks Service Account Token Creator.
            raise api.AccessDeniedError(
                f"Cannot impersonate {impersonate} to read gs://{bucket}/"
                f"{name}: {error}"
            ) from error
        return api.ObjectData(data, generation or 0)

    def _billing_policy_message(self, account_id):
        """Returns the resource name and the raw policy of a billing account.

        The callers translate errors.
        """
        resource = f"billingAccounts/{account_id}"
        policy = self._billing.get_iam_policy(
            request={
                "resource": resource,
                "options": {"requested_policy_version": _POLICY_VERSION},
            }
        )
        return resource, policy

    @_translated
    def billing_account_iam(self, account_id):
        """See `CloudApi.billing_account_iam`."""
        _, policy = self._billing_policy_message(account_id)
        return _to_policy(policy)

    @_translated
    def service_accounts(self, project_id):
        """See `CloudApi.service_accounts`."""
        pager = self._iam.list_service_accounts(
            request={"name": f"projects/{project_id}"}
        )
        return [
            api.ServiceAccount(account.email, account.disabled)
            for account in pager
        ]

    @_translated
    def gcs_service_agent(self, project_id):
        """See `CloudApi.gcs_service_agent`."""
        return self._storage.get_service_account_email(project=project_id)

    @_translated
    def set_org_iam_policy(self, org_id, policy, *, etag, update_mask):
        """See `CloudWriter.set_org_iam_policy`."""
        if not etag:
            raise ValueError("An organization IAM write needs the read etag.")
        written = self._organizations.set_iam_policy(
            request={
                "resource": f"organizations/{org_id}",
                "policy": _to_message(policy, etag),
                "update_mask": field_mask_pb2.FieldMask(
                    paths=[_field_path(name) for name in update_mask]
                ),
            }
        )
        return _to_policy(written)

    @_translated
    def enable_services(self, project_id, services):
        """See `CloudWriter.enable_services`."""
        for batch in _batches(sorted(services), _ENABLE_BATCH):
            operation = self._service_usage.batch_enable_services(
                request={
                    "parent": f"projects/{project_id}",
                    "service_ids": batch,
                }
            )
            try:
                operation.result(timeout=_OPERATION_TIMEOUT_SECONDS)
            except futures.TimeoutError as error:
                raise api.CloudError(
                    f"Enabling {', '.join(batch)} on {project_id} did not "
                    f"finish in {_OPERATION_TIMEOUT_SECONDS} seconds."
                ) from error

    @_translated
    def restrict_allowed_resources(self, name):
        """See `CloudWriter.restrict_allowed_resources`."""
        found = self._rest_call(
            "POST",
            f"{_workload_url(name)}:restrictAllowedResources",
            body={"restrictionType": _APPEND_COMPLIANT},
        )
        if found is None:
            raise api.CloudError(f"The workload {name} does not exist.")

    @_translated
    def add_billing_account_binding(self, account_id, role, member):
        """See `CloudWriter.add_billing_account_binding`."""
        resource, policy = self._billing_policy_message(account_id)
        binding = next(
            (
                item
                for item in policy.bindings
                if item.role == role and not item.HasField("condition")
            ),
            None,
        )
        if binding is None:
            binding = policy.bindings.add(role=role)
        if member in binding.members:
            return
        binding.members.append(member)
        # The policy carries the etag of the read, so a concurrent change
        # fails the write instead of being overwritten.
        self._billing.set_iam_policy(
            request={"resource": resource, "policy": policy}
        )

    @_translated
    def generate_service_identity(self, project_id, service):
        """See `CloudWriter.generate_service_identity`."""
        operation = self._rest_call(
            "POST",
            f"{_SERVICE_USAGE_BETA_URL}/projects/{project_id}/services/"
            f"{service}:generateServiceIdentity",
        )
        if operation is None:
            raise api.CloudError(f"Project {project_id} does not exist.")
        return (operation.get("response") or {}).get("email")
