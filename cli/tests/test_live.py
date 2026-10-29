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

from google.api_core import exceptions as api_exceptions
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
