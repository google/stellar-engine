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

"""Tests for error translation in the live Google Cloud facade."""

import json
import os
import subprocess

from google.api_core import exceptions as api_exceptions
from google.auth import credentials as ga_credentials
from google.auth import exceptions as auth_exceptions
from google.rpc import error_details_pb2
import pytest
import requests

from stellar_engine.gcp import api
from stellar_engine.gcp import live


def _service_disabled():
    info = error_details_pb2.ErrorInfo(
        reason="SERVICE_DISABLED",
        domain="googleapis.com",
        metadata={
            "service": "cloudbilling.googleapis.com",
            "consumer": "projects/123",
        },
    )
    return api_exceptions.PermissionDenied(
        "Cloud Billing API has not been used\nlots of detail",
        details=[info],
        error_info=info,
    )


def test_service_disabled_becomes_api_disabled():
    error = live._denied(_service_disabled())
    assert isinstance(error, api.ApiDisabledError)
    assert error.service == "cloudbilling.googleapis.com"
    assert error.project == "123"
    assert "--project=123" in str(error)


@pytest.mark.parametrize(
    "raised",
    [
        api_exceptions.PermissionDenied("denied here\nstack noise"),
        api_exceptions.Forbidden("denied here\nstack noise"),
        api_exceptions.Unauthenticated("denied here\nstack noise"),
        api_exceptions.Unauthorized("denied here\nstack noise"),
    ],
)
def test_denials_are_shortened(raised):
    error = live._denied(raised)
    assert type(error) is api.AccessDeniedError
    assert str(error) == "denied here"


def test_http_denials_become_access_denied():
    # A REST transport raises the HTTP classes, not the gRPC subclasses.
    for status in (401, 403):
        error = live._denied(api_exceptions.from_http_status(status, "no"))
        assert type(error) is api.AccessDeniedError


def test_rest_service_disabled():
    body = {
        "error": {
            "message": "disabled",
            "details": [
                {
                    "reason": "SERVICE_DISABLED",
                    "metadata": {
                        "service": "cloudidentity.googleapis.com",
                        "consumer": "projects/9",
                    },
                }
            ],
        }
    }
    error = live._rest_denied(body, "HTTP 403")
    assert isinstance(error, api.ApiDisabledError)
    assert error.service == "cloudidentity.googleapis.com"


def test_rest_fallback_message():
    assert str(live._rest_denied(None, "HTTP 401")) == "HTTP 401"
    body = {"error": {"message": "nope"}}
    assert str(live._rest_denied(body, "HTTP 403")) == "nope"


def test_batches():
    assert live._batches(list(range(5)), 2) == [[0, 1], [2, 3], [4]]


class _Credentials:
    def __init__(self, email=None, token="token"):
        if email is not None:
            self.service_account_email = email
        self.token = token
        self.refreshed = False

    def refresh(self, request):
        self.refreshed = True
        if getattr(self, "service_account_email", None) == "default":
            self.service_account_email = "vm@example.iam.gserviceaccount.com"


@pytest.fixture
def adc(monkeypatch):
    """Patches google.auth.default and records the requested scopes."""
    state = {}

    def install(credentials):
        def default(scopes=None):
            state["scopes"] = scopes
            return credentials, "project"

        monkeypatch.setattr(live.google.auth, "default", default)
        return state

    return install


def test_user_credentials_resolve_email(adc, monkeypatch):
    state = adc(_Credentials())
    cloud = live.LiveCloudApi()
    monkeypatch.setattr(
        cloud, "_rest_get", lambda url, params=None: {"email": "a@example.com"}
    )
    principal = cloud.adc_principal()
    assert principal == api.Principal("a@example.com", api.PrincipalKind.USER)
    # Without the email scope, tokeninfo never returns the user's email.
    assert "https://www.googleapis.com/auth/userinfo.email" in state["scopes"]


def test_service_account_credentials(adc):
    adc(_Credentials("sa@example.iam.gserviceaccount.com"))
    principal = live.LiveCloudApi().adc_principal()
    assert principal.kind == api.PrincipalKind.SERVICE_ACCOUNT


def test_metadata_server_credentials(adc):
    adc(_Credentials("default"))
    principal = live.LiveCloudApi().adc_principal()
    assert principal.email == "vm@example.iam.gserviceaccount.com"


