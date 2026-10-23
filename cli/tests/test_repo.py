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

import re

import pytest

import conftest
from stellar_engine import repo as repo_lib
from stellar_engine.preflight import checks
from stellar_engine.preflight import regions

_DDG_ROLE_RE = re.compile(r"\((roles/[a-zA-Z.]+)\)")


def _ddg_prerequisites(root):
    text = (root / "docs/ddg.md").read_text(encoding="utf-8")
    start = text.index("## Prerequisites")
    return text[start : text.index("\n## ", start + 1)]


def _slug(heading):
    slug = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return slug.replace(" ", "-")


def test_find_root_from_nested_directory(repo):
    nested = repo.root / "fast/stages-aw/0-bootstrap"
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
    resman = (repo.root / "fast/stages-aw/1-resman/variables.tf").read_text(
        encoding="utf-8"
    )
    assert repo.prefix_max_length() == 7
    assert "Use a maximum of 7 characters for prefix." in resman


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


def _write_stage0(root, organization_iam):
    bootstrap = root / repo_lib.BOOTSTRAP_DIR
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
    path, anchor = doc.split("#")
    text = (conftest.REPO_ROOT / path).read_text(encoding="utf-8")
    slugs = {
        _slug(line.lstrip("#"))
        for line in text.splitlines()
        if line.startswith("#")
    }
    assert anchor in slugs, f"{doc} has no matching heading"
