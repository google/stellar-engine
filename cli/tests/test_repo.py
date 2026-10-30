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

"""Sync tests that keep the CLI aligned with the repository and the DDG.

These tests read the real checkout. When one fails, the repository changed in
a way the CLI must follow, or the documentation drifted from the code.
"""

import json
import re
import shutil
import subprocess

import pytest

import conftest
import helpers
from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.preflight import checks
from stellar_engine.preflight import regions
from stellar_engine.render import hcl

_DDG_ROLE_RE = re.compile(r"\((roles/[a-zA-Z.]+)\)")


def _ddg_prerequisites(root):
    text = (root / "docs/ddg.md").read_text(encoding="utf-8")
    start = text.index("## Prerequisites")
    return text[start : text.index("\n## ", start + 1)]


def test_find_root_from_nested_directory(repo):
    nested = repo.bootstrap_dir
    assert repo_lib.find_root(nested) == repo.root


def test_find_root_outside_checkout(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_lib, "__file__", str(tmp_path / "repo.py"))
    with pytest.raises(repo_lib.RepoError):
        repo_lib.find_root(tmp_path)


def test_required_roles_match_ddg(repo):
    ddg_roles = set(_DDG_ROLE_RE.findall(_ddg_prerequisites(repo.root)))
    script_roles = set(repo.required_roles())
    assert ddg_roles, "No roles found in the DDG prerequisites section"
    # setIAM.yaml.sample also grants projectDeleter, which the DDG documents
    # in docs/prerequisites.md rather than in its role list.
    assert script_roles - ddg_roles == {"roles/resourcemanager.projectDeleter"}
    assert ddg_roles <= script_roles


def test_required_apis(repo):
    apis = repo.required_apis()
    assert {"cloudresourcemanager.googleapis.com"} <= set(apis)
    assert all(api.endswith(".googleapis.com") for api in apis)


def test_prerequisites_doc_lists_every_script_api(repo):
    text = (repo.root / "docs/prerequisites.md").read_text(encoding="utf-8")
    for api in repo.required_apis():
        assert f"`{api}`" in text


def test_ddg_requires_monitoring_api(repo):
    assert "/apis/api/monitoring.googleapis.com/overview" in _ddg_prerequisites(
        repo.root
    )
    assert checks.EXTRA_APIS == ("monitoring.googleapis.com",)


def test_prefix_limit_matches_resman(repo):
    resman = (
        paths.stage_dir(repo.root, paths.RESMAN) / "variables.tf"
    ).read_text(encoding="utf-8")
    assert repo.prefix_max_length() == 7
    assert "Use a maximum of 7 characters for prefix." in resman


def test_tenant_key_limit_matches_resman(repo):
    variables = (
        paths.stage_dir(repo.root, paths.RESMAN) / "variables.tf"
    ).read_text(encoding="utf-8")
    assert repo.tenant_key_max_length() == 6
    assert "Tenant keys must be less than 7 characters." in variables


@pytest.mark.parametrize(
    ("condition", "limit"),
    [("length(k) < 9", 8), ("length(k) <= 9", 9)],
)
def test_tenant_key_limit_reads_both_bounds(tmp_path, condition, limit):
    resman = paths.stage_dir(tmp_path, paths.RESMAN)
    resman.mkdir(parents=True)
    (resman / "variables.tf").write_text(
        'variable "tenants" {\n  validation {\n'
        f"    condition = alltrue([for k, _ in var.tenants : {condition}])\n"
        "  }\n}\n",
        encoding="utf-8",
    )
    assert repo_lib.Repo(tmp_path).tenant_key_max_length() == limit


def test_tenant_key_limit_missing_raises(tmp_path):
    resman = paths.stage_dir(tmp_path, paths.RESMAN)
    resman.mkdir(parents=True)
    (resman / "variables.tf").write_text("", encoding="utf-8")
    with pytest.raises(repo_lib.RepoError):
        repo_lib.Repo(tmp_path).tenant_key_max_length()