def test_unknown_when_tokeninfo_has_no_email(adc, monkeypatch):
    adc(_Credentials())
    cloud = live.LiveCloudApi()
    monkeypatch.setattr(cloud, "_rest_get", lambda url, params=None: {})
    assert cloud.adc_principal().kind == api.PrincipalKind.UNKNOWN


def test_missing_credentials(monkeypatch):
    def default(scopes=None):
        raise auth_exceptions.DefaultCredentialsError("none")

    monkeypatch.setattr(live.google.auth, "default", default)
    with pytest.raises(api.CredentialsError):
        live.LiveCloudApi().adc_principal()


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (api_exceptions.PermissionDenied("no"), api.AccessDeniedError),
        (api_exceptions.Forbidden("no"), api.AccessDeniedError),
        (api_exceptions.Unauthorized("no"), api.AccessDeniedError),
        (api_exceptions.InvalidArgument("bad"), api.CloudError),
        (requests.ConnectionError("offline"), api.CloudError),
    ],
)
def test_translated_decorator(raised, expected):
    @live._translated
    def call():
        raise raised

    with pytest.raises(expected) as caught:
        call()
    assert type(caught.value) is expected


class _Project:
    def __init__(self, project_id, state):
        self.project_id = project_id
        self.state = type("State", (), {"name": state})()


def test_visible_project_state_queries_soft_deleted(monkeypatch):
    queries = []

    class Projects:
        def search_projects(self, query):
            queries.append(query)
            if "DELETE_REQUESTED" in query:
                return [_Project("abc-prod-iac-core-0", "DELETE_REQUESTED")]
            return [_Project("abc-prod-iac-core-01", "ACTIVE")]

    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_projects", Projects())
    assert cloud.visible_project_state("abc-prod-iac-core-0") == (
        "DELETE_REQUESTED"
    )
    assert queries == [
        "id:abc-prod-iac-core-0",
        "id:abc-prod-iac-core-0 state:DELETE_REQUESTED",
    ]


def test_find_folders_ignores_deleted_folders(monkeypatch):
    queries = []

    class _Folder:
        name = "folders/111"

    class Folders:
        def search_folders(self, query):
            queries.append(query)
            return [_Folder()]

    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_folders", Folders())
    assert cloud.find_folders("123456789012", "StellarEngine-abc") == [
        "folders/111"
    ]
    assert queries == [
        'displayName="StellarEngine-abc" AND '
        "parent=organizations/123456789012 AND state=ACTIVE"
    ]


class _Account:
    def __init__(self, name, is_open):
        self.name = name
        self.open_ = is_open


def test_list_billing_accounts(monkeypatch):
    class Billing:
        def list_billing_accounts(self):
            return [
                _Account("billingAccounts/000000-AAAAAA-BBBBBB", True),
                _Account("billingAccounts/111111-AAAAAA-BBBBBB", False),
            ]

    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_billing", Billing())
    assert cloud.list_billing_accounts() == [
        api.BillingAccount("000000-AAAAAA-BBBBBB", True),
        api.BillingAccount("111111-AAAAAA-BBBBBB", False),
    ]


def test_list_billing_accounts_translates_errors(monkeypatch):
    class Billing:
        def list_billing_accounts(self):
            raise api_exceptions.PermissionDenied("no billing access")

    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_billing", Billing())
    with pytest.raises(api.AccessDeniedError, match="no billing access"):
        cloud.list_billing_accounts()


class _Policy:
    def __init__(self, name):
        self.name = name


def test_list_org_policies(monkeypatch):
    parents = []

    class OrgPolicy:
        def list_policies(self, parent):
            parents.append(parent)
            return [
                _Policy("organizations/123/policies/storage.publicAccess"),
                _Policy("organizations/123/policies/custom.kmsRotation"),
                _Policy(
                    "organizations/123/policies/iam.allowedPolicyMemberDomains"
                ),
            ]

    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_org_policy", OrgPolicy())
    assert cloud.list_org_policies("123") == [
        "custom.kmsRotation",
        "iam.allowedPolicyMemberDomains",
        "storage.publicAccess",
    ]
    assert parents == ["organizations/123"]


def test_list_org_policies_translates_errors(monkeypatch):
    class OrgPolicy:
        def list_policies(self, parent):
            raise _service_disabled()

    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_org_policy", OrgPolicy())
    with pytest.raises(api.ApiDisabledError):
        cloud.list_org_policies("123")


