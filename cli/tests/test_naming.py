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

"""Tests for the names that mirror the stage code."""

import pytest

from stellar_engine import naming


def _bootstrap_text(repo, name):
    return (repo.bootstrap_dir / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("regime", "explicit", "expected"),
    [
        ("FEDRAMP_MODERATE", None, "SOFTWARE"),
        ("IL5", None, "HSM"),
        ("", None, "HSM"),
        ("FEDRAMP_MODERATE", "HSM", "HSM"),
    ],
)
def test_kms_protection_level(regime, explicit, expected):
    assert naming.kms_protection_level(regime, explicit) == expected


def test_kms_rule_matches_stage0(repo):
    assert (
        'regime == "FEDRAMP_MODERATE" ? "SOFTWARE" : "HSM"'
        in _bootstrap_text(repo, "kms.tf")
    )


def test_stage0_names():
    assert (
        naming.stage0_project_id("tst", "iac-core-0") == "tst-prod-iac-core-0"
    )
    assert naming.automation_sa_email("tst", "bootstrap-0") == (
        "tst-prod-bootstrap-0@tst-prod-iac-core-0.iam.gserviceaccount.com"
    )
    assert [
        naming.state_bucket("tst", name) for name in naming.STATE_BUCKET_NAMES
    ] == [
        "tst-prod-iac-core-bootstrap-0",
        "tst-prod-iac-core-outputs-0",
        "tst-prod-iac-core-resman-0",
    ]


def test_stage0_names_match_automation(repo):
    main = _bootstrap_text(repo, "main.tf")
    assert 'prefix = join("-", compact([var.prefix, "prod"]))' in main
    automation = _bootstrap_text(repo, "automation.tf")
    assert f'name                    = "{naming.AUTOMATION_PROJECT_NAME}"' in (
        automation
    )
    for name in naming.STATE_BUCKET_NAMES:
        assert f'"iac-core-{name}-0"' in automation
    assert set(repo.automation_service_accounts().values()) >= {
        "bootstrap-0",
        "resman-0",
    }


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("gcp-devops", "group:gcp-devops@example.com"),
        ("user:admin@example.com", "user:admin@example.com"),
    ],
)
def test_group_principal(name, expected):
    assert naming.group_principal(name, "example.com") == expected


def test_group_rule_matches_stage0(repo):
    assert naming.PRINCIPAL_TYPE_RE.pattern in _bootstrap_text(repo, "main.tf")


def test_group_name():
    defaults = {"gcp-devops": "gcp-devops", "gcp-security-admins": "sec"}
    groups = {"gcp-devops": "platform"}
    assert naming.group_name(groups, defaults, "gcp-devops") == "platform"
    assert naming.group_name(groups, defaults, "gcp-security-admins") == ("sec")
    with pytest.raises(KeyError):
        naming.group_name({"other": "x"}, defaults, "other")


def test_principal_email():
    assert naming.principal_email("group:ops@example.com") == "ops@example.com"


def test_workload_folder_name_matches_stage0(repo):
    assert naming.workload_folder_name("tst") == "StellarEngine-tst"
    assert 'display_name                 = "StellarEngine-${var.prefix}"' in (
        _bootstrap_text(repo, "organization.tf")
    )


def test_tenant_ids():
    assert naming.tenant_project_ids("tst", ["Prod"], "ten1") == [
        "tst-prod-ten1-iac-core-0",
        "tst-prod-ten1-main-0",
    ]
    assert naming.tenant_service_account_ids("tst", ["Prod"], "ten1") == [
        "tst-tn-prod-ten1-prod-0",
        "tst-prod-ten1-iac-0",
    ]
