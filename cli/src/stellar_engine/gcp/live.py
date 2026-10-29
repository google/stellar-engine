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

"""Live `CloudApi` implementation backed by Google Cloud client libraries.

All calls are read-only and use Application Default Credentials. Clients are
created lazily so that a check which never runs never needs its API. Every
public method translates Google API errors into the facade's error types.
"""

from concurrent import futures
import functools

from google.api_core import exceptions as api_exceptions
import google.auth
from google.auth import exceptions as auth_exceptions
from google.auth.transport import requests as auth_requests
from google.cloud import billing_v1
from google.cloud import iam_admin_v1
from google.cloud import orgpolicy_v2
from google.cloud import resourcemanager_v3
from google.cloud import service_usage_v1
from google.cloud import storage
import requests

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
_TEST_PERMISSIONS_BATCH = 100
_MAX_WORKERS = 8
_HTTP_NOT_FOUND = 404
_HTTP_FORBIDDEN = (401, 403)


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

    def _rest_get(self, url, params=None):
        """Issues a GET and maps HTTP errors to the facade conventions.

        Returns:
            The decoded JSON body, or None for HTTP 404.

        Raises:
            AccessDeniedError: For HTTP 401 or 403.
            CloudError: For any other HTTP error.
        """
        response = self._session.get(url, params=params, timeout=30)
        if response.status_code == _HTTP_NOT_FOUND:
            return None
        if response.status_code in _HTTP_FORBIDDEN:
            try:
                body = response.json()
            except ValueError:
                body = None
            raise _rest_denied(body, f"HTTP {response.status_code}")
        if not response.ok:
            raise api.CloudError(
                f"HTTP {response.status_code} from {url}: {response.text[:200]}"
            )
        return response.json()

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
            info = self._rest_get(
                _TOKENINFO_URL, {"access_token": credentials.token}
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
    def org_iam_bindings(self, org_id):
        """See `CloudApi.org_iam_bindings`."""
        policy = self._organizations.get_iam_policy(
            request={
                "resource": f"organizations/{org_id}",
                "options": {"requested_policy_version": 3},
            }
        )
        return [
            api.IamBinding(binding.role, tuple(binding.members))
            for binding in policy.bindings
        ]

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
        return self._rest_get(url) is not None

    @_translated
    def group_exists(self, email):
        """See `CloudApi.group_exists`."""
        found = self._rest_get(_CLOUD_IDENTITY_URL, {"groupKey.id": email})
        return found is not None