def test_transport_resolution_and_validation():
    assert live.LiveCloudApi(environ={}).transport == "grpc"
    assert live.LiveCloudApi("rest", environ={}).transport == "rest"
    assert live.LiveCloudApi("REST", environ={}).transport == "rest"
    assert live.LiveCloudApi("grpc", environ={}).transport == "grpc"
    assert (
        live.LiveCloudApi(environ={"STELLAR_GCP_TRANSPORT": "rest"}).transport
        == "rest"
    )
    assert (
        live.LiveCloudApi(
            "grpc", environ={"STELLAR_GCP_TRANSPORT": "rest"}
        ).transport
        == "grpc"
    )
    assert (
        live.LiveCloudApi(environ={"STELLAR_GCP_TRANSPORT": "   "}).transport
        == "grpc"
    )


@pytest.mark.parametrize(
    "bad_value", ["", "   ", "http", "grpc_asyncio", "invalid"]
)
def test_invalid_transport_raises(bad_value):
    with pytest.raises(ValueError, match="Invalid transport"):
        live.LiveCloudApi(bad_value, environ={})


def test_invalid_env_transport_raises():
    with pytest.raises(ValueError, match="Invalid transport"):
        live.LiveCloudApi(environ={"STELLAR_GCP_TRANSPORT": "bogus"})


def test_rest_transport_wires_all_rest_gapic_clients_and_storage(adc):
    adc(ga_credentials.AnonymousCredentials())
    config = live.NetworkConfig(
        ca_bundle="/etc/ssl/example-ca.pem",
        proxies={
            "http": "http://proxy.example.com:8080",
            "https": "http://proxy.example.com:8080",
        },
    )
    cloud = live.LiveCloudApi("rest", network_config=config)
    for attr in (
        "_organizations",
        "_projects",
        "_folders",
        "_billing",
        "_service_usage",
        "_org_policy",
    ):
        client = getattr(cloud, attr)
        assert type(client.transport).__name__.endswith("RestTransport")
        session = client.transport._session
        assert session.verify == "/etc/ssl/example-ca.pem"
        assert session.proxies["https"] == "http://proxy.example.com:8080"
        assert session._auth_request_session.verify == "/etc/ssl/example-ca.pem"
        assert (
            session._auth_request_session.proxies["https"]
            == "http://proxy.example.com:8080"
        )
    assert cloud._storage._http is cloud._session
    assert cloud._session.verify == "/etc/ssl/example-ca.pem"
    assert cloud._session.proxies["https"] == "http://proxy.example.com:8080"
    assert cloud._auth_request.session.verify == "/etc/ssl/example-ca.pem"


def test_grpc_transport_passes_grpc_to_gapic_clients(adc, monkeypatch):
    adc(ga_credentials.AnonymousCredentials())
    seen = {}

    def _capture(module, cls_name):
        def factory(*, credentials, transport):
            seen[cls_name] = transport
            return object()

        monkeypatch.setattr(module, cls_name, factory)

    _capture(live.resourcemanager_v3, "OrganizationsClient")
    _capture(live.resourcemanager_v3, "ProjectsClient")
    _capture(live.resourcemanager_v3, "FoldersClient")
    _capture(live.iam_admin_v1, "IAMClient")
    _capture(live.billing_v1, "CloudBillingClient")
    _capture(live.service_usage_v1, "ServiceUsageClient")
    _capture(live.orgpolicy_v2, "OrgPolicyClient")

    cloud = live.LiveCloudApi("grpc", network_config=live.NetworkConfig())
    _ = (
        cloud._organizations,
        cloud._projects,
        cloud._folders,
        cloud._iam,
        cloud._billing,
        cloud._service_usage,
        cloud._org_policy,
    )
    assert seen == {
        "OrganizationsClient": "grpc",
        "ProjectsClient": "grpc",
        "FoldersClient": "grpc",
        "IAMClient": "grpc",
        "CloudBillingClient": "grpc",
        "ServiceUsageClient": "grpc",
        "OrgPolicyClient": "grpc",
    }


