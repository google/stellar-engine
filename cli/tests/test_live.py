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

"""Tests for the live Google Cloud facade with its clients faked."""

from concurrent import futures

from google.api_core import exceptions as api_exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import orgpolicy_v2
from google.iam.v1 import policy_pb2
from google.oauth2 import credentials as oauth2_credentials
from google.rpc import error_details_pb2
import pytest
import requests

import conftest
from stellar_engine import iam_diff
from stellar_engine.gcp import api
from stellar_engine.gcp import live

WORKLOAD = (
    f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/my-workload"
)
WORKLOAD_URL = f"https://us-east4-assuredworkloads.googleapis.com/v1/{WORKLOAD}"


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


def test_aborted_becomes_conflict():
    error = live._denied(api_exceptions.Aborted("etag changed\ndetail"))
    assert type(error) is api.ConflictError
    assert str(error) == "etag changed"


@pytest.mark.parametrize(
    ("name", "path"),
    [
        ("bindings", "bindings"),
        ("etag", "etag"),
        ("auditConfigs", "audit_configs"),
    ],
)
def test_field_path(name, path):
    assert live._field_path(name) == path


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
        cloud,
        "_rest_call",
        lambda method, url, params=None, body=None: {"email": "a@example.com"},
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
    monkeypatch.setattr(
        cloud, "_rest_call", lambda method, url, params=None, body=None: {}
    )
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


class _Response:
    def __init__(self, status, body=None, text=""):
        self.status_code = status
        self.ok = status < 400
        self._body = body
        self.text = text
        self.content = b"" if body is None else b"{}"

    def json(self):
        if self._body is None:
            raise ValueError("no JSON")
        return self._body


class _Session:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def request(self, method, url, params=None, json=None, timeout=None):
        self.requests.append((method, url, params, json))
        return self.response


def _rest(monkeypatch, response):
    cloud = live.LiveCloudApi()
    session = _Session(response)
    monkeypatch.setitem(cloud.__dict__, "_session", session)
    return cloud, session


def test_rest_call_returns_the_body(monkeypatch):
    cloud, session = _rest(monkeypatch, _Response(200, {"a": 1}))
    found = cloud._rest_call("POST", "https://x", params={"p": "1"}, body={})
    assert found == {"a": 1}
    assert session.requests == [("POST", "https://x", {"p": "1"}, {})]


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (_Response(404), None),
        (_Response(200), {}),
    ],
)
def test_rest_call_missing_and_empty(monkeypatch, response, expected):
    cloud, _ = _rest(monkeypatch, response)
    assert cloud._rest_call("GET", "https://x") == expected


@pytest.mark.parametrize(
    ("response", "error"),
    [
        (_Response(403, {"error": {"message": "nope"}}), api.AccessDeniedError),
        (_Response(401), api.AccessDeniedError),
        (_Response(409, text="ABORTED"), api.ConflictError),
        (_Response(500, text="boom"), api.CloudError),
    ],
)
def test_rest_call_errors(monkeypatch, response, error):
    cloud, _ = _rest(monkeypatch, response)
    with pytest.raises(error) as caught:
        cloud._rest_call("GET", "https://x")
    assert type(caught.value) is error


class _Recorder:
    """Records each call to a fake client method and returns a value."""

    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append(kwargs or args)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _client(**methods):
    """Returns a fake client whose methods are the given callables."""
    client = type("Client", (), {})()
    for name, method in methods.items():
        setattr(client, name, method)
    return client


def _live_policy():
    return policy_pb2.Policy(
        version=3,
        etag=b"etag",
        bindings=[
            policy_pb2.Binding(
                role="roles/browser", members=["domain:example.com"]
            ),
            policy_pb2.Binding(
                role="roles/viewer",
                members=["user:a@example.com"],
                condition={"title": "t", "expression": "true"},
            ),
        ],
        audit_configs=[
            policy_pb2.AuditConfig(
                service="allServices",
                audit_log_configs=[
                    policy_pb2.AuditLogConfig(
                        log_type=policy_pb2.AuditLogConfig.DATA_READ,
                        exempted_members=["user:quiet@example.com"],
                    )
                ],
            )
        ],
    )


