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

"""Tests for the `stellar init` wizard sections."""

import copy

import pytest

import conftest
import helpers
from stellar_engine.config import models
from stellar_engine.config import validate
from stellar_engine.gcp import api
from stellar_engine.preflight import regions
from stellar_engine.wizard import discovery
from stellar_engine.wizard import flow
from stellar_engine.wizard import prompts

OTHER = "module.other.google_storage_bucket.bucket"


class RecordingPrompter(prompts.ScriptedPrompter):
    """Scripted prompter that also records the choices of each select."""

    def __init__(self, answers):
        super().__init__(answers)
        self.choices = {}

    def select(self, message, choices, default=None) -> str:
        self.choices[message] = list(choices)
        return super().select(message, choices, default)


@pytest.fixture
def discovered(cloud, local_tools):
    return discovery.discover(cloud, local_tools)


def _run(data, answers, repo, found, sections=None):
    prompter = RecordingPrompter(answers)
    result = flow.run(
        data,
        prompter=prompter,
        repo=repo,
        discovered=found,
        sections=sections,
    )
    assert prompter.answers == [], "unused scripted answers"
    return result, prompter


# One entry per prompt of a full run; None accepts the default.
FRESH = [
    "tst",  # prefix
    None,  # organization ID
    None,  # domain
    None,  # customer ID
    None,  # billing account
    None,  # is_org_level
    None,  # no_iam
    None,  # external_grant
    None,  # bootstrap project
    None,  # pre-created projects
    "IL5",  # regime
    "us-east4",  # region
    None,  # Assured Workloads location
    None,  # KMS level
    None,  # alert email
    None,  # essential contacts
    None,  # bootstrap user
    None,  # rename groups
    None,  # env keys
    None,  # custom folder admins
    None,  # tenant keys
]


def test_sections_order():
    assert list(flow.SECTIONS) == [
        "prefix",
        "organization",
        "billing",
        "bootstrap",
        "compliance",
        "region",
        "kms",
        "contacts",
        "groups",
        "envs",
        "tenants",
    ]


def test_fresh_run_accepts_discovered_defaults(repo, discovered):
    result, _ = _run({}, FRESH, repo, discovered)
    assert result == {
        "prefix": "tst",
        "organization": {
            "id": conftest.ORG_ID,
            "domain": conftest.DOMAIN,
            "customer_id": conftest.CUSTOMER_ID,
        },
        "billing": {
            "account_id": conftest.BILLING,
            "is_org_level": True,
            "no_iam": False,
            "external_grant": False,
        },
        "bootstrap_project": conftest.PROJECT,
        "compliance": {"regime": "IL5"},
        "region": "us-east4",
        "alert_email": conftest.USER,
        "bootstrap_user": conftest.USER,
        "resman": {
            "envs": {"Prod": {}, "Int": {}, "Test": {}},
            "tenants": {},
        },
    }
    answers = models.Answers.model_validate(result)
    assert validate.problems(answers, repo) == []


def test_offline_fresh_run_needs_typed_values(repo):
    script = list(FRESH)
    script[1:4] = [conftest.ORG_ID, conftest.DOMAIN, conftest.CUSTOMER_ID]
    script[4] = conftest.BILLING
    script[8] = conftest.PROJECT
    script[14] = f"alerts@{conftest.DOMAIN}"
    script[16] = f"admin@{conftest.DOMAIN}"
    result, _ = _run({}, script, repo, discovery.Discovered())
    assert result["organization"]["id"] == conftest.ORG_ID
    assert result["alert_email"] == f"alerts@{conftest.DOMAIN}"
    assert result["bootstrap_user"] == f"admin@{conftest.DOMAIN}"


def test_bootstrap_phase_requires_a_bootstrap_user(repo):
    script = list(FRESH)
    script[1:4] = [conftest.ORG_ID, conftest.DOMAIN, conftest.CUSTOMER_ID]
    script[4] = conftest.BILLING
    script[8] = conftest.PROJECT
    script[14] = f"alerts@{conftest.DOMAIN}"
    # A blank bootstrap user fails validation, so the prompt asks again.
    script[16:17] = ["", f"admin@{conftest.DOMAIN}"]
    result, prompter = _run({}, script, repo, discovery.Discovered())
    assert result["bootstrap_user"] == f"admin@{conftest.DOMAIN}"
    assert "Enter an email address such as admin@example.com." in (
        prompter.notes
    )


