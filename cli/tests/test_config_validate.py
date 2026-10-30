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

"""Tests for the repository-backed answer rules."""

import pytest

import conftest
import helpers
from stellar_engine import repo as repo_lib
from stellar_engine.config import models
from stellar_engine.config import validate


def test_valid_answers_have_no_problems(repo):
    answers = helpers.minimal_answers(
        groups={"gcp-devops": "platform"},
        resman={"tenants": {"ten1": {"descriptive_name": "Tenant"}}},
        imports={
            "0-bootstrap": {
                conftest.AUTOMATION_ADDRESS: ("tst-prod-iac-core-0")
            }
        },
    )
    assert validate.problems(answers, repo) == []


def test_schema_prefix_limit_matches_repo(repo):
    schema = models.Answers.model_json_schema()["properties"]["prefix"]
    assert repo.prefix_max_length() == models.PREFIX_SCHEMA_MAX_LENGTH
    assert schema["maxLength"] == repo.prefix_max_length()


def test_prefix_longer_than_repo_limit(repo, monkeypatch):
    monkeypatch.setattr(repo_lib.Repo, "prefix_max_length", lambda self: 2)
    problems = validate.problems(helpers.minimal_answers(), repo)
    assert problems == [
        "prefix tst is longer than the 2 characters Stage 0 allows."
    ]


def test_unknown_regime(repo):
    problems = validate.problems(
        helpers.minimal_answers(compliance={"regime": "IL9"}), repo
    )
    assert len(problems) == 1
    assert problems[0].startswith("compliance.regime IL9 is not one of")


def test_unknown_group_key(repo):
    problems = validate.problems(
        helpers.minimal_answers(groups={"gcp-nope": "x"}), repo
    )
    assert len(problems) == 1
    assert problems[0].startswith("groups keys gcp-nope are not Stage 0")


def test_region_must_suit_the_regime(repo):
    answers = helpers.minimal_answers(region="us-east5")
    problems = validate.problems(answers, repo)
    assert len(problems) == 1
    assert problems[0].startswith(
        "region us-east5 is not an Assured Workloads region for IL5"
    )


def test_unlisted_region_can_be_allowed(repo):
    answers = helpers.minimal_answers(
        region="us-east5",
        compliance={"regime": "IL5", "allow_unlisted_region": True},
    )
    assert validate.problems(answers, repo) == []


def test_regime_without_region_table_accepts_any_region(repo):
    answers = helpers.minimal_answers(
        region="europe-west1", compliance={"regime": "IL2"}
    )
    assert validate.problems(answers, repo) == []


def test_tenant_key_limit_comes_from_resman(repo):
    answers = helpers.minimal_answers(
        resman={"tenants": {"abcdefg": {"descriptive_name": "Tenant"}}}
    )
    problems = validate.problems(answers, repo)
    assert (
        "resman.tenants key abcdefg is longer than the 6 characters Stage 1 "
        "allows."
    ) in problems


def test_tenant_ids_over_30_characters(repo):
    answers = helpers.minimal_answers(
        prefix="abcdefg",
        resman={
            "envs": {"Production": {}},
            "tenants": {"tenant": {"descriptive_name": "Tenant"}},
        },
    )
    problems = validate.problems(answers, repo)
    # abcdefg-production-tenant-iac-core-0 is 36 characters.
    assert any(
        "project ID abcdefg-production-tenant-iac-core-0 is 36" in problem
        for problem in problems
    )
    assert any("service account ID" in problem for problem in problems)
    assert all(
        problem.startswith("resman.tenants.tenant: ") for problem in problems
    )


@pytest.mark.parametrize(
    "address",
    [
        "google_project.project",
        "google_project.project[0]",
        conftest.AUTOMATION_ADDRESS,
        conftest.BILLING_EXPORT_ADDRESS,
        'module.a["key"].module.b[1].google_x.y["a.b[0]"]',
        'module.a["with \\"quote\\""].google_x.y',
    ],
)
def test_valid_import_addresses(address):
    assert validate.import_address_problems(address) == []


@pytest.mark.parametrize(
    ("address", "message"),
    [
        ("", "empty or has spaces"),
        (" google_x.y", "empty or has spaces"),
        ("google_project", "not a resource address"),
        ("module.automation-project", "names a module"),
        ("module.a.module.b", "names a module"),
        ("data.google_project.x", "data source"),
        ("module.a.data.google_project.x", "data source"),
        ("google_project.project[x]", "not a resource address"),
        ("google_project.project[0", "not a resource address"),
        ("google_project.project.extra", "not a resource address"),
        ("module..google_x.y", "not a resource address"),
        ("1bad.name", "not a resource address"),
        ("google_x.y[0][1]", "not a resource address"),
    ],
)
def test_invalid_import_addresses(address, message):
    problems = validate.import_address_problems(address)
    assert len(problems) == 1
    assert message in problems[0]