def test_get_org_iam_policy(monkeypatch):
    get = _Recorder(_live_policy())
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__, "_organizations", _client(get_iam_policy=get)
    )
    policy = cloud.get_org_iam_policy(conftest.ORG_ID)
    assert get.calls == [
        {
            "request": {
                "resource": f"organizations/{conftest.ORG_ID}",
                "options": {"requested_policy_version": 3},
            }
        }
    ]
    assert policy.etag == "ZXRhZw=="
    condition = iam_diff.Condition("t", "true")
    assert policy.bindings == {
        iam_diff.BindingKey("roles/browser"): {"domain:example.com"},
        iam_diff.BindingKey("roles/viewer", condition): {"user:a@example.com"},
    }
    assert policy.audit_configs == {
        "allServices": (
            iam_diff.AuditLogConfig("DATA_READ", ("user:quiet@example.com",)),
        )
    }


def test_set_org_iam_policy(monkeypatch):
    written = _live_policy()
    set_policy = _Recorder(written)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__, "_organizations", _client(set_iam_policy=set_policy)
    )
    policy = iam_diff.Policy.from_json(
        {
            "version": 1,
            "bindings": [
                {"role": "roles/browser", "members": ["domain:example.com"]}
            ],
        }
    )
    found = cloud.set_org_iam_policy(
        conftest.ORG_ID,
        policy,
        etag="ZXRhZw==",
        update_mask=("bindings", "etag", "auditConfigs"),
    )
    request = set_policy.calls[0]["request"]
    assert request["resource"] == f"organizations/{conftest.ORG_ID}"
    assert request["policy"].version == 3
    assert request["policy"].etag == b"etag"
    assert [b.role for b in request["policy"].bindings] == ["roles/browser"]
    assert list(request["update_mask"].paths) == [
        "bindings",
        "etag",
        "audit_configs",
    ]
    assert found == live._to_policy(written)


def test_set_org_iam_policy_needs_an_etag():
    with pytest.raises(ValueError, match="etag"):
        live.LiveCloudApi().set_org_iam_policy(
            conftest.ORG_ID, iam_diff.Policy(), etag="", update_mask=()
        )


def test_set_org_iam_policy_conflict(monkeypatch):
    set_policy = _Recorder(api_exceptions.Aborted("stale etag"))
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__, "_organizations", _client(set_iam_policy=set_policy)
    )
    with pytest.raises(api.ConflictError, match="stale etag"):
        cloud.set_org_iam_policy(
            conftest.ORG_ID,
            iam_diff.Policy(),
            etag="ZXRhZw==",
            update_mask=("bindings", "etag"),
        )


def test_adc_info_for_user_credentials(adc):
    credentials = oauth2_credentials.Credentials(
        token="token", quota_project_id="my-project"
    )
    adc(credentials)
    assert live.LiveCloudApi().adc_info() == api.AdcInfo(
        api.PrincipalKind.USER, "my-project"
    )


def test_adc_info_for_service_accounts_and_others(adc):
    adc(_Credentials("sa@example.iam.gserviceaccount.com"))
    info = live.LiveCloudApi().adc_info()
    assert info == api.AdcInfo(api.PrincipalKind.SERVICE_ACCOUNT, None)
    adc(_Credentials())
    assert live.LiveCloudApi().adc_info().kind == api.PrincipalKind.UNKNOWN


def _rule(**values):
    return orgpolicy_v2.PolicySpec.PolicyRule(**values)


def _string_values(**values):
    return orgpolicy_v2.PolicySpec.PolicyRule.StringValues(**values)


def test_effective_service_restriction(monkeypatch):
    effective = orgpolicy_v2.Policy(
        spec=orgpolicy_v2.PolicySpec(
            rules=[
                _rule(
                    values=_string_values(
                        allowed_values=[
                            "is:bigquery.googleapis.com",
                            "storage.googleapis.com",
                        ],
                        denied_values=["is:compute.googleapis.com"],
                    )
                )
            ]
        )
    )
    get = _Recorder(effective)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__, "_org_policy", _client(get_effective_policy=get)
    )
    found = cloud.effective_service_restriction("folders/123")
    assert get.calls == [
        {"name": "folders/123/policies/gcp.restrictServiceUsage"}
    ]
    assert found == api.ServiceRestriction(
        allowed=("bigquery.googleapis.com", "storage.googleapis.com"),
        denied=("compute.googleapis.com",),
    )
    assert found.allows("bigquery.googleapis.com")
    assert not found.allows("bigquerystorage.googleapis.com")
    assert not found.allows("compute.googleapis.com")