def test_final_phase_accepts_a_blank_bootstrap_user(repo):
    data = helpers.minimal_data(stage0_phase="final", bootstrap_user=None)
    result, prompter = _run(
        data, [None, None, ""], repo, discovery.Discovered(), ["contacts"]
    )
    assert "bootstrap_user" not in result
    assert prompter.asked[-1].endswith(", blank for none")


def test_rerun_keeps_existing_answers(repo, discovered):
    data = helpers.minimal_data(
        kms_protection_level="SOFTWARE",
        essential_contacts=f"ops@{conftest.DOMAIN}",
        bootstrap_user=f"admin@{conftest.DOMAIN}",
        groups={"gcp-devops": "team-devops"},
        compliance={"regime": "IL5", "location": "us"},
        billing={
            "account_id": conftest.BILLING,
            "is_org_level": True,
            "no_iam": True,
            "external_grant": False,
        },
        resman={
            "envs": {"Prod": {"admin": f"prod@{conftest.DOMAIN}"}, "Dev": {}},
            "tenants": {
                "ten1": {
                    "descriptive_name": "Tenant one",
                    "admin_principal": f"user:t@{conftest.DOMAIN}",
                    "locations": {"gcs": "us", "kms": "us"},
                }
            },
        },
        imports={"0-bootstrap": {OTHER: "other-bucket"}},
        overrides={"0-bootstrap": {"iam": {}}},
    )
    original = copy.deepcopy(data)
    # Every prompt accepts its default; renamed groups and custom admins
    # ask one more question per group and env.
    groups = len(repo.default_groups())
    script = [None] * (len(FRESH) + groups + 2 + 2)
    result, prompter = _run(data, script, repo, discovered)
    assert result == original
    assert data == original
    assert "Organization ID" in prompter.asked


def test_section_subset_asks_only_those(repo, discovered):
    data = helpers.minimal_data()
    result, prompter = _run(
        data, ["new", None], repo, discovered, sections=["kms", "prefix"]
    )
    assert prompter.asked == [
        "Resource prefix, at most 7 characters",
        "KMS protection level",
    ]
    assert result == {**data, "prefix": "new"}


def test_unknown_section():
    with pytest.raises(ValueError, match="Unknown section nope"):
        flow.run(
            {},
            prompter=prompts.ScriptedPrompter([]),
            repo=None,  # pyright: ignore[reportArgumentType]
            discovered=discovery.Discovered(),
            sections=["nope"],
        )


def test_tenants_show_project_ids_and_characters_left(repo, discovered):
    data = helpers.minimal_data(resman={"envs": {"Prod": {}}})
    result, prompter = _run(
        data,
        ["ten1, ten2", "Tenant one", None, None, "group:t2@example.com"],
        repo,
        discovered,
        sections=["tenants"],
    )
    tenants = result["resman"]["tenants"]
    assert tenants == {
        "ten1": {"descriptive_name": "Tenant one"},
        "ten2": {
            "descriptive_name": "ten2",
            "admin_principal": "group:t2@example.com",
        },
    }
    assert "Tenant ten1 projects:" in prompter.notes
    # tst-prod-ten1-iac-core-0 is 24 characters.
    assert "  tst-prod-ten1-iac-core-0  6 characters left" in prompter.notes
    assert "  tst-prod-ten1-main-0  10 characters left" in prompter.notes


def test_tenant_key_rejected_when_ids_too_long(repo, discovered):
    data = helpers.minimal_data(
        prefix="abcdefg", resman={"envs": {"Prod1": {}}}
    )
    result, prompter = _run(
        data,
        ["tenant", "ten", None, None],
        repo,
        discovered,
        sections=["tenants"],
    )
    assert list(result["resman"]["tenants"]) == ["ten"]
    assert any("longer than 30 characters" in note for note in prompter.notes)


