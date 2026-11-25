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

from collections.abc import Callable, Mapping
from concurrent import futures
import dataclasses
import functools
from importlib import util as importlib_util
import ipaddress
import json
import os
import pathlib
import shutil
import subprocess
from typing import Any
from urllib import parse

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
from requests import adapters as requests_adapters

from stellar_engine.gcp import api

# The email scopes let tokeninfo report the user behind user credentials;
# without them, refreshed user tokens carry only cloud-platform.
_SCOPES = (
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
)
TRANSPORT_GRPC = "grpc"
TRANSPORT_REST = "rest"
VALID_TRANSPORTS = (TRANSPORT_GRPC, TRANSPORT_REST)
TRANSPORT_ENV_VAR = "STELLAR_GCP_TRANSPORT"

_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_CLOUD_IDENTITY_URL = "https://cloudidentity.googleapis.com/v1/groups:lookup"
_IAM_URL = "https://iam.googleapis.com/v1"
_LOGGING_URL = "https://logging.googleapis.com/v2"
_TEST_PERMISSIONS_BATCH = 100
_MAX_WORKERS = 8
_HTTP_NOT_FOUND = 404
_HTTP_FORBIDDEN = (401, 403)
_GCLOUD_TIMEOUT_SECONDS = 5
_PROXY_SCHEMES = {
    "http": "http",
    "http_no_tunnel": "http",
    "socks4": "socks4",
    "socks5": "socks5",
}


@dataclasses.dataclass(frozen=True)
class NetworkConfig:
    """TLS CA bundle and HTTP proxy settings for Google Cloud requests.

    Attributes:
        ca_bundle: Path to a PEM certificate bundle for TLS verification, or
            None to use the default trust store.
        proxies: Mapping of URL scheme (`http`, `https`) to proxy URL.
    """

    ca_bundle: str | None = None
    proxies: Mapping[str, str] = dataclasses.field(default_factory=dict)