def test_effective_service_restriction_without_rules(monkeypatch):
    cloud = live.LiveCloudApi()
    get = _Recorder(orgpolicy_v2.Policy())
    monkeypatch.setitem(
        cloud.__dict__, "_org_policy", _client(get_effective_policy=get)
    )
    found = cloud.effective_service_restriction("folders/123")
    assert found == api.ServiceRestriction()
    assert found.allows("bigquery.googleapis.com")


@pytest.mark.parametrize(
    ("restriction", "allowed"),
    [
        (api.ServiceRestriction(allow_all=True), True),
        (api.ServiceRestriction(deny_all=True), False),
        (api.ServiceRestriction(allow_all=True, denied=("x.com",)), False),
        (api.ServiceRestriction(allowed=("x.com",)), True),
        (api.ServiceRestriction(allowed=("y.com",)), False),
        (api.ServiceRestriction(denied=("y.com",)), True),
    ],
)
def test_service_restriction_allows(restriction, allowed):
    assert restriction.allows("is:x.com") is allowed


def _rest_calls(monkeypatch, cloud, result):
    calls = []

    def call(method, url, params=None, body=None):
        calls.append((method, url, body))
        return result

    monkeypatch.setattr(cloud, "_rest_call", call)
    return calls


def test_assured_workload(monkeypatch):
    cloud = live.LiveCloudApi()
    body = {
        "name": WORKLOAD,
        "complianceRegime": "IL5",
        "resources": [
            {"resourceId": "111", "resourceType": "ENCRYPTION_KEYS_PROJECT"},
            {"resourceId": "222", "resourceType": "CONSUMER_FOLDER"},
        ],
        "compliantButDisallowedServices": ["bigquery.googleapis.com"],
    }
    calls = _rest_calls(monkeypatch, cloud, body)
    assert cloud.assured_workload(WORKLOAD) == api.WorkloadInfo(
        WORKLOAD, "IL5", "folders/222", ("bigquery.googleapis.com",)
    )
    assert calls == [("GET", WORKLOAD_URL, None)]


def test_assured_workload_missing(monkeypatch):
    cloud = live.LiveCloudApi()
    _rest_calls(monkeypatch, cloud, None)
    assert cloud.assured_workload(WORKLOAD) is None


def test_assured_workload_rejects_other_names():
    with pytest.raises(ValueError, match="not an Assured Workloads"):
        live.LiveCloudApi().assured_workload("folders/123")


def test_restrict_allowed_resources(monkeypatch):
    cloud = live.LiveCloudApi()
    calls = _rest_calls(monkeypatch, cloud, {})
    cloud.restrict_allowed_resources(WORKLOAD)
    assert calls == [
        (
            "POST",
            f"{WORKLOAD_URL}:restrictAllowedResources",
            {"restrictionType": "APPEND_COMPLIANT_RESOURCES"},
        )
    ]


def test_restrict_allowed_resources_missing_workload(monkeypatch):
    cloud = live.LiveCloudApi()
    _rest_calls(monkeypatch, cloud, None)
    with pytest.raises(api.CloudError, match="does not exist"):
        cloud.restrict_allowed_resources(WORKLOAD)


def test_generate_service_identity(monkeypatch):
    cloud = live.LiveCloudApi()
    agent = "service-1@gcp-sa-cloudkms.iam.gserviceaccount.com"
    calls = _rest_calls(
        monkeypatch, cloud, {"done": True, "response": {"email": agent}}
    )
    found = cloud.generate_service_identity(
        "my-project", "cloudkms.googleapis.com"
    )
    assert found == agent
    assert calls == [
        (
            "POST",
            "https://serviceusage.googleapis.com/v1beta1/projects/my-project"
            "/services/cloudkms.googleapis.com:generateServiceIdentity",
            None,
        )
    ]