def test_default_groups(repo):
    groups = repo.default_groups()
    assert groups["gcp-support"] == "gcp-devops"
    assert {
        "gcp-billing-admins",
        "gcp-devops",
        "gcp-organization-admins",
        "gcp-security-admins",
        "gcp-vpc-network-admins",
    } <= set(groups.values())


def test_log_sinks_and_custom_resources(repo):
    assert "audit-logs" in repo.log_sink_names()
    assert "storage_viewer" in repo.custom_role_ids()
    assert "custom.kmsRotation" in repo.custom_constraint_names()


# The pattern `0-bootstrap/import.sh` greps for a declared constraint.
_IMPORT_SH_KEY_RE = re.compile(r"^([^\s#:%-][^:\s]*):", re.MULTILINE)


def _import_sh_keys(repo):
    keys = set()
    for directory in ("data/org-policies", "data/custom-org-policies"):
        for path in (repo.bootstrap_dir / directory).rglob("*"):
            if path.is_file():
                keys.update(_IMPORT_SH_KEY_RE.findall(path.read_text()))
    return keys


def test_declared_org_policies_match_import_sh(repo):
    declared = repo.declared_org_policies()
    assert declared == sorted(set(declared))
    assert set(declared) == _import_sh_keys(repo)


def test_declared_org_policies_read_templated_files(repo):
    declared = set(repo.declared_org_policies())
    # Keys from data/custom-org-policies, one behind a regime directive.
    assert {
        "iam.allowedPolicyMemberDomains",
        "compute.managed.restrictProtocolForwardingCreationForTypes",
        "gcp.resourceLocations",
    } <= declared
    # Keys from data/org-policies, including a custom constraint.
    assert {"compute.skipDefaultNetworkCreation", "custom.kmsRotation"} <= (
        declared
    )
    assert not any(name.startswith(("%", "-")) for name in declared)


def test_declared_org_policies_follow_the_file_pattern(tmp_path):
    bootstrap = paths.stage_dir(tmp_path, paths.BOOTSTRAP)
    plain = bootstrap / "data/org-policies"
    templated = bootstrap / "data/custom-org-policies"
    plain.mkdir(parents=True)
    templated.mkdir(parents=True)
    (plain / "a_policy.yaml").write_text("b.one:\n  rules: []\n")
    (plain / "notes.yaml").write_text("ignored.key: {}\n")
    (templated / "c_policy.yaml").write_text(
        "---\n# c.comment:\n%{ if x ~}\nc.two:\n  rules:\n"
        "  - allow:\n      values:\n        - ${v}\n%{ endif ~}\n"
    )
    repo = repo_lib.Repo(tmp_path)
    assert repo.declared_org_policies() == ["b.one", "c.two"]


def test_declared_org_policies_cover_import_defaults(repo):
    # The `import_defaults` import block in organization.tf lists the
    # policies of a new organization; the scan must keep each of them.
    text = (repo.bootstrap_dir / "organization.tf").read_text()
    block = text.split("var.org_policies_config.import_defaults", 1)[1]
    block = block.split(": toset([])", 1)[0]
    listed = re.findall(r'^\s*"([^"]+)",', block, re.MULTILINE)
    assert listed
    assert repo.scan_org_policies(listed).kept == tuple(sorted(listed))


def test_scan_org_policies(repo):
    scan = repo.scan_org_policies(
        [
            "storage.uniformBucketLevelAccess",
            "custom.kmsRotation",
            "unmanaged.constraint",
            "iam.allowedPolicyMemberDomains",
            "iam.allowedPolicyMemberDomains",
        ]
    )
    assert scan == repo_lib.OrgPolicyScan(
        kept=(
            "iam.allowedPolicyMemberDomains",
            "storage.uniformBucketLevelAccess",
        ),
        custom=("custom.kmsRotation",),
        undeclared=("unmanaged.constraint",),
    )


def test_scan_org_policies_treat_foreign_custom_as_undeclared(repo):
    scan = repo.scan_org_policies(["custom.kmsRotation", "custom.myOrgRule"])
    assert scan.custom == ("custom.kmsRotation",)
    assert scan.undeclared == ("custom.myOrgRule",)


