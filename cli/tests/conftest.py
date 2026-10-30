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
import itertools
import pathlib
import shutil
import stat
import subprocess

import pytest
from typer import testing

from stellar_engine import iam_diff
from stellar_engine import repo as repo_lib
from stellar_engine import tools as tools_lib
from stellar_engine.gcp import api
from stellar_engine.gcp import live
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
ETAG = "BwYAAAAAAAA="


def empty_policy():
    """Returns an IAM policy without bindings in the gcloud JSON shape."""
    return {"version": 1, "etag": ETAG, "bindings": []}


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
    """In-memory `CloudApi` and `CloudWriter` with a healthy default state.

    Tests change one field to model one failure. A field holding an
    exception instance makes the matching method raise it. Writer methods
    append `(method, *args)` to `writes`, raise the exception that
    `write_errors` holds for their name, and otherwise change the fields
    that the readers return, so a check after a write sees it.
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
    # The organization IAM policy in the gcloud JSON shape.
    policy: object = dataclasses.field(default_factory=empty_policy)
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
    adc: object = dataclasses.field(
        default_factory=lambda: api.AdcInfo(api.PrincipalKind.USER, PROJECT)
    )
    # The effective gcp.restrictServiceUsage of every resource; the
    # default has no rules, so it allows every service.
    restriction: api.ServiceRestriction | Exception = dataclasses.field(
        default_factory=api.ServiceRestriction
    )
    # Workload name to WorkloadInfo.
    workloads: dict = dataclasses.field(default_factory=dict)
    # `(bucket, name, impersonate)` or `(bucket, name)` to ObjectData; the
    # longer key wins, so a test can model a read only one identity has.
    objects: dict = dataclasses.field(default_factory=dict)
    # The billing account IAM policy in the gcloud JSON shape.
    billing_policy: object = dataclasses.field(default_factory=empty_policy)
    # What `service_accounts` returns for every project.
    accounts: object = dataclasses.field(default_factory=list)
    # What `gcs_service_agent` returns; None derives it from the project.
    gcs_agent: object = None
    calls: list = dataclasses.field(default_factory=list)
    writes: list = dataclasses.field(default_factory=list)
    write_errors: dict = dataclasses.field(default_factory=dict)

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

    def get_org_iam_policy(self, org_id):
        return iam_diff.Policy.from_json(self._value(self.policy))

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

    def adc_info(self):
        return self._value(self.adc)

    def effective_service_restriction(self, resource):
        return self._value(self.restriction)

    def assured_workload(self, name):
        return self._value(self.workloads.get(name))

    def read_object(self, bucket, name, *, impersonate=None):
        self.calls.append(("read_object", bucket, name, impersonate))
        key = (bucket, name, impersonate)
        if key not in self.objects:
            key = (bucket, name)
        return self._value(self.objects.get(key))

    def billing_account_iam(self, account_id):
        return iam_diff.Policy.from_json(self._value(self.billing_policy))

    def service_accounts(self, project_id):
        return self._value(self.accounts)

    def gcs_service_agent(self, project_id):
        if self.gcs_agent is None:
            domain = "gs-project-accounts.iam.gserviceaccount.com"
            return f"service-{project_id}@{domain}"
        return self._value(self.gcs_agent)

    def _write(self, method, *args):
        self.writes.append((method, *args))
        error = self.write_errors.get(method)
        if error is not None:
            raise error

    def set_org_iam_policy(self, org_id, policy, *, etag, update_mask):
        self._write("set_org_iam_policy", org_id, policy, etag, update_mask)
        current = self._value(self.policy)
        if etag != current.get("etag"):
            raise api.ConflictError("The policy changed since the read.")
        self.policy = {
            **policy.to_json(),
            "version": 3,
            "etag": f"{ETAG}{len(self.writes)}",
        }
        return iam_diff.Policy.from_json(self.policy)

    def enable_services(self, project_id, services):
        self._write("enable_services", project_id, tuple(services))
        if self.services is not None:
            self.services = {*self._value(self.services), *services}

    def restrict_allowed_resources(self, name):
        self._write("restrict_allowed_resources", name)
        workload = self.workloads.get(name)
        if workload is None or isinstance(self.restriction, Exception):
            return
        allowed = {
            *self.restriction.allowed,
            *workload.compliant_but_disallowed,
        }
        self.restriction = dataclasses.replace(
            self.restriction, allowed=tuple(sorted(allowed))
        )
        self.workloads[name] = dataclasses.replace(
            workload, compliant_but_disallowed=()
        )

    def add_billing_account_binding(self, account_id, role, member):
        self._write("add_billing_account_binding", account_id, role, member)
        policy = iam_diff.Policy.from_json(self._value(self.billing_policy))
        key = iam_diff.BindingKey(role)
        bindings = dict(policy.bindings)
        bindings[key] = bindings.get(key, frozenset()) | {member}
        self.billing_policy = dataclasses.replace(
            policy, bindings=bindings
        ).to_json()

    def generate_service_identity(self, project_id, service):
        self._write("generate_service_identity", project_id, service)
        name = service.split(".")[0]
        return f"service-{project_id}@gcp-sa-{name}.iam.gserviceaccount.com"


@dataclasses.dataclass
class FakeTerraform:
    """In-memory `terraform.runner.Runner` with scripted results.

    `results` maps a subcommand, the words before the first flag such as
    `plan` or `state pull`, to the results of its calls in order: a
    CompletedProcess to return or an exception to raise. A call without a
    scripted result succeeds with empty output. Every call appends its
    arguments and the sorted names of its environment to `calls`, and
    writes its output to the log file as the real runner does: `run` the
    merged output, `capture` stderr only.
    """

    results: dict = dataclasses.field(default_factory=dict)
    calls: list = dataclasses.field(default_factory=list)

    @staticmethod
    def subcommand(args):
        """Returns the words of the arguments before the first flag."""
        words = itertools.takewhile(lambda arg: not arg.startswith("-"), args)
        return " ".join(words)

    def run(self, workspace, args, *, env, log, timeout):
        result = self._call(workspace, args, env)
        self._log(log, result.stdout, result.returncode)
        return result

    def capture(self, workspace, args, *, env, log, timeout):
        result = self._call(workspace, args, env)
        self._log(log, result.stderr, result.returncode)
        return result

    def _call(self, workspace, args, env):
        self.calls.append((tuple(args), tuple(sorted(env))))
        scripted = self.results.get(self.subcommand(args)) or []
        result = scripted.pop(0) if scripted else None
        if isinstance(result, Exception):
            raise result
        if result is None:
            argv = ["terraform", f"-chdir={workspace}", *args]
            result = subprocess.CompletedProcess(argv, 0, "", "")
        return result

    @staticmethod
    def _log(log, text, returncode):
        log = pathlib.Path(log)
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(text or "")
            handle.write(f"# exit status {returncode}\n")
        log.chmod(0o600)


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
def isolated_home(tmp_path, monkeypatch):
    """Points every command at a temp home outside the repository.

    The command tests apply it to every test with
    `pytestmark = pytest.mark.usefixtures("isolated_home")`.
    """
    home = tmp_path / "home"
    monkeypatch.setenv("STELLAR_HOME", str(home))
    monkeypatch.delenv("STELLAR_PREFIX", raising=False)
    return home


@pytest.fixture
def cli_runner():
    """Returns a CliRunner for the `stellar` app."""
    return testing.CliRunner()


@pytest.fixture
def fake_tools(monkeypatch):
    """Makes the commands use FakeTools instead of the local binaries."""
    monkeypatch.setattr(tools_lib, "SystemTools", FakeTools)


@pytest.fixture
def fake_cloud(cloud, fake_tools, monkeypatch):
    """Makes the commands use the `cloud` fixture and FakeTools.

    Returns:
        The FakeCloud that the commands use.
    """
    del fake_tools  # Only its patch matters.
    monkeypatch.setattr(live, "LiveCloudApi", lambda: cloud)
    monkeypatch.delenv("GOOGLE_IMPERSONATE_SERVICE_ACCOUNT", raising=False)
    return cloud


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
