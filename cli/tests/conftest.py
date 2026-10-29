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

"""Shared fixtures and in-memory fakes for the CLI tests."""

import dataclasses
import pathlib
import shutil
import stat

import pytest

from stellar_engine import repo as repo_lib
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.preflight import inputs as inputs_lib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ORG_ID = "123456789012"
DOMAIN = "example.com"
CUSTOMER_ID = "C01234567"
BILLING = "000000-AAAAAA-BBBBBB"
PROJECT = "example-bootstrap"
USER = "deployer@example.com"
# Addresses of the Stage 0 project resources that import blocks adopt.
AUTOMATION_ADDRESS = "module.automation-project.google_project.project[0]"
LOG_EXPORT_ADDRESS = "module.log-export-project.google_project.project[0]"
BILLING_EXPORT_ADDRESS = (
    "module.billing-export-project[0].google_project.project[0]"
)


def mode(path):
    """Returns the permission bits of a file or directory."""
    return stat.S_IMODE(path.stat().st_mode)


def pytest_collection_modifyitems(config, items):
    """Skips the tests marked `terraform` when the binary is missing."""
    del config  # Unused.
    if shutil.which("terraform") is not None:
        return
    skip = pytest.mark.skip(reason="terraform is not installed")
    for item in items:
        if item.get_closest_marker("terraform") is not None:
            item.add_marker(skip)


@dataclasses.dataclass
class FakeTools:
    """In-memory `LocalTools`."""

    terraform: str | None = "1.13.0"
    gcloud: str | None = "540.0.0"
    account: str | None = USER
    project: str | None = PROJECT
    jq: str | None = "jq-1.7.1"

    def terraform_version(self):
        return self.terraform

    def gcloud_version(self):
        return self.gcloud

    def gcloud_account(self):
        return self.account

    def gcloud_project(self):
        return self.project

    def jq_version(self):
        return self.jq

    def terraform_fmt(self, text):
        return None


@dataclasses.dataclass
class FakeCloud:
    """In-memory `CloudApi` with a healthy default state.

    Tests change one field to model one failure. A field holding an
    exception instance makes the matching method raise it.
    """

    principal: object = dataclasses.field(
        default_factory=lambda: api.Principal(USER, api.PrincipalKind.USER)
    )
    orgs: list = dataclasses.field(
        default_factory=lambda: [api.Organization(ORG_ID, DOMAIN, CUSTOMER_ID)]
    )
    role_perms: dict = dataclasses.field(default_factory=dict)
    org_testable: set | None = None
    billing_testable: set | None = None
    denied_org_perms: set = dataclasses.field(default_factory=set)
    denied_billing_perms: set = dataclasses.field(default_factory=set)
    billing_perm_error: Exception | None = None
    bindings: list = dataclasses.field(default_factory=list)
    billing_account: object = dataclasses.field(
        default_factory=lambda: api.BillingAccount(BILLING, True)
    )
    billing_accounts: object = dataclasses.field(
        default_factory=lambda: [api.BillingAccount(BILLING, True)]
    )
    project_link: object = dataclasses.field(
        default_factory=lambda: api.ProjectBilling(BILLING, True)
    )
    projects: dict = dataclasses.field(
        default_factory=lambda: {PROJECT: "ACTIVE"}
    )
    services: object = None
    buckets: set = dataclasses.field(default_factory=set)
    folders: list = dataclasses.field(default_factory=list)
    custom_roles: set = dataclasses.field(default_factory=set)
    constraints: set = dataclasses.field(default_factory=set)
    sinks: set = dataclasses.field(default_factory=set)
    org_policies: object = dataclasses.field(default_factory=list)
    groups: object = None
    calls: list = dataclasses.field(default_factory=list)

    @staticmethod
    def _value(value):
        if isinstance(value, Exception):
            raise value
        return value

    def adc_principal(self):
        return self._value(self.principal)

    def search_organizations(self):
        return self._value(self.orgs)

    def get_organization(self, org_id):
        orgs = self._value(self.orgs)
        return next((org for org in orgs if org.org_id == org_id), None)

    def role_permissions(self, role):
        return self.role_perms.get(role, [f"{role}.permission"])

    def testable_permissions(self, full_resource_name):
        if "cloudbilling" in full_resource_name:
            if self.billing_testable is not None:
                return self.billing_testable
        elif self.org_testable is not None:
            return self.org_testable
        return {p for perms in self._all_role_perms() for p in perms}

    def _all_role_perms(self):
        roles = repo_lib.Repo(REPO_ROOT).required_roles()
        return [self.role_permissions(role) for role in roles]

    def granted_org_permissions(self, org_id, permissions):
        self.calls.append(("org_perms", org_id, len(permissions)))
        return set(permissions) - self.denied_org_perms

    def granted_billing_permissions(self, account_id, permissions):
        if self.billing_perm_error:
            raise self.billing_perm_error
        return set(permissions) - self.denied_billing_perms

    def org_iam_bindings(self, org_id):
        return self._value(self.bindings)

    def get_billing_account(self, account_id):
        return self._value(self.billing_account)

    def list_billing_accounts(self):
        return self._value(self.billing_accounts)

    def project_billing(self, project_id):
        return self._value(self.project_link)

    def project_state(self, project_id):
        return self._value(self.projects.get(project_id))

    def enabled_services(self, project_id):
        if self.services is None:
            repo = repo_lib.Repo(REPO_ROOT)
            return {*repo.required_apis(), *checks.EXTRA_APIS}
        return self._value(self.services)

    def visible_project_state(self, project_id):
        return self._value(self.projects.get(project_id))

    def bucket_exists(self, name):
        return name in self.buckets

    def find_folders(self, org_id, display_name):
        return self._value(self.folders)

    def custom_role_exists(self, org_id, role_id):
        return role_id in self.custom_roles

    def custom_constraint_exists(self, org_id, name):
        return name in self.constraints

    def log_sink_exists(self, org_id, name):
        return name in self.sinks

    def list_org_policies(self, org_id):
        self.calls.append(("org_policies", org_id))
        return sorted(self._value(self.org_policies))

    def group_exists(self, email):
        if self.groups is None:
            return True
        return email in self._value(self.groups)


@pytest.fixture
def repo():
    """Returns a Repo for the real checkout under test."""
    return repo_lib.Repo(REPO_ROOT)


@pytest.fixture
def cloud():
    """Returns a healthy FakeCloud."""
    return FakeCloud()


@pytest.fixture
def local_tools():
    """Returns healthy FakeTools."""
    return FakeTools()


@pytest.fixture
def make_ctx(repo, cloud, local_tools):
    """Returns a factory for check contexts with complete inputs."""

    def factory(environ=None, **overrides):
        values = {
            "org_id": ORG_ID,
            "billing_account": BILLING,
            "bootstrap_project": PROJECT,
            "prefix": "tst",
            "regime": "IL5",
            "region": "us-east4",
            "domain": DOMAIN,
            "customer_id": CUSTOMER_ID,
        }
        values.update(overrides)
        # An empty tuple stays, so a test can model answers.yaml with an
        # empty list.
        values = {
            key: value
            for key, value in values.items()
            if value or value is False or value == ()
        }
        return checks.Context(
            inputs=inputs_lib.PreflightInputs.model_validate(values),
            cloud=cloud,
            tools=local_tools,
            repo=repo,
            environ=environ or {},
        )

    return factory