_MODERATE_GATED = "compute.managed.restrictProtocolForwardingCreationForTypes"
_IL_GATED = "compute.requireOsLogin"


def test_declared_org_policies_follow_the_regime(repo):
    every = set(repo.declared_org_policies())
    moderate = set(repo.declared_org_policies("FEDRAMP_MODERATE"))
    assert set(repo.declared_org_policies("FEDRAMP_HIGH")) == every
    assert set(repo.declared_org_policies("IL4")) == every - {_IL_GATED}
    assert set(repo.declared_org_policies("IL5")) == every - {_IL_GATED}
    assert _MODERATE_GATED in every - moderate
    # The FedRAMP Moderate branch of an if and else pair still counts.
    assert "gcp.resourceLocations" in moderate
    scan = repo.scan_org_policies([_MODERATE_GATED], "FEDRAMP_MODERATE")
    assert scan.undeclared == (_MODERATE_GATED,)


def test_templated_keys_follow_regime_conditions():
    text = (
        '%{ if !contains(["A"], regime) ~}\nnot.a: 1\n%{ else ~}\n'
        'only.a: 1\n%{ endif ~}\n%{ if contains(["B", "C"], regime) ~}\n'
        "b.or.c: 1\n%{ endif ~}\n%{ if other ~}\nunknown: 1\n%{ endif ~}\n"
        "%{ for d in ds ~}\n- ${d}\n%{ endfor ~}\nalways: 1\n"
    )
    assert repo_lib._templated_keys(text, "A") == {
        "only.a",
        "unknown",
        "always",
    }
    assert repo_lib._templated_keys(text, "B") == {
        "not.a",
        "b.or.c",
        "unknown",
        "always",
    }
    assert repo_lib._templated_keys(text, None) == {
        "not.a",
        "only.a",
        "b.or.c",
        "unknown",
        "always",
    }


_TEMPLATE_VARS = (
    'organization_id = "1", domain_name = "example.com", '
    'customer_id = "C0", drs_tag_name = "x/y", allowed_domains = ["C0"]'
)


@pytest.mark.terraform
@pytest.mark.parametrize("regime", ["FEDRAMP_MODERATE", "IL5"])
def test_templated_keys_match_templatefile(repo, regime, tmp_path):
    # Sync test: Terraform renders the templated files the way
    # `local._org_policies_raw` does, and the keys must match ours.
    directory = repo.bootstrap_dir / "data/custom-org-policies"
    expression = (
        "jsonencode(sort(flatten([for f in fileset("
        f'"{directory}", "*_policy.yaml") : try(keys(yamldecode('
        f'templatefile("{directory}/${{f}}", {{{_TEMPLATE_VARS}, '
        f'regime = "{regime}"}}))), [])])))'
    )
    console = subprocess.run(
        ["terraform", f"-chdir={tmp_path}", "console", "-no-color"],
        input=expression,
        capture_output=True,
        text=True,
        check=False,
    )
    assert console.returncode == 0, console.stderr
    rendered = set(json.loads(json.loads(console.stdout)))
    ours = set()
    for path in directory.glob("*_policy.yaml"):
        ours |= repo_lib._templated_keys(path.read_text(), regime)
    assert rendered == ours


def test_authoritative_roles(repo):
    roles = repo.authoritative_org_roles()
    assert "roles/resourcemanager.organizationAdmin" in roles
    assert "roles/browser" in roles
    assert "roles/billing.creator" in roles
    assert "roles/orgpolicy.policyAdmin" not in roles


def test_conditional_bindings_keep_their_holders(repo):
    bindings = repo.authoritative_bindings()
    assert (
        repo_lib.Holder(repo_lib.HolderKind.DOMAIN)
        in (bindings["roles/browser"])
    )
    assert (
        repo_lib.Holder(repo_lib.HolderKind.BOOTSTRAP_USER)
        in (bindings["roles/logging.admin"])
    )


