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

"""Tests for derived values, including sync tests against the stage code."""

import re

import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine.config import derive


def _with_tenant(tenant="ten1", **info):
    info.setdefault("descriptive_name", "Tenant")
    return helpers.minimal_answers(resman={"tenants": {tenant: info}})


@pytest.mark.parametrize(
    ("regime", "level"),
    [
        ("FEDRAMP_MODERATE", "SOFTWARE"),
        ("FEDRAMP_HIGH", "HSM"),
        ("IL4", "HSM"),
        ("IL5", "HSM"),
        ("COMPLIANCE_REGIME_UNSPECIFIED", "HSM"),
    ],
)
def test_kms_protection_level_follows_regime(regime, level):
    answers = helpers.minimal_answers(compliance={"regime": regime})
    assert derive.kms_protection_level(answers) == level


def test_explicit_kms_protection_level_wins():
    answers = helpers.minimal_answers(
        compliance={"regime": "IL5"}, kms_protection_level="SOFTWARE"
    )
    assert derive.kms_protection_level(answers) == "SOFTWARE"


def test_kms_rule_matches_stage0(repo):
    kms = (repo.bootstrap_dir / "kms.tf").read_text(encoding="utf-8")
    assert (
        "kms_protection_level = coalesce(var.kms_protection_level, "
        'var.assured_workloads.regime == "FEDRAMP_MODERATE" ? "SOFTWARE" '
        ': "HSM")'
    ) in kms


def test_compliance_location_defaults_to_region():
    assert derive.compliance_location(helpers.minimal_answers()) == "us-east4"
    answers = helpers.minimal_answers(
        compliance={"regime": "IL5", "location": "us"}
    )
    assert derive.compliance_location(answers) == "us"


def test_group_names_and_principals(repo):
    answers = helpers.minimal_answers(
        groups={
            "gcp-devops": "platform-team",
            "gcp-security-admins": "user:sec@example.com",
        }
    )
    assert derive.group_name(answers, repo, "gcp-devops") == "platform-team"
    assert (
        derive.group_name(answers, repo, "gcp-billing-admins")
        == "gcp-billing-admins"
    )
    assert (
        derive.group_principal(answers, repo, "gcp-devops")
        == f"group:platform-team@{conftest.DOMAIN}"
    )
    assert (
        derive.group_principal(answers, repo, "gcp-security-admins")
        == "user:sec@example.com"
    )
    assert (
        derive.group_email(answers, repo, "gcp-security-admins")
        == "sec@example.com"
    )


def test_unknown_group_key_raises(repo):
    with pytest.raises(KeyError):
        derive.group_name(helpers.minimal_answers(), repo, "gcp-unknown")


def test_group_principal_rule_matches_stage0(repo):
    main = (repo.bootstrap_dir / "main.tf").read_text(encoding="utf-8")
    assert 'can(regex("^[a-zA-Z]+:", v))' in main
    assert '"group:${v}@${var.organization.domain}"' in main


def test_env_admin(repo):
    answers = helpers.minimal_answers(
        resman={"envs": {"Prod": {"admin": "prod@example.com"}, "Dev": {}}}
    )
    assert derive.env_admin(answers, repo, "Prod") == "prod@example.com"
    assert (
        derive.env_admin(answers, repo, "Dev")
        == f"gcp-organization-admins@{conftest.DOMAIN}"
    )


def test_tenant_admin(repo):
    assert (
        derive.tenant_admin(_with_tenant(), repo, "ten1")
        == f"group:gcp-devops@{conftest.DOMAIN}"
    )
    answers = _with_tenant(admin_principal="group:t1@example.com")
    assert derive.tenant_admin(answers, repo, "ten1") == "group:t1@example.com"


def test_admin_defaults_match_resman_sample(repo):
    sample = (
        paths.stage_dir(repo.root, paths.RESMAN) / "terraform.tfvars.sample"
    ).read_text(encoding="utf-8")
    assert 'admin = "gcp-organization-admins@<domain>"' in sample
    assert 'admin_principal  = "group:gcp-devops@<domain>"' in sample


def test_tenant_locations():
    assert derive.tenant_locations(_with_tenant(), "ten1") == {
        "gcs": "us-east4",
        "kms": "us-east4",
    }
    answers = _with_tenant(locations={"gcs": "us", "kms": "us-east1"})
    assert derive.tenant_locations(answers, "ten1") == {
        "gcs": "us",
        "kms": "us-east1",
    }


def _stage0_project_ids(answers, repo):
    return list(derive.stage0_deletion_policies(answers, repo))


def test_stage0_project_ids(repo):
    assert _stage0_project_ids(helpers.minimal_answers(), repo) == [
        "tst-prod-iac-core-0",
        "tst-prod-audit-logs-0",
        "tst-prod-billing-exp-0",
    ]


@pytest.mark.parametrize("billing", [{"no_iam": True}, {"is_org_level": False}])
def test_stage0_project_ids_skip_billing_export(repo, billing):
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, **billing}
    )
    assert _stage0_project_ids(answers, repo) == [
        "tst-prod-iac-core-0",
        "tst-prod-audit-logs-0",
    ]


def test_tenant_project_ids_lowercase_env_keys():
    answers = helpers.minimal_answers(
        resman={
            "envs": {"Prod": {}, "Int": {}},
            "tenants": {"ten1": {"descriptive_name": "Tenant"}},
        }
    )
    assert derive.tenant_project_ids(answers) == {
        "ten1": [
            "tst-prod-ten1-iac-core-0",
            "tst-prod-ten1-main-0",
            "tst-int-ten1-iac-core-0",
            "tst-int-ten1-main-0",
        ]
    }
    assert derive.tenant_service_account_ids(answers) == {
        "ten1": [
            "tst-tn-prod-ten1-prod-0",
            "tst-prod-ten1-iac-0",
            "tst-tn-int-ten1-prod-0",
            "tst-int-ten1-iac-0",
        ]
    }


def test_tenant_id_formats_match_resman(repo):
    tenants = (
        paths.stage_dir(repo.root, paths.RESMAN) / "branch-tenants.tf"
    ).read_text(encoding="utf-8")
    for fragment in (
        '"${e}-${t}" => {',
        'name   = lower("${each.key}-iac-core-0")',
        'name   = lower("${each.key}-main-0")',
        'name        = lower("tn-${each.key}-prod-0")',
        'name        = lower("${each.key}-iac-0")',
    ):
        assert fragment in tenants
    assert len(re.findall(r"prefix\s+= var\.prefix", tenants)) >= 4


def test_no_tenants_no_ids():
    assert derive.tenant_project_ids(helpers.minimal_answers()) == {}