def test_iam_methods_use_rest_in_rest_mode(monkeypatch):
    cloud = live.LiveCloudApi("rest", network_config=live.NetworkConfig())
    requests_made = []

    def fake_request(method, url, *, params=None, json_body=None):
        requests_made.append((method, url, json_body))
        if method == "GET" and url.endswith("/roles/owner"):
            return {"includedPermissions": ["resourcemanager.projects.get"]}
        if method == "GET" and url.endswith("/roles/missing"):
            return None
        if method == "GET" and url.endswith("/roles/tagViewer"):
            return {"name": "organizations/123/roles/tagViewer"}
        if method == "POST" and url.endswith(":queryTestablePermissions"):
            token = (json_body or {}).get("pageToken")
            if token is None:
                return {
                    "permissions": [
                        {"name": "storage.buckets.get"},
                        {
                            "name": "iam.serviceAccounts.actAs",
                            "customRolesSupportLevel": "NOT_SUPPORTED",
                        },
                    ],
                    "nextPageToken": "page-2",
                }
            return {
                "permissions": [
                    {
                        "name": "storage.objects.get",
                        "customRolesSupportLevel": "TESTING",
                    }
                ]
            }
        return None

    monkeypatch.setattr(cloud, "_rest_request", fake_request)
    assert cloud.role_permissions("roles/owner") == [
        "resourcemanager.projects.get"
    ]
    with pytest.raises(api.CloudError, match="not found"):
        cloud.role_permissions("roles/missing")
    assert cloud.custom_role_exists("123", "tagViewer") is True
    assert cloud.custom_role_exists("123", "missing") is False
    resource = "//cloudresourcemanager.googleapis.com/organizations/123"
    assert cloud.testable_permissions(resource) == {
        "storage.buckets.get",
        "iam.serviceAccounts.actAs",
        "storage.objects.get",
    }
    assert cloud.custom_role_permissions(resource) == {
        "storage.buckets.get",
        "storage.objects.get",
    }
    assert "_iam" not in cloud.__dict__
    # Both testable_permissions and custom_role_permissions share one query.
    assert len(requests_made) == 6


def test_grpc_custom_role_permissions_excludes_not_supported(monkeypatch):
    level = live.iam_admin_v1.Permission.CustomRolesSupportLevel
    calls = 0

    class _Perm:
        def __init__(self, name, support_level):
            self.name = name
            self.custom_roles_support_level = support_level

    class _Iam:
        def query_testable_permissions(self, request):
            nonlocal calls
            calls += 1
            return [
                _Perm("storage.buckets.get", level.SUPPORTED),
                _Perm("storage.objects.get", level.TESTING),
                _Perm("iam.serviceAccounts.actAs", level.NOT_SUPPORTED),
            ]

    cloud = live.LiveCloudApi("grpc", network_config=live.NetworkConfig())
    monkeypatch.setitem(cloud.__dict__, "_iam", _Iam())
    resource = "//cloudresourcemanager.googleapis.com/organizations/123"
    assert cloud.testable_permissions(resource) == {
        "storage.buckets.get",
        "storage.objects.get",
        "iam.serviceAccounts.actAs",
    }
    assert cloud.custom_role_permissions(resource) == {
        "storage.buckets.get",
        "storage.objects.get",
    }
    assert calls == 1


def test_detect_network_config_from_gcloud(monkeypatch):
    payload = {
        "core": {"custom_ca_certs_file": "/etc/ssl/gcloud-ca.pem"},
        "proxy": {
            "type": "http",
            "address": "proxy.example.com",
            "port": "8443",
        },
    }
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["shell"] = kwargs["shell"]
        captured["timeout"] = kwargs["timeout"]
        return subprocess.CompletedProcess(
            argv, 0, stdout=json.dumps(payload), stderr=""
        )

    monkeypatch.setattr(live.shutil, "which", lambda name: "/usr/bin/gcloud")
    monkeypatch.setattr(live.subprocess, "run", fake_run)
    env_before = dict(os.environ)

    config = live.detect_network_config(environ={})

    assert config.ca_bundle == "/etc/ssl/gcloud-ca.pem"
    assert config.proxies == {
        "http": "http://proxy.example.com:8443",
        "https": "http://proxy.example.com:8443",
    }
    assert captured["argv"] == ["gcloud", "config", "list", "--format=json"]
    assert captured["shell"] is False
    assert captured["timeout"] == live._GCLOUD_TIMEOUT_SECONDS
    assert dict(os.environ) == env_before