def test_tenant_key_limit_from_repo(repo, discovered):
    limit = repo.tenant_key_max_length()
    data = helpers.minimal_data(resman={"envs": {"P": {}}})
    result, prompter = _run(
        data,
        ["a" * (limit + 1), "a" * limit, None, None],
        repo,
        discovered,
        sections=["tenants"],
    )
    assert list(result["resman"]["tenants"]) == ["a" * limit]
    assert (
        prompter.asked.count("Tenant keys, comma-separated, blank for none")
        == 2
    )


@pytest.mark.parametrize("regime", ["IL5", "FEDRAMP_HIGH"])
def test_region_choices_follow_regime(repo, discovered, regime):
    data = helpers.minimal_data(compliance={"regime": regime})
    _, prompter = _run(data, [None, None], repo, discovered, ["region"])
    expected = sorted(regions.supported_regions(regime) or ())
    assert prompter.choices[f"Region for {regime}"] == expected


def test_region_outside_regime_is_flagged(repo, discovered):
    data = helpers.minimal_data(
        region="us-south1", compliance={"regime": "IL5"}
    )
    result, prompter = _run(data, [None, None], repo, discovered, ["region"])
    assert "Region us-south1 is not listed for IL5; pick another." in (
        prompter.notes
    )
    assert result["region"] in regions.supported_regions("IL5")


def test_region_without_table_is_typed(repo, discovered):
    data = helpers.minimal_data(
        compliance={"regime": "COMPLIANCE_REGIME_UNSPECIFIED"}
    )
    result, prompter = _run(
        data, ["europe-west1", None], repo, discovered, ["region"]
    )
    assert result["region"] == "europe-west1"
    assert any(note.startswith("No region table") for note in prompter.notes)


def test_region_keeps_only_a_different_location(repo, discovered):
    data = helpers.minimal_data(compliance={"regime": "IL5", "location": "us"})
    result, _ = _run(data, [None, "us-east4"], repo, discovered, ["region"])
    assert result["compliance"] == {"regime": "IL5"}
    result, _ = _run(data, [None, None], repo, discovered, ["region"])
    assert result["compliance"] == {"regime": "IL5", "location": "us"}


def test_regime_choices_come_from_repo(repo, discovered):
    _, prompter = _run(
        helpers.minimal_data(), [None], repo, discovered, ["compliance"]
    )
    choices = prompter.choices["Compliance regime"]
    assert sorted(choices) == repo.regime_names()
    # Regimes with a region table come first.
    assert set(choices[:4]) == set(regions.SUPPORTED_REGIONS)


@pytest.mark.parametrize(
    ("regime", "picked", "stored"),
    [
        ("IL5", "HSM", None),
        ("IL5", "SOFTWARE", "SOFTWARE"),
        ("FEDRAMP_MODERATE", "SOFTWARE", None),
        ("FEDRAMP_MODERATE", "HSM", "HSM"),
    ],
)
def test_kms_stored_only_when_changed(repo, discovered, regime, picked, stored):
    data = helpers.minimal_data(compliance={"regime": regime})
    result, prompter = _run(data, [picked], repo, discovered, ["kms"])
    assert result.get("kms_protection_level") == stored
    assert any("derives KMS protection level" in n for n in prompter.notes)


def test_kms_explicit_value_is_the_default(repo, discovered):
    data = helpers.minimal_data(kms_protection_level="SOFTWARE")
    result, _ = _run(data, [None], repo, discovered, ["kms"])
    assert result["kms_protection_level"] == "SOFTWARE"


def test_kms_back_to_derived_clears_value(repo, discovered):
    data = helpers.minimal_data(kms_protection_level="SOFTWARE")
    result, _ = _run(data, ["HSM"], repo, discovered, ["kms"])
    assert "kms_protection_level" not in result