def test_audit_log_configs_follow_the_file(repo):
    assert repo.audit_log_configs() == {
        "allServices": [
            ("ADMIN_READ", ()),
            ("DATA_WRITE", ()),
            ("DATA_READ", ()),
        ]
    }


def _write_stage0(root, organization_iam):
    bootstrap = paths.stage_dir(root, paths.BOOTSTRAP)
    bootstrap.mkdir(parents=True)
    (bootstrap / "automation.tf").write_text(
        'module "automation-project" { source = "x"\n name = "iac-core-0" }\n'
        'module "automation-tf-bootstrap-sa" {\n'
        '  source = "x"\n  iam = { "roles/x" = [] }\n  name = "bootstrap-0"\n'
        "}\n"
    )
    (bootstrap / "organization-iam.tf").write_text(organization_iam)
    module = root / "modules/project"
    module.mkdir(parents=True)
    (module / "versions.tf").write_text(
        'terraform { required_version = ">= 1.11.0, < 2.0.0" }\n'
    )
    return repo_lib.Repo(root)


def test_parsing_ignores_layout(tmp_path):
    fake = _write_stage0(
        tmp_path,
        "locals {\n"
        '  iam_delete_roles = ["roles/billing.creator"]\n'
        "  iam_sa_bindings = { (module.automation-tf-bootstrap-sa.iam_email)"
        ' = { additive = [], authoritative = ["roles/owner"] } }\n'
        "  iam_user_bootstrap_bindings = var.bootstrap_user == null ? {} : {\n"
        '    "user:${var.bootstrap_user}" = {\n'
        "      authoritative = [\n"
        '        "roles/logging.admin"]\n'
        "    }\n"
        "  }\n"
        "}\n",
    )
    assert fake.automation_service_accounts() == {
        "automation-tf-bootstrap-sa": "bootstrap-0"
    }
    assert fake.authoritative_bindings() == {
        "roles/billing.creator": set(),
        "roles/logging.admin": {
            repo_lib.Holder(repo_lib.HolderKind.BOOTSTRAP_USER)
        },
        "roles/owner": {
            repo_lib.Holder(repo_lib.HolderKind.SERVICE_ACCOUNT, "bootstrap-0")
        },
    }
    assert fake.min_terraform_version() == "1.11.0"


def test_unknown_principal_raises(tmp_path):
    fake = _write_stage0(
        tmp_path,
        'locals {\n  iam_x_bindings = { "group:x@example.com" = {'
        ' authoritative = ["roles/owner"] } }\n}\n',
    )
    with pytest.raises(repo_lib.RepoError, match="Unknown principal"):
        fake.authoritative_bindings()


def test_min_terraform_version(repo):
    floor = repo.min_terraform_version()
    assert re.fullmatch(r"\d+\.\d+\.\d+", floor)
    assert tuple(int(part) for part in floor.split(".")) >= (1, 10, 2)


def test_regimes_exist_in_stage0_mapping(repo):
    names = repo.regime_names()
    assert "CJIS" in names
    assert {regime.value for regime in regions.Regime} <= set(names)


@pytest.mark.parametrize(
    "doc",
    sorted(
        {
            value
            for name, value in vars(checks).items()
            if name.startswith(("DOC_", "DDG_")) and "#" in value
        }
    ),
)
def test_doc_links_resolve(doc):
    assert helpers.doc_resolves(doc), f"{doc} has no matching heading"


def test_stage0_projects(repo):
    projects = repo.stage0_projects()
    assert [project.name for project in projects] == [
        "iac-core-0",
        "audit-logs-0",
        "billing-exp-0",
    ]
    assert [project.module for project in projects] == [
        "automation-project",
        "log-export-project",
        repo_lib.BILLING_EXPORT_MODULE,
    ]
    assert repo.stage0_project_names() == [p.name for p in projects]


@pytest.mark.parametrize(
    ("no_iam", "is_org_level", "expected"),
    [(False, True, True), (True, True, False), (False, False, False)],
)
def test_stage0_project_created_follows_billing_mode(
    repo, no_iam, is_org_level, expected
):
    automation, _, billing_export = repo.stage0_projects()
    flags = {"no_iam": no_iam, "is_org_level": is_org_level}
    assert repo_lib.stage0_project_created(automation, **flags)
    assert repo_lib.stage0_project_created(billing_export, **flags) is expected