def test_generate_service_identity_pending_and_missing(monkeypatch):
    cloud = live.LiveCloudApi()
    _rest_calls(monkeypatch, cloud, {"done": False})
    assert cloud.generate_service_identity("my-project", "x.com") is None
    _rest_calls(monkeypatch, cloud, None)
    with pytest.raises(api.CloudError, match="does not exist"):
        cloud.generate_service_identity("my-project", "x.com")


class _Blob:
    def __init__(self, data, generation, error=None):
        self.data = data
        self.generation = generation
        self.error = error
        self.matches = []

    def download_as_bytes(self, if_generation_match=None):
        self.matches.append(if_generation_match)
        if self.error is not None:
            raise self.error
        return self.data


class _Storage:
    def __init__(self, blob):
        self.blob = blob
        self.reads = []

    def bucket(self, name):
        storage = self

        class Bucket:
            def get_blob(self, blob_name):
                storage.reads.append((name, blob_name))
                if isinstance(storage.blob, Exception):
                    raise storage.blob
                return storage.blob

        return Bucket()

    def get_service_account_email(self, project=None):
        return f"service-{project}@gs-project-accounts.iam.gserviceaccount.com"


def test_read_object(monkeypatch):
    blob = _Blob(b"{}", 17)
    storage = _Storage(blob)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_storage", storage)
    found = cloud.read_object("my-bucket", "default.tfstate")
    assert found == api.ObjectData(b"{}", 17)
    assert storage.reads == [("my-bucket", "default.tfstate")]
    # The download only accepts the generation the metadata named.
    assert blob.matches == [17]


@pytest.mark.parametrize(
    "blob", [None, _Blob(b"", 3, api_exceptions.NotFound("gone"))]
)
def test_read_object_missing(monkeypatch, blob):
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_storage", _Storage(blob))
    assert cloud.read_object("my-bucket", "default.tfstate") is None


def test_read_object_denied(monkeypatch):
    cloud = live.LiveCloudApi()
    storage = _Storage(api_exceptions.Forbidden("no storage access"))
    monkeypatch.setitem(cloud.__dict__, "_storage", storage)
    with pytest.raises(api.AccessDeniedError, match="no storage access"):
        cloud.read_object("my-bucket", "default.tfstate")


def test_read_object_impersonates(monkeypatch):
    built = {}

    def credentials(**kwargs):
        built["credentials"] = kwargs
        return "impersonated"

    storage = _Storage(_Blob(b"state", 5))

    def client(credentials, project):
        built["client"] = (credentials, project)
        return storage

    monkeypatch.setattr(
        live.impersonated_credentials, "Credentials", credentials
    )
    monkeypatch.setattr(live.storage, "Client", client)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_credentials", "adc")
    sa = "abc-prod-bootstrap-0@abc-prod-iac-core-0.iam.gserviceaccount.com"
    found = cloud.read_object("my-bucket", "default.tfstate", impersonate=sa)
    assert found == api.ObjectData(b"state", 5)
    assert built["credentials"] == {
        "source_credentials": "adc",
        "target_principal": sa,
        "target_scopes": ["https://www.googleapis.com/auth/cloud-platform"],
    }
    assert built["client"] == ("impersonated", "_")


@pytest.mark.parametrize(
    ("impersonate", "error"),
    [
        ("sa@my-project.iam.gserviceaccount.com", api.AccessDeniedError),
        (None, api.CredentialsError),
    ],
)
def test_read_object_refresh_errors(monkeypatch, impersonate, error):
    cloud = live.LiveCloudApi()
    storage = _Storage(auth_exceptions.RefreshError("no token"))
    monkeypatch.setattr(cloud, "_storage_client", lambda impersonate: storage)
    with pytest.raises(error, match="no token"):
        cloud.read_object("my-bucket", "x", impersonate=impersonate)


def test_gcs_service_agent(monkeypatch):
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_storage", _Storage(None))
    assert cloud.gcs_service_agent("my-project") == (
        "service-my-project@gs-project-accounts.iam.gserviceaccount.com"
    )


def test_billing_account_iam(monkeypatch):
    get = _Recorder(_live_policy())
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(cloud.__dict__, "_billing", _client(get_iam_policy=get))
    policy = cloud.billing_account_iam(conftest.BILLING)
    assert get.calls[0]["request"]["resource"] == (
        f"billingAccounts/{conftest.BILLING}"
    )
    assert iam_diff.BindingKey("roles/browser") in policy.bindings