def test_detect_network_config_env_precedence(monkeypatch):
    called = False

    def fail_if_called(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("gcloud should not be invoked when env sets both")

    monkeypatch.setattr(live.subprocess, "run", fail_if_called)
    config = live.detect_network_config(
        environ={
            "REQUESTS_CA_BUNDLE": "/env/requests-ca.pem",
            "SSL_CERT_FILE": "/env/ssl-ca.pem",
            "HTTPS_PROXY": "http://env-proxy.example.com:3128",
        }
    )
    assert called is False
    assert config.ca_bundle == "/env/requests-ca.pem"
    assert config.proxies == {"https": "http://env-proxy.example.com:3128"}


def test_detect_network_config_ssl_cert_file_fallback():
    config = live.detect_network_config(
        environ={"SSL_CERT_FILE": "/env/ssl-ca.pem"},
        gcloud_config={"core": {"custom_ca_certs_file": "/gcloud/ca.pem"}},
    )
    assert config.ca_bundle == "/env/ssl-ca.pem"
    assert config.proxies == {}


def test_detect_network_config_missing_gcloud_falls_back(monkeypatch):
    monkeypatch.setattr(live.shutil, "which", lambda name: None)
    config = live.detect_network_config(environ={})
    assert config == live.NetworkConfig()


@pytest.mark.parametrize(
    "error",
    [
        subprocess.TimeoutExpired(["gcloud"], 5),
        subprocess.CalledProcessError(1, ["gcloud"]),
        OSError("exec failed"),
    ],
)
def test_detect_network_config_gcloud_failure_falls_back(monkeypatch, error):
    def fake_run(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(live.shutil, "which", lambda name: "/usr/bin/gcloud")
    monkeypatch.setattr(live.subprocess, "run", fake_run)
    assert live.detect_network_config(environ={}) == live.NetworkConfig()


def test_gcloud_proxy_url_variants():
    assert (
        live._gcloud_proxy_url(
            {
                "type": "http",
                "address": "proxy.example.com",
                "port": "8080",
            }
        )
        == "http://proxy.example.com:8080"
    )
    assert (
        live._gcloud_proxy_url(
            {
                "type": "http",
                "address": "10.0.0.1",
                "port": "3128",
            }
        )
        == "http://10.0.0.1:3128"
    )
    assert (
        live._gcloud_proxy_url(
            {
                "type": "socks5",
                "address": "proxy.example.com",
                "port": "1080",
                "username": "user@corp",
                "password": "p:w",
            }
        )
        == "socks5h://user%40corp:p%3Aw@proxy.example.com:1080"
    )
    assert (
        live._gcloud_proxy_url(
            {
                "type": "socks5",
                "address": "2001:db8::1",
                "port": "1080",
                "rdns": "false",
            }
        )
        == "socks5://[2001:db8::1]:1080"
    )
    assert (
        live._gcloud_proxy_url(
            {
                "type": "http",
                "address": "[2001:db8::1]",
                "port": "8080",
            }
        )
        == "http://[2001:db8::1]:8080"
    )
    assert live._gcloud_proxy_url({"type": "unknown", "address": "a"}) is None
    assert live._gcloud_proxy_url({"address": "a", "port": "bad"}) is None
    assert live._gcloud_proxy_url({"address": "proxy.example.com:8080"}) is None
    assert (
        live._gcloud_proxy_url({"address": "http://proxy.example.com"}) is None
    )
    assert live._gcloud_proxy_url({"address": "[not-ipv6]"}) is None


def test_socks_proxy_requires_pysocks(adc, monkeypatch):
    adc(ga_credentials.AnonymousCredentials())
    config = live.NetworkConfig(
        proxies={
            "https": "socks5h://user:secret@proxy.example.com:1080",
        }
    )
    monkeypatch.setattr(live.importlib_util, "find_spec", lambda name: None)
    cloud = live.LiveCloudApi("rest", network_config=config)
    with pytest.raises(api.CloudError, match="PySocks") as caught:
        _ = cloud._session
    assert "HTTP proxy" in str(caught.value)
    assert "secret" not in str(caught.value)


def test_socks_proxy_succeeds_when_pysocks_available(adc, monkeypatch):
    adc(ga_credentials.AnonymousCredentials())
    config = live.NetworkConfig(
        proxies={"https": "socks5h://proxy.example.com:1080"}
    )
    monkeypatch.setattr(live.importlib_util, "find_spec", lambda name: object())
    cloud = live.LiveCloudApi("rest", network_config=config)
    assert cloud._session.proxies["https"] == "socks5h://proxy.example.com:1080"