def _bootstrap_blocks(repo, kind):
    """Yields each module or resource in Stage 0 as (file, label, body)."""
    for path in sorted(repo.bootstrap_dir.glob("*.tf")):
        for block in repo_lib._load_hcl(path).get(kind, []):
            for label, body in block.items():
                if kind == "resource":
                    for name, resource in body.items():
                        yield path.name, (label, name), resource
                else:
                    yield path.name, label, body


def test_assured_workload(repo):
    workload = repo.assured_workload()
    assert workload.address == "google_assured_workloads_workload.primary[0]"
    assert workload.skipped_regime == "COMPLIANCE_REGIME_UNSPECIFIED"
    assert workload.created("IL5")
    assert not workload.created("COMPLIANCE_REGIME_UNSPECIFIED")
    # organization.tf ignores billing_account and resource_settings and
    # leaves provisioned_resources_parent empty.
    assert workload.replaced_on_import == ()


def _write_workload(tmp_path, lifecycle):
    """Writes a Stage 0 organization.tf with one workload resource."""
    stage = tmp_path / paths.STAGES_DIR / paths.BOOTSTRAP
    stage.mkdir(parents=True)
    (stage / "organization.tf").write_text(
        'resource "google_assured_workloads_workload" "primary" {\n'
        '  billing_account              = "billingAccounts/x"\n'
        '  provisioned_resources_parent = "folders/1"\n'
        "  resource_settings {\n"
        '    resource_type = "CONSUMER_FOLDER"\n'
        "  }\n"
        f"  {lifecycle}\n"
        "}\n",
        encoding="utf-8",
    )
    return repo_lib.Repo(tmp_path)


def test_assured_workload_without_ignore_changes(tmp_path):
    workload = _write_workload(tmp_path, "").assured_workload()
    assert workload.replaced_on_import == repo_lib.WORKLOAD_INPUT_ONLY


def test_assured_workload_ignoring_input_only_arguments(tmp_path):
    fields = ", ".join(repo_lib.WORKLOAD_INPUT_ONLY)
    workload = _write_workload(
        tmp_path, f"lifecycle {{\n    ignore_changes = [{fields}]\n  }}"
    ).assured_workload()
    assert workload.replaced_on_import == ()


def test_no_compliance_folder_address(repo):
    address = repo.no_compliance_folder_address()
    assert address == "module.no-compliance-folder[0]"


def test_no_compliance_folder_address_requires_the_module(tmp_path):
    repo = _write_workload(tmp_path, "")
    with pytest.raises(repo_lib.RepoError, match="no-compliance-folder"):
        repo.no_compliance_folder_address()


def _git(root, *args):
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        capture_output=True,
        check=True,
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git is missing")
def test_provenance(tmp_path):
    root = tmp_path / "engine"
    root.mkdir()
    _git(root, "init", "-q")
    (root / "main.tf").write_text("# engine\n", encoding="utf-8")
    _git(root, "add", "main.tf")
    _git(root, "commit", "-q", "-m", "engine")
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()
    repo = repo_lib.Repo(root)
    assert repo.provenance() == repo_lib.Provenance(head, dirty=False)
    (root / "new.tf").write_text("# untracked\n", encoding="utf-8")
    assert repo.provenance() == repo_lib.Provenance(head, dirty=True)