def test_several_orgs_are_offered_as_choices(repo, cloud, local_tools):
    cloud.orgs = [
        api.Organization("111111111111", "one.example.com", "C0000001"),
        api.Organization("222222222222", "two.example.com", "C0000002"),
    ]
    found = discovery.discover(cloud, local_tools)
    data = helpers.minimal_data()
    del data["organization"]
    result, prompter = _run(
        data, ["222222222222", None, None], repo, found, ["organization"]
    )
    assert result["organization"] == {
        "id": "222222222222",
        "domain": "two.example.com",
        "customer_id": "C0000002",
    }
    assert "111111111111  one.example.com" in prompter.notes


def test_changed_org_takes_discovered_domain(repo, cloud, local_tools):
    cloud.orgs = [
        api.Organization("222222222222", "two.example.com", "C0000002")
    ]
    found = discovery.discover(cloud, local_tools)
    result, _ = _run(
        helpers.minimal_data(),
        ["222222222222", None, None],
        repo,
        found,
        ["organization"],
    )
    assert result["organization"]["domain"] == "two.example.com"


def test_closed_billing_accounts_are_not_defaults(repo, cloud, local_tools):
    cloud.billing_accounts = [api.BillingAccount(conftest.BILLING, False)]
    found = discovery.discover(cloud, local_tools)
    data = helpers.minimal_data()
    del data["billing"]
    result, prompter = _run(
        data,
        [None, "111111-AAAAAA-BBBBBB", None, None, None],
        repo,
        found,
        ["billing"],
    )
    assert result["billing"]["account_id"] == "111111-AAAAAA-BBBBBB"
    assert prompter.notes == ["Enter an ID such as 000000-AAAAAA-BBBBBB."]


def test_service_account_is_not_a_contact_default(repo, cloud, local_tools):
    local_tools.account = "sa@example-bootstrap.iam.gserviceaccount.com"
    found = discovery.discover(cloud, local_tools)
    result, prompter = _run(
        # The final phase allows a blank bootstrap user, so the test sees
        # that the service account is not its default either.
        helpers.minimal_data(
            alert_email=None, bootstrap_user=None, stage0_phase="final"
        ),
        [None, f"alerts@{conftest.DOMAIN}", None, None],
        repo,
        found,
        ["contacts"],
    )
    assert result["alert_email"] == f"alerts@{conftest.DOMAIN}"
    assert "bootstrap_user" not in result
    assert "essential_contacts" not in result
    assert prompter.notes == [
        "Enter an email address such as admin@example.com."
    ]


def test_essential_contacts_map_is_kept(repo, discovered):
    contacts = {f"ops@{conftest.DOMAIN}": ["ALL"]}
    data = helpers.minimal_data(essential_contacts=contacts)
    result, prompter = _run(data, [None, None], repo, discovered, ["contacts"])
    assert result["essential_contacts"] == contacts
    assert any("essential_contacts map" in note for note in prompter.notes)


def test_groups_store_only_renames(repo, discovered):
    defaults = repo.default_groups()
    script: list[object] = [True, "renamed-first"]
    script += [None] * (len(defaults) - 1)
    result, _ = _run(
        helpers.minimal_data(), script, repo, discovered, ["groups"]
    )
    assert result["groups"] == {next(iter(defaults)): "renamed-first"}
    result, _ = _run(
        {**helpers.minimal_data(), "groups": result["groups"]},
        [False],
        repo,
        discovered,
        ["groups"],
    )
    assert "groups" not in result


def test_envs_with_custom_admins(repo, discovered):
    default_admin = f"gcp-organization-admins@{conftest.DOMAIN}"
    result, prompter = _run(
        helpers.minimal_data(),
        ["Prod, Dev", True, f"prod@{conftest.DOMAIN}", None],
        repo,
        discovered,
        ["envs"],
    )
    assert result["resman"]["envs"] == {
        "Prod": {"admin": f"prod@{conftest.DOMAIN}"},
        "Dev": {},
    }
    assert f"Use folder admins other than {default_admin}?" in prompter.asked


def test_env_keys_validated(repo, discovered):
    result, prompter = _run(
        helpers.minimal_data(),
        ["Prod, prod", "", "1st", "Prod", None],
        repo,
        discovered,
        ["envs"],
    )
    assert result["resman"]["envs"] == {"Prod": {}}
    assert len(prompter.notes) == 3