def test_problems_include_import_addresses(repo):
    answers = helpers.minimal_answers(
        imports={"0-bootstrap": {"bad address": "x"}}
    )
    problems = validate.problems(answers, repo)
    assert len(problems) == 1
    assert problems[0].startswith("imports.0-bootstrap: Import address")


def test_home_references(tmp_path):
    home = tmp_path / "home"
    answers = helpers.minimal_answers(
        overrides={
            "0-bootstrap": {"outputs_location": str(home / "envs/tst")},
            "1-resman": {"other": str(tmp_path / "elsewhere")},
        },
        engine={"path": str(tmp_path / "engine")},
    )
    problems = validate.home_references(answers, home)
    assert len(problems) == 1
    assert problems[0].startswith("overrides.0-bootstrap.outputs_location")


def test_home_references_skip_the_recorded_engine(tmp_path):
    home = tmp_path / "home"
    answers = helpers.minimal_answers(
        engine={"path": str(home / "engine")},
        overrides={"1-resman": {"other": str(home / "data")}},
    )
    problems = validate.home_references(answers, home)
    assert len(problems) == 1
    assert problems[0].startswith("overrides.1-resman.other")


def test_home_references_expand_tilde(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = helpers.minimal_answers(
        overrides={"1-resman": {"other": "~/home/engine"}}
    )
    assert validate.home_references(answers, tmp_path / "home")
    assert (
        validate.home_references(helpers.minimal_answers(), tmp_path / "home")
        == []
    )


def test_import_id_must_match_the_prefix(repo):
    # The prefix changes while the imports keep the old project IDs.
    data = helpers.fixture_data("lab")
    data["prefix"] = "new1"
    problems = validate.problems(models.Answers.model_validate(data), repo)
    assert len(problems) == 2
    assert problems[0].startswith(
        f"imports.0-bootstrap: {conftest.AUTOMATION_ADDRESS} imports "
        "lab1-prod-iac-core-0, "
        "but Stage 0 names that project new1-prod-iac-core-0"
    )
    assert "new1-prod-audit-logs-0" in problems[1]


def test_swapped_import_id_is_a_problem(repo):
    answers = helpers.minimal_answers(
        imports={
            "0-bootstrap": {
                conftest.AUTOMATION_ADDRESS: "tst-prod-audit-logs-0"
            }
        }
    )
    problems = validate.problems(answers, repo)
    assert len(problems) == 1
    assert "set the import ID to tst-prod-iac-core-0" in problems[0]


def test_unknown_import_addresses_keep_any_id(repo):
    answers = helpers.minimal_answers(
        imports={
            "0-bootstrap": {"google_storage_bucket.extra": "any-bucket"},
            "1-resman": {
                'module.x["a"].google_project.project[0]': "any-project"
            },
        }
    )
    assert validate.problems(answers, repo) == []


def test_problems_include_override_problems(repo):
    answers = helpers.minimal_answers(
        overrides={
            "0-bootstrap": {"prefix": "other", "not_a_var": 1},
            "1-resman": {"prefix": "zzz"},
        }
    )
    problems = validate.problems(answers, repo)
    assert len(problems) == 3
    assert all(problem.startswith("overrides.") for problem in problems)


def test_existing_org_policies_declared_by_stage0(repo):
    answers = helpers.minimal_answers(
        existing_org_policies=[
            "iam.allowedPolicyMemberDomains",
            "compute.skipDefaultNetworkCreation",
        ]
    )
    assert validate.problems(answers, repo) == []


def test_existing_org_policies_reject_custom_and_undeclared(repo):
    answers = helpers.minimal_answers(
        existing_org_policies=["custom.kmsRotation", "unmanaged.constraint"]
    )
    problems = validate.problems(answers, repo)
    assert len(problems) == 2
    assert "custom.kmsRotation" in problems[0]
    assert "custom constraints" in problems[0]
    assert "unmanaged.constraint" in problems[1]
    assert "stellar imports scan" in problems[1]


def test_existing_org_policies_conflict_with_import_defaults(repo):
    overrides = {
        "0-bootstrap": {"org_policies_config": {"import_defaults": True}}
    }
    assert (
        validate.problems(helpers.minimal_answers(overrides=overrides), repo)
        == []
    )
    answers = helpers.minimal_answers(
        overrides=overrides,
        existing_org_policies=["iam.allowedPolicyMemberDomains"],
    )
    problems = validate.problems(answers, repo)
    assert len(problems) == 1
    assert "import_defaults" in problems[0]
    assert "whether or not each one exists" in problems[0]


def test_existing_org_policies_accept_any_regime(repo):
    # The list stays valid when the regime omits a templated policy,
    # because the import filter drops it.
    answers = helpers.minimal_answers(
        existing_org_policies=[
            "compute.managed.restrictProtocolForwardingCreationForTypes"
        ]
    )
    answers.compliance.regime = "FEDRAMP_MODERATE"
    assert validate.problems(answers, repo) == []


WORKLOAD = "google_assured_workloads_workload.primary[0]"
WORKLOAD_ID = (
    f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/abc123"
)


def test_workload_import_is_valid(repo):
    assert validate.import_address_problems(WORKLOAD) == []
    answers = helpers.minimal_answers(
        imports={"0-bootstrap": {WORKLOAD: WORKLOAD_ID}}
    )
    assert validate.problems(answers, repo) == []


def test_workload_import_follows_the_compliance_location(repo):
    answers = helpers.minimal_answers(
        compliance={"regime": "IL5", "location": "US"},
        imports={
            "0-bootstrap": {
                WORKLOAD: f"organizations/{conftest.ORG_ID}/locations/us/"
                "workloads/abc123"
            }
        },
    )
    assert validate.problems(answers, repo) == []


@pytest.mark.parametrize(
    "import_id",
    [
        "abc123",
        "organizations/999999999999/locations/us-east4/workloads/abc123",
        f"organizations/{conftest.ORG_ID}/locations/us-west1/workloads/abc",
        f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/",
    ],
)
def test_workload_import_id_must_match(repo, import_id):
    answers = helpers.minimal_answers(
        imports={"0-bootstrap": {WORKLOAD: import_id}}
    )
    problems = validate.problems(answers, repo)
    assert len(problems) == 1
    assert problems[0].startswith(f"imports.0-bootstrap: {WORKLOAD}")
    assert "would replace the imported workload" in problems[0]


def test_workload_name_problem_names_the_pattern():
    answers = helpers.minimal_answers()
    assert validate.workload_name_problem(WORKLOAD_ID, answers) is None
    pattern = validate.workload_name_pattern(answers)
    assert pattern == (
        f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/"
        "<workload_id>"
    )
    problem = validate.workload_name_problem("abc123", answers)
    assert problem is not None
    assert pattern in problem


def test_bootstrap_phase_requires_bootstrap_user(repo):
    answers = helpers.minimal_answers(bootstrap_user=None)
    found = validate.problems(answers, repo)
    assert len(found) == 1
    assert found[0].startswith(
        "bootstrap_user is required while stage0_phase is bootstrap"
    )
    assert "first Stage 0 apply" in found[0]


def test_final_phase_needs_no_bootstrap_user(repo):
    answers = helpers.minimal_answers(bootstrap_user=None, stage0_phase="final")
    assert validate.problems(answers, repo) == []


@pytest.mark.parametrize(
    ("previous", "updated", "refused"),
    [
        ("final", "bootstrap", True),
        ("final", "final", False),
        ("bootstrap", "final", False),
        ("bootstrap", "bootstrap", False),
    ],
)
def test_phase_change_problems(previous, updated, refused):
    found = validate.phase_change_problems(previous, updated)
    assert bool(found) is refused
    if refused:
        assert found == [
            "stage0_phase cannot return from final to bootstrap: the final "
            "Stage 0 apply already ran, and a bootstrap apply would delete "
            "the organization policies and essential contacts it manages; "
            "keep stage0_phase final."
        ]


def test_no_warnings_without_external_grant():
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "no_iam": True},
        billing_override={
            "project": "my-project",
            "billing_project": "my-project",
        },
    )
    assert validate.warnings(answers) == []


def test_external_grant_with_no_iam_alone_is_fine():
    answers = helpers.minimal_answers(
        billing={
            "account_id": conftest.BILLING,
            "no_iam": True,
            "external_grant": True,
        }
    )
    assert validate.warnings(answers) == []


def test_external_grant_is_redundant_when_stage0_manages_billing_iam():
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "external_grant": True}
    )
    found = validate.warnings(answers)
    assert len(found) == 1
    assert found[0].startswith(
        "billing.external_grant is set while billing.no_iam is false"
    )


def test_external_grant_is_unused_with_billing_override():
    answers = helpers.minimal_answers(
        billing={
            "account_id": conftest.BILLING,
            "no_iam": True,
            "external_grant": True,
        },
        billing_override={
            "project": "my-project",
            "billing_project": "my-project",
        },
    )
    found = validate.warnings(answers)
    assert len(found) == 1
    assert found[0].startswith(
        "billing.external_grant and billing_override are both set"
    )


def test_warnings_are_not_problems(repo):
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "external_grant": True}
    )
    assert validate.warnings(answers)
    assert validate.problems(answers, repo) == []