@pytest.mark.skipif(shutil.which("git") is None, reason="git is missing")
def test_provenance_outside_a_checkout(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    assert repo_lib.Repo(tmp_path).provenance() is None


def test_provenance_without_git(tmp_path, monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(repo_lib.subprocess, "run", missing)
    assert repo_lib.Repo(tmp_path).provenance() is None


def test_assured_workload_matches_organization_tf(repo):
    # The pre-creation advice names these attributes, so the import of a
    # workload created by hand plans no replacement.
    (body,) = [
        body
        for filename, (label, _), body in _bootstrap_blocks(repo, "resource")
        if filename == "organization.tf"
        and hcl.unquote(label) == repo_lib.WORKLOAD_RESOURCE
    ]
    folder = naming.workload_folder_name("${var.prefix}")
    assert hcl.unquote(body["display_name"]) == folder
    (settings,) = body["resource_settings"]
    assert hcl.unquote(settings["display_name"]) == folder
    assert hcl.unquote(settings["resource_type"]) == "CONSUMER_FOLDER"
    assert body["violation_notifications_enabled"] is True
    assert "var.billing_account.id" in body["billing_account"]


def test_billing_resources_cover_every_billing_account_use(repo):
    # Every Stage 0 module or resource that reads the billing account ID
    # needs billing access. Preflight lists the ones to pre-create, and
    # reports the budget and the billing account IAM, which nothing
    # pre-created replaces.
    passing = set()
    for _, label, body in _bootstrap_blocks(repo, "module"):
        if "var.billing_account.id" in str(body):
            passing.add(f"module.{hcl.unquote(label)}")
    account_iam = set()
    for _, (kind, name), body in _bootstrap_blocks(repo, "resource"):
        if "var.billing_account.id" not in str(body):
            continue
        address = f"{hcl.unquote(kind)}.{hcl.unquote(name)}"
        if hcl.unquote(kind) == "google_billing_account_iam_member":
            account_iam.add(address)
        else:
            passing.add(address)
    assert account_iam
    budget = f"module.{repo_lib.BUDGET_MODULE}"
    assert budget in passing
    passing.discard(budget)
    resources = repo.billing_resources(
        prefix="abc",
        regime="IL5",
        location="us-east4",
        no_iam=False,
        is_org_level=True,
    )
    listed = {
        item.address.split(".google_project.")[0].removesuffix("[0]")
        if item.kind == repo_lib.BillingResourceKind.PROJECT
        else item.address.removesuffix("[0]")
        for item in resources
    }
    assert listed == passing
    assert {
        f"module.{project.module}" for project in repo.stage0_projects()
    } < passing


@pytest.mark.parametrize(
    ("no_iam", "is_org_level", "names"),
    [
        (
            False,
            True,
            [
                "abc-prod-iac-core-0",
                "abc-prod-audit-logs-0",
                "abc-prod-billing-exp-0",
            ],
        ),
        (True, True, ["abc-prod-iac-core-0", "abc-prod-audit-logs-0"]),
        (False, False, ["abc-prod-iac-core-0", "abc-prod-audit-logs-0"]),
    ],
)
def test_billing_resources_follow_billing_answers(
    repo, no_iam, is_org_level, names
):
    resources = repo.billing_resources(
        prefix="abc",
        regime="IL5",
        location="us-east4",
        no_iam=no_iam,
        is_org_level=is_org_level,
        org_id=conftest.ORG_ID,
    )
    projects = [
        item
        for item in resources
        if item.kind == repo_lib.BillingResourceKind.PROJECT
    ]
    assert [item.name for item in projects] == names
    assert [item.address for item in projects] == [
        project.address
        for project in repo.created_stage0_projects(
            no_iam=no_iam, is_org_level=is_org_level
        )
    ]
    assert all(item.import_id == item.name for item in projects)
    workload = resources[-1]
    assert workload.kind == repo_lib.BillingResourceKind.WORKLOAD
    assert workload.address == repo.assured_workload().address
    assert workload.name == "StellarEngine-abc"
    assert workload.import_id == (
        f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/"
        "<workload_id>"
    )
    assert "IL5" in workload.create
    assert "us-east4" in workload.create


def test_billing_resources_skip_the_workload_without_a_regime(repo):
    resources = repo.billing_resources(
        prefix="abc",
        regime="COMPLIANCE_REGIME_UNSPECIFIED",
        location="us-east4",
        no_iam=True,
        is_org_level=True,
    )
    assert [item.kind for item in resources] == [
        repo_lib.BillingResourceKind.PROJECT,
        repo_lib.BillingResourceKind.PROJECT,
    ]


def test_budget_module_follows_the_budget_variable(repo):
    # Preflight treats the budget.amount answer as a use of the billing
    # account, because Stage 0 creates this module only for that variable.
    (body,) = [
        body
        for filename, label, body in _bootstrap_blocks(repo, "module")
        if hcl.unquote(label) == repo_lib.BUDGET_MODULE
    ]
    assert "var.billing_budget_amount != null" in str(body["count"])
    assert "var.billing_account.id" in str(body["id"])


@pytest.mark.parametrize(
    ("no_iam", "is_org_level", "expected"),
    [(False, True, False), (True, False, False), (False, False, True)],
)
def test_billing_iam_on_account_follows_billing_mode(
    repo, no_iam, is_org_level, expected
):
    # `google_billing_account_iam_member` in billing.tf exists only in the
    # "resource" billing mode.
    text = (repo.bootstrap_dir / "billing.tf").read_text(encoding="utf-8")
    assert 'local.billing_mode == "resource"' in text
    assert (
        repo_lib.billing_iam_on_account(
            no_iam=no_iam, is_org_level=is_org_level
        )
        is expected
    )


def test_assured_workload_requires_one_resource(tmp_path):
    stage = tmp_path / paths.STAGES_DIR / paths.BOOTSTRAP
    stage.mkdir(parents=True)
    (stage / "organization.tf").write_text("", encoding="utf-8")
    with pytest.raises(repo_lib.RepoError, match="Expected one"):
        repo_lib.Repo(tmp_path).assured_workload()


_LAYOUT_TF = """\
locals {
  a = 1
}
locals {
  b = "c"
}
variable "first" {
  default = "x"
}
variable "second" {}
module "one" {
  source = "./one"
}
module "two" {
  source = "./two"
}
resource "google_project" "main" {}
resource "google_folder" "skipped" {}
resource "google_project" "other" {
  count = 1
}
"""


def test_hcl_helpers_merge_filter_and_unquote(tmp_path):
    path = tmp_path / "main.tf"
    path.write_text(_LAYOUT_TF, encoding="utf-8")
    found_locals = repo_lib._locals(path)
    assert (found_locals["a"], found_locals["b"]) == (1, '"c"')
    assert list(repo_lib._variables(path)) == ["first", "second"]
    assert [label for label, _ in repo_lib._modules(path)] == ["one", "two"]
    assert [
        (name, body.get("count"))
        for name, body in repo_lib._resources(path, "google_project")
    ] == [("main", None), ("other", 1)]


def test_hcl_helpers_read_stage0(repo):
    bootstrap = repo.bootstrap_dir
    assert {"tfvars", "tfvars_globals"} <= set(
        repo_lib._locals(bootstrap / "outputs.tf")
    )
    iam_locals = repo_lib._locals(bootstrap / "organization-iam.tf")
    assert {"iam_delete_roles", "iam_sa_bindings"} <= set(iam_locals)
    variables = repo_lib._variables(bootstrap / "variables.tf")
    assert {"prefix", repo_lib.PROJECT_DELETION_POLICIES} <= set(variables)
    ((workload, _),) = repo_lib._resources(
        bootstrap / "organization.tf", repo_lib.WORKLOAD_RESOURCE
    )
    assert workload == "primary"


def test_hcl_helpers_cover_every_stage0_block(repo):
    files = sorted(repo.bootstrap_dir.glob("*.tf"))
    modules = [
        (path.name, label)
        for path in files
        for label, _ in repo_lib._modules(path)
    ]
    assert modules == [
        (filename, hcl.unquote(label))
        for filename, label, _ in _bootstrap_blocks(repo, "module")
    ]
    expected = sorted(
        (filename, hcl.unquote(kind), hcl.unquote(name))
        for filename, (kind, name), _ in _bootstrap_blocks(repo, "resource")
    )
    kinds = {kind for _, kind, _ in expected}
    resources = sorted(
        (path.name, kind, name)
        for path in files
        for kind in kinds
        for name, _ in repo_lib._resources(path, kind)
    )
    assert resources == expected