def resolve_transport(
    transport: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resolves and validates the Google Cloud client transport.

    Args:
        transport: Explicit transport name, or None to read
            `STELLAR_GCP_TRANSPORT` and default to `grpc`.
        environ: Process environment mapping, defaulting to `os.environ`.

    Returns:
        Either `grpc` or `rest`.

    Raises:
        ValueError: If the transport name is not `grpc` or `rest`.
    """
    if transport is None:
        env = os.environ if environ is None else environ
        raw = env.get(TRANSPORT_ENV_VAR, "").strip()
        if not raw:
            return TRANSPORT_GRPC
        value = raw
    else:
        value = transport
    selected = value.strip().lower()
    if selected not in VALID_TRANSPORTS:
        expected = ", ".join(VALID_TRANSPORTS)
        raise ValueError(
            f"Invalid transport {value!r}; expected one of {expected}."
        )
    return selected


def _read_gcloud_config() -> dict[str, Any]:
    """Returns active gcloud configuration as a dict, or empty on failure."""
    if shutil.which("gcloud") is None:
        return {}
    try:
        completed = subprocess.run(
            ["gcloud", "config", "list", "--format=json"],
            capture_output=True,
            check=True,
            shell=False,
            text=True,
            timeout=_GCLOUD_TIMEOUT_SECONDS,
        )
        data = json.loads(completed.stdout)
    except OSError, subprocess.SubprocessError, ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _format_proxy_host(address: str) -> str | None:
    """Formats a proxy address, bracketing bare IPv6 literals."""
    stripped = address.strip()
    if not stripped:
        return None
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            ipaddress.IPv6Address(stripped[1:-1])
        except ValueError:
            return None
        return stripped
    try:
        ip = ipaddress.ip_address(stripped)
    except ValueError:
        if any(char in stripped for char in (":", "/", "@", " ", "\t")):
            return None
        return stripped
    return f"[{ip}]" if isinstance(ip, ipaddress.IPv6Address) else str(ip)


def _has_socks_proxy(proxies: Mapping[str, str]) -> bool:
    """Returns whether any configured proxy uses a SOCKS scheme."""
    return any(
        parse.urlsplit(url).scheme.lower().startswith("socks")
        for url in proxies.values()
    )


def _gcloud_proxy_url(proxy_section: object) -> str | None:
    """Builds a requests-compatible proxy URL from a gcloud `proxy` section."""
    if not isinstance(proxy_section, Mapping):
        return None
    host = _format_proxy_host(str(proxy_section.get("address") or ""))
    if host is None:
        return None
    proxy_type = str(proxy_section.get("type") or "http").strip().lower()
    scheme = _PROXY_SCHEMES.get(proxy_type)
    if scheme is None:
        return None
    raw_rdns = proxy_section.get("rdns")
    rdns = (
        True if raw_rdns is None else str(raw_rdns).strip().lower() != "false"
    )
    if scheme == "socks4" and rdns:
        scheme = "socks4a"
    elif scheme == "socks5" and rdns:
        scheme = "socks5h"
    port = str(proxy_section.get("port") or "").strip()
    if port and not port.isdigit():
        return None
    netloc = f"{host}:{port}" if port else host
    username = str(proxy_section.get("username") or "").strip()
    password = str(proxy_section.get("password") or "")
    if username:
        user_enc = parse.quote(username, safe="")
        auth = (
            f"{user_enc}:{parse.quote(password, safe='')}"
            if password
            else user_enc
        )
        netloc = f"{auth}@{netloc}"
    return f"{scheme}://{netloc}"


def detect_network_config(
    environ: Mapping[str, str] | None = None,
    gcloud_config: Mapping[str, Any] | None = None,
) -> NetworkConfig:
    """Detects custom CA certificate and proxy settings from env and gcloud.

    Standard environment variables (`REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`,
    `SSL_CERT_FILE`, `HTTPS_PROXY`, `HTTP_PROXY`) take precedence over gcloud
    properties (`core/custom_ca_certs_file` and `proxy/*`).

    Args:
        environ: Process environment mapping, defaulting to `os.environ`.
        gcloud_config: Optional pre-loaded `gcloud config list --format=json`
            mapping. When None, gcloud is queried only if a setting is unset
            in `environ`.

    Returns:
        A `NetworkConfig` with resolved CA bundle path and proxy map.
    """
    env = os.environ if environ is None else environ
    ca_bundle = (
        env.get("REQUESTS_CA_BUNDLE", "").strip()
        or env.get("CURL_CA_BUNDLE", "").strip()
        or env.get("SSL_CERT_FILE", "").strip()
        or None
    )
    proxies: dict[str, str] = {}
    http_proxy = (
        env.get("HTTP_PROXY", "").strip() or env.get("http_proxy", "").strip()
    )
    https_proxy = (
        env.get("HTTPS_PROXY", "").strip() or env.get("https_proxy", "").strip()
    )
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy

    if ca_bundle is None or not proxies:
        config = (
            _read_gcloud_config() if gcloud_config is None else gcloud_config
        )
        if ca_bundle is None:
            core = config.get("core")
            if isinstance(core, Mapping):
                raw_ca = str(core.get("custom_ca_certs_file") or "").strip()
                if raw_ca:
                    ca_bundle = str(pathlib.Path(raw_ca).expanduser())
        if not proxies:
            proxy_url = _gcloud_proxy_url(config.get("proxy"))
            if proxy_url:
                proxies = {"http": proxy_url, "https": proxy_url}

    return NetworkConfig(ca_bundle=ca_bundle, proxies=proxies)


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

    def __init__(
        self,
        transport: str | None = None,
        *,
        environ: Mapping[str, str] | None = None,
        network_config: NetworkConfig | None = None,
    ) -> None:
        """Initializes the facade with transport and TLS/proxy settings.

        Args:
            transport: Transport protocol (`grpc` or `rest`), or None to read
                `STELLAR_GCP_TRANSPORT` and default to `grpc`.
            environ: Optional process environment mapping for transport and
                network configuration detection.
            network_config: Optional pre-resolved `NetworkConfig`. When None,
                settings are detected lazily on first HTTP use.

        Raises:
            ValueError: If the resolved transport is not `grpc` or `rest`.
        """
        self._environ = environ
        self._transport = resolve_transport(transport, environ=environ)
        self._provided_network_config = network_config

    @property
    def transport(self) -> str:
        """Returns the active transport (`grpc` or `rest`)."""
        return self._transport

    @functools.cached_property
    def _network_config(self) -> NetworkConfig:
        if self._provided_network_config is not None:
            return self._provided_network_config
        return detect_network_config(environ=self._environ)

    def _configure_session(self, session):
        """Applies detected CA bundle and proxy settings to a session."""
        config = self._network_config
        if config.ca_bundle:
            session.verify = config.ca_bundle
        if config.proxies:
            if (
                _has_socks_proxy(config.proxies)
                and importlib_util.find_spec("socks") is None
            ):
                raise api.CloudError(
                    "A SOCKS proxy is configured, but PySocks is not "
                    "installed. Install PySocks or configure an HTTP proxy."
                )
            session.proxies.update(config.proxies)
        return session

    def _gapic_client[T](self, client_cls: Callable[..., T]) -> T:
        """Builds a GAPIC client with configured transport and TLS/proxy."""
        client = client_cls(
            credentials=self._credentials, transport=self._transport
        )
        if self._transport == TRANSPORT_REST:
            transport = getattr(client, "transport", None)
            session = getattr(transport, "_session", None)
            if session is not None:
                self._configure_session(session)
                auth_session = getattr(session, "_auth_request_session", None)
                if auth_session is not None:
                    self._configure_session(auth_session)
        return client

    @functools.cached_property
    def _credentials(self):
        try:
            credentials, _ = google.auth.default(scopes=_SCOPES)
        except auth_exceptions.DefaultCredentialsError as error:
            raise api.CredentialsError(str(error)) from error
        return credentials

    @functools.cached_property
    def _auth_request(self):
        session = requests.Session()
        adapter = requests_adapters.HTTPAdapter(max_retries=3)
        session.mount("https://", adapter)
        self._configure_session(session)
        return auth_requests.Request(session)

    @functools.cached_property
    def _session(self):
        session = auth_requests.AuthorizedSession(
            self._credentials, auth_request=self._auth_request
        )
        return self._configure_session(session)

    @functools.cached_property
    def _organizations(self):
        return self._gapic_client(resourcemanager_v3.OrganizationsClient)

    @functools.cached_property
    def _projects(self):
        return self._gapic_client(resourcemanager_v3.ProjectsClient)

    @functools.cached_property
    def _folders(self):
        return self._gapic_client(resourcemanager_v3.FoldersClient)

    @functools.cached_property
    def _iam(self):
        # google-cloud-iam exposes only gRPC transports; REST mode uses IAM v1
        # HTTP endpoints directly over `self._session`.
        return iam_admin_v1.IAMClient(
            credentials=self._credentials, transport=TRANSPORT_GRPC
        )

    @functools.cached_property
    def _billing(self):
        return self._gapic_client(billing_v1.CloudBillingClient)

    @functools.cached_property
    def _service_usage(self):
        return self._gapic_client(service_usage_v1.ServiceUsageClient)

    @functools.cached_property
    def _storage(self):
        return storage.Client(
            credentials=self._credentials, project="_", _http=self._session
        )

    @functools.cached_property
    def _org_policy(self):
        return self._gapic_client(orgpolicy_v2.OrgPolicyClient)

    def _rest_request(self, method, url, *, params=None, json_body=None):
        """Issues an HTTP request and maps errors to the facade conventions.

        Returns:
            The decoded JSON body, or None for HTTP 404.

        Raises:
            AccessDeniedError: For HTTP 401 or 403.
            CloudError: For any other HTTP error.
        """
        response = self._session.request(
            method, url, params=params, json=json_body, timeout=30
        )
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

    def _rest_get(self, url, params=None):
        """Issues a GET and maps HTTP errors to the facade conventions."""
        return self._rest_request("GET", url, params=params)

    def _rest_post(self, url, json_body=None):
        """Issues a POST and maps HTTP errors to the facade conventions."""
        return self._rest_request("POST", url, json_body=json_body)

    def adc_principal(self):
        """See `CloudApi.adc_principal`."""
        credentials = self._credentials
        email = getattr(credentials, "service_account_email", None)
        if email and email != "default":
            return api.Principal(email, api.PrincipalKind.SERVICE_ACCOUNT)
        try:
            credentials.refresh(self._auth_request)
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
        if self._transport == TRANSPORT_REST:
            data = self._rest_get(f"{_IAM_URL}/{role}")
            if data is None:
                raise api.CloudError(f"Role {role} not found.")
            return list(data.get("includedPermissions", []))
        role_info = self._iam.get_role(request={"name": role})
        return list(role_info.included_permissions)

    @functools.cache  # noqa: B019 - the facade lives for one CLI run.
    @_translated
    def _query_testable_permissions(
        self, full_resource_name: str
    ) -> tuple[frozenset[str], frozenset[str]]:
        """Queries testable permissions once, separating custom-role support."""
        all_perms: set[str] = set()
        custom_perms: set[str] = set()
        if self._transport == TRANSPORT_REST:
            page_token = None
            url = f"{_IAM_URL}/permissions:queryTestablePermissions"
            while True:
                payload: dict[str, Any] = {
                    "fullResourceName": full_resource_name,
                    "pageSize": 1000,
                }
                if page_token:
                    payload["pageToken"] = page_token
                data = self._rest_post(url, json_body=payload)
                if data is None:
                    raise api.CloudError(
                        f"Resource {full_resource_name} not found."
                    )
                for item in data.get("permissions", []):
                    name = item.get("name")
                    if not name:
                        continue
                    all_perms.add(name)
                    if item.get("customRolesSupportLevel") != "NOT_SUPPORTED":
                        custom_perms.add(name)
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
            return frozenset(all_perms), frozenset(custom_perms)
        unsupported_level = (
            iam_admin_v1.Permission.CustomRolesSupportLevel.NOT_SUPPORTED
        )
        pager = self._iam.query_testable_permissions(
            request={
                "full_resource_name": full_resource_name,
                "page_size": 1000,
            }
        )
        for permission in pager:
            all_perms.add(permission.name)
            if permission.custom_roles_support_level != unsupported_level:
                custom_perms.add(permission.name)
        return frozenset(all_perms), frozenset(custom_perms)

    def testable_permissions(self, full_resource_name):
        """See `CloudApi.testable_permissions`."""
        return set(self._query_testable_permissions(full_resource_name)[0])

    def custom_role_permissions(self, full_resource_name):
        """See `CloudApi.custom_role_permissions`."""
        return set(self._query_testable_permissions(full_resource_name)[1])

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
        name = f"organizations/{org_id}/roles/{role_id}"
        if self._transport == TRANSPORT_REST:
            return self._rest_get(f"{_IAM_URL}/{name}") is not None
        try:
            self._iam.get_role(request={"name": name})
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