def _billing_policy():
    return policy_pb2.Policy(
        etag=b"etag",
        bindings=[
            policy_pb2.Binding(
                role="roles/billing.user",
                members=["user:other@example.com"],
                condition={"title": "t", "expression": "true"},
            ),
            policy_pb2.Binding(
                role="roles/billing.viewer", members=["user:a@example.com"]
            ),
        ],
    )


@pytest.mark.parametrize(
    ("role", "member", "expected"),
    [
        # A conditional binding of the role is left alone.
        (
            "roles/billing.user",
            "serviceAccount:sa@my-project.iam.gserviceaccount.com",
            ["serviceAccount:sa@my-project.iam.gserviceaccount.com"],
        ),
        (
            "roles/billing.viewer",
            "user:b@example.com",
            ["user:a@example.com", "user:b@example.com"],
        ),
    ],
)
def test_add_billing_account_binding(monkeypatch, role, member, expected):
    get = _Recorder(_billing_policy())
    set_policy = _Recorder(None)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__,
        "_billing",
        _client(get_iam_policy=get, set_iam_policy=set_policy),
    )
    cloud.add_billing_account_binding(conftest.BILLING, role, member)
    request = set_policy.calls[0]["request"]
    assert request["resource"] == f"billingAccounts/{conftest.BILLING}"
    unconditional = [
        list(b.members)
        for b in request["policy"].bindings
        if b.role == role and not b.HasField("condition")
    ]
    assert unconditional == [expected]
    assert request["policy"].etag == b"etag"


def test_add_billing_account_binding_is_idempotent(monkeypatch):
    set_policy = _Recorder(None)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__,
        "_billing",
        _client(
            get_iam_policy=_Recorder(_billing_policy()),
            set_iam_policy=set_policy,
        ),
    )
    cloud.add_billing_account_binding(
        conftest.BILLING, "roles/billing.viewer", "user:a@example.com"
    )
    assert set_policy.calls == []


class _ServiceAccount:
    def __init__(self, email, disabled):
        self.email = email
        self.disabled = disabled


def test_service_accounts(monkeypatch):
    accounts = [
        _ServiceAccount("a@my-project.iam.gserviceaccount.com", False),
        _ServiceAccount("b@my-project.iam.gserviceaccount.com", True),
    ]
    listing = _Recorder(accounts)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__, "_iam", _client(list_service_accounts=listing)
    )
    assert cloud.service_accounts("my-project") == [
        api.ServiceAccount("a@my-project.iam.gserviceaccount.com", False),
        api.ServiceAccount("b@my-project.iam.gserviceaccount.com", True),
    ]
    assert listing.calls == [{"request": {"name": "projects/my-project"}}]


class _Operation:
    def __init__(self, error=None):
        self.error = error
        self.timeouts = []

    def result(self, timeout=None):
        self.timeouts.append(timeout)
        if self.error is not None:
            raise self.error


def test_enable_services_in_batches(monkeypatch):
    operation = _Operation()
    enable = _Recorder(operation)
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__,
        "_service_usage",
        _client(batch_enable_services=enable),
    )
    services = [f"api{index:02d}.googleapis.com" for index in range(25)]
    cloud.enable_services("my-project", reversed(services))
    batches = [call["request"]["service_ids"] for call in enable.calls]
    assert batches == [services[:20], services[20:]]
    assert {call["request"]["parent"] for call in enable.calls} == {
        "projects/my-project"
    }
    assert len(operation.timeouts) == 2


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (futures.TimeoutError(), api.CloudError),
        (
            api_exceptions.PermissionDenied("no serviceusage"),
            api.AccessDeniedError,
        ),
    ],
)
def test_enable_services_failures(monkeypatch, error, expected):
    cloud = live.LiveCloudApi()
    monkeypatch.setitem(
        cloud.__dict__,
        "_service_usage",
        _client(batch_enable_services=_Recorder(_Operation(error))),
    )
    with pytest.raises(expected):
        cloud.enable_services("my-project", ["x.googleapis.com"])