@pytest.mark.parametrize(
    ("billing", "expected"),
    [
        (
            {"no_iam": True},
            {
                conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0",
                conftest.LOG_EXPORT_ADDRESS: "tst-prod-audit-logs-0",
            },
        ),
        (
            {"no_iam": False},
            {
                conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0",
                conftest.LOG_EXPORT_ADDRESS: "tst-prod-audit-logs-0",
                conftest.BILLING_EXPORT_ADDRESS: "tst-prod-billing-exp-0",
            },
        ),
        (
            {"no_iam": False, "is_org_level": False},
            {
                conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0",
                conftest.LOG_EXPORT_ADDRESS: "tst-prod-audit-logs-0",
            },
        ),
    ],
)
def test_bootstrap_precreated_projects_become_imports(
    repo, discovered, billing, expected
):
    data = helpers.minimal_data(
        billing={"account_id": conftest.BILLING, **billing}
    )
    result, prompter = _run(
        data, [None, True, None], repo, discovered, ["bootstrap"]
    )
    assert result["imports"] == {"0-bootstrap": expected}
    assert (
        f"  import {conftest.AUTOMATION_ADDRESS} = tst-prod-iac-core-0"
        in prompter.notes
    )


@pytest.mark.parametrize(
    "billing", [{"no_iam": True}, {"no_iam": False, "is_org_level": False}]
)
def test_bootstrap_notes_why_billing_export_is_not_imported(
    repo, discovered, billing
):
    data = helpers.minimal_data(
        billing={"account_id": conftest.BILLING, **billing}
    )
    _, prompter = _run(
        data, [None, True, None], repo, discovered, ["bootstrap"]
    )
    assert (
        f"  Stage 0 creates {conftest.BILLING_EXPORT_ADDRESS} only when "
        "billing.no_iam is false and billing.is_org_level is true, so "
        "Stage 0 imports nothing for it."
    ) in prompter.notes


def test_stage0_project_addresses_match_repo(repo):
    projects = repo.stage0_projects()
    assert [project.address for project in projects] == [
        conftest.AUTOMATION_ADDRESS,
        conftest.LOG_EXPORT_ADDRESS,
        conftest.BILLING_EXPORT_ADDRESS,
    ]
    assert projects[0].count is None
    assert "billing_mode" in (projects[2].count or "")


def test_bootstrap_declining_removes_only_project_imports(repo, discovered):
    data = helpers.minimal_data(
        imports={
            "0-bootstrap": {
                conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0",
                OTHER: "other-bucket",
            }
        }
    )
    result, prompter = _run(
        data, [None, False], repo, discovered, ["bootstrap"]
    )
    assert result["imports"] == {"0-bootstrap": {OTHER: "other-bucket"}}
    assert (
        "Do the Stage 0 projects exist already, so Stage 0 imports them?"
        in (prompter.asked)
    )


def test_bootstrap_declining_drops_empty_imports(repo, discovered):
    data = helpers.minimal_data(
        imports={
            "0-bootstrap": {conftest.AUTOMATION_ADDRESS: "x-prod-iac-core-0"}
        }
    )
    result, _ = _run(data, [None, False], repo, discovered, ["bootstrap"])
    assert "imports" not in result


def test_bootstrap_rerun_defaults_to_existing_imports(repo, discovered):
    data = helpers.minimal_data(
        billing={"account_id": conftest.BILLING, "no_iam": True},
        imports={
            "0-bootstrap": {conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0"}
        },
    )
    result, _ = _run(data, [None, None, None], repo, discovered, ["bootstrap"])
    assert set(result["imports"]["0-bootstrap"]) == {
        conftest.AUTOMATION_ADDRESS,
        conftest.LOG_EXPORT_ADDRESS,
    }


def test_prefix_change_updates_imports(repo, discovered):
    data = helpers.minimal_data(
        billing={"account_id": conftest.BILLING, "no_iam": True},
        imports={
            "0-bootstrap": {
                conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0",
                conftest.LOG_EXPORT_ADDRESS: "tst-prod-audit-logs-0",
            }
        },
    )
    result, prompter = _run(data, ["abc"], repo, discovered, ["prefix"])
    assert result["imports"]["0-bootstrap"] == {
        conftest.AUTOMATION_ADDRESS: "abc-prod-iac-core-0",
        conftest.LOG_EXPORT_ADDRESS: "abc-prod-audit-logs-0",
    }
    assert "Updated the Stage 0 imports:" in prompter.notes


def test_billing_change_adds_billing_export_import(repo, discovered):
    data = helpers.minimal_data(
        billing={"account_id": conftest.BILLING, "no_iam": True},
        imports={
            "0-bootstrap": {conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0"}
        },
    )
    result, _ = _run(
        data, [None, None, False, None], repo, discovered, ["billing"]
    )
    assert conftest.BILLING_EXPORT_ADDRESS in result["imports"]["0-bootstrap"]


def test_invalid_answer_reasks_owning_section(repo, discovered):
    # A stored prefix the model rejects sends the wizard back to prefix.
    data = helpers.minimal_data(prefix="Bad_Prefix")
    result, prompter = _run(data, [None, "good"], repo, discovered, ["tenants"])
    assert result["prefix"] == "good"
    assert prompter.asked == [
        "Tenant keys, comma-separated, blank for none",
        "Resource prefix, at most 7 characters",
    ]
    assert "These answers need another look:" in prompter.notes


def test_long_tenant_ids_reask_prefix_envs_and_tenants(repo, discovered):
    data = helpers.minimal_data(
        prefix="abcdefg",
        resman={"envs": {"Prod": {}}, "tenants": {"tenant": {}}},
    )
    data["resman"]["tenants"]["tenant"] = {"descriptive_name": "t"}
    script = [
        "Production",  # env keys, which makes the tenant IDs too long
        None,  # custom admins
        None,  # prefix kept
        "Prod",  # env keys fixed
        None,  # custom admins
        None,  # tenant keys kept
        None,  # descriptive name
        None,  # admin principal
    ]
    result, prompter = _run(data, script, repo, discovered, ["envs"])
    assert list(result["resman"]["envs"]) == ["Prod"]
    assert any("over the 30 limit" in note for note in prompter.notes)


def test_retries_are_bounded(repo, discovered):
    # The bootstrap section keeps foreign import entries, so a malformed one
    # survives every round.
    data = helpers.minimal_data(
        imports={"0-bootstrap": {"not an address": "x"}}
    )
    script = [None, None] * (flow.MAX_ROUNDS + 1)
    prompter = prompts.ScriptedPrompter(script)
    with pytest.raises(flow.WizardError) as caught:
        flow.run(
            data,
            prompter=prompter,
            repo=repo,
            discovered=discovered,
            sections=["bootstrap"],
        )
    assert prompter.answers == []
    assert "Bootstrap project ID" in prompter.asked
    assert any("not an address" in p for p in caught.value.problems)


def test_problem_without_section_raises_at_once(repo, discovered):
    data = helpers.minimal_data(logging={"sink_type": "nope"})
    prompter = prompts.ScriptedPrompter([None])
    with pytest.raises(flow.WizardError, match=r"logging\.sink_type"):
        flow.run(
            data,
            prompter=prompter,
            repo=repo,
            discovered=discovered,
            sections=["kms"],
        )


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("prefix", ("prefix",)),
        ("compliance.regime", ("compliance",)),
        ("compliance.location", ("region",)),
        ("compliance.allow_unlisted_region", ("region",)),
        ("bootstrap_user", ("contacts",)),
        ("bootstrap_project", ("bootstrap",)),
        ("region", ("region",)),
        ("billing.account_id", ("billing",)),
        ("billing_override", ()),
        ("imports.0-bootstrap", ("bootstrap",)),
        ("resman.envs", ("envs",)),
        ("resman.tenants", ("tenants",)),
        ("resman.tenants.ten1", ("prefix", "envs", "tenants")),
        ("overrides", ()),
    ],
)
def test_owners(field, expected):
    assert flow.owners(field) == expected
