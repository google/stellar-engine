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

"""Tests for the answers model rules that need no repository."""

import pydantic
import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine.config import models


def test_minimal_answers_get_defaults():
    answers = helpers.minimal_answers()
    assert answers.schema_version == 1
    assert list(answers.resman.envs) == ["Prod", "Int", "Test"]
    assert answers.resman.tenants == {}
    assert answers.logging.sink_type == "logging"
    assert answers.kms_protection_level is None
    assert answers.billing.is_org_level is True
    assert answers.billing.no_iam is False
    assert answers.imports == {}
    assert answers.overrides == {}
    assert answers.stage0_phase == models.STAGE0_BOOTSTRAP


@pytest.mark.parametrize("phase", ["bootstrap", "final"])
def test_stage0_phase_accepts_both_phases(phase):
    assert helpers.minimal_answers(stage0_phase=phase).stage0_phase == phase


def test_stage0_phase_rejects_other_values():
    with pytest.raises(pydantic.ValidationError, match="stage0_phase"):
        helpers.minimal_answers(stage0_phase="first")


def test_stage0_phase_schema_describes_the_field():
    schema = models.Answers.model_json_schema()["properties"]["stage0_phase"]
    assert schema["enum"] == ["bootstrap", "final"]
    assert schema["default"] == "bootstrap"
    assert "bootstrap_user" in schema["description"]


def test_default_envs_are_not_shared():
    first = helpers.minimal_answers()
    second = helpers.minimal_answers()
    first.resman.envs["Dev"] = models.EnvFolder()
    assert "Dev" not in second.resman.envs


@pytest.mark.parametrize(
    "data",
    [
        helpers.minimal_data(unknown=True),
        helpers.minimal_data(
            billing={"account_id": conftest.BILLING, "extra": 1}
        ),
        helpers.minimal_data(resman={"tenants": {"ten1": {"name": "x"}}}),
    ],
)
def test_unknown_keys_are_rejected(data):
    with pytest.raises(pydantic.ValidationError, match="Extra inputs"):
        models.Answers.model_validate(data)


def test_numeric_organization_id_becomes_string():
    data = helpers.minimal_data()
    data["organization"]["id"] = int(conftest.ORG_ID)
    answers = models.Answers.model_validate(data)
    assert answers.organization.id == conftest.ORG_ID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("prefix", "Tst"),
        ("prefix", "1ab"),
        ("prefix", "abc-"),
        ("bootstrap_project", "Bad_Project"),
        ("alert_email", "not-an-email"),
        ("bootstrap_user", "nobody"),
        ("kms_protection_level", "EXTERNAL"),
        ("compliance", {"regime": "il5"}),
        ("organization", {"id": "x1", "domain": "d", "customer_id": "C1"}),
        ("billing", {"account_id": "0000-AAAA"}),
        ("logging", {"sink_type": "splunk"}),
        ("budget", {"amount": 0}),
    ],
)
def test_invalid_formats_are_rejected(field, value):
    with pytest.raises(pydantic.ValidationError):
        helpers.minimal_answers(**{field: value})


@pytest.mark.parametrize(
    "contacts",
    [None, "ops@example.com", {"ops@example.com": ["ALL"]}],
)
def test_essential_contacts_accepts_string_or_map(contacts):
    answers = helpers.minimal_answers(essential_contacts=contacts)
    assert answers.essential_contacts == contacts


def test_env_keys_that_differ_only_in_case_are_rejected():
    data = helpers.minimal_data(resman={"envs": {"Prod": {}, "prod": {}}})
    with pytest.raises(pydantic.ValidationError, match="only in case"):
        models.Answers.model_validate(data)


@pytest.mark.parametrize("key", ["1prod", "prod_1", "pr od"])
def test_env_keys_must_fit_project_ids(key):
    data = helpers.minimal_data(resman={"envs": {key: {}}})
    with pytest.raises(pydantic.ValidationError, match="Env key"):
        models.Answers.model_validate(data)


@pytest.mark.parametrize("key", ["Ten1", "1ten", "ten_1"])
def test_tenant_keys_must_be_lowercase(key):
    data = helpers.minimal_data(
        resman={"tenants": {key: {"descriptive_name": "Tenant"}}}
    )
    with pytest.raises(pydantic.ValidationError, match="Tenant key"):
        models.Answers.model_validate(data)


def test_tenant_with_locations():
    data = helpers.minimal_data(
        resman={
            "tenants": {
                "ten-1": {
                    "descriptive_name": "Tenant one",
                    "admin_principal": "group:admins@example.com",
                    "locations": {"gcs": "us", "kms": "us"},
                }
            }
        }
    )
    tenant = models.Answers.model_validate(data).resman.tenants["ten-1"]
    assert tenant.locations == models.TenantLocations(gcs="us", kms="us")


@pytest.mark.parametrize("field", ["overrides", "imports"])
def test_stage_keyed_fields_reject_unknown_stages(field):
    value = {"2-networking": {"x": "y"}}
    with pytest.raises(pydantic.ValidationError, match="Unknown stage"):
        helpers.minimal_answers(**{field: value})


@pytest.mark.parametrize("field", ["overrides", "imports"])
def test_stage_keyed_fields_reject_aliases(field):
    with pytest.raises(pydantic.ValidationError, match="Unknown stage"):
        helpers.minimal_answers(**{field: {"0": {}}})


def test_imports_and_overrides_accept_every_stage():
    address = conftest.AUTOMATION_ADDRESS
    data = helpers.minimal_data(
        imports={
            stage: {address: "tst-prod-iac-core-0"} for stage in paths.STAGES
        },
        overrides={"0-bootstrap": {"iam": {"roles/browser": ["domain:x"]}}},
    )
    answers = models.Answers.model_validate(data)
    assert set(answers.imports) == set(paths.STAGES)
    assert answers.overrides["0-bootstrap"]["iam"]


def test_import_ids_must_not_be_empty():
    data = helpers.minimal_data(imports={"0-bootstrap": {"x.y": ""}})
    with pytest.raises(pydantic.ValidationError):
        models.Answers.model_validate(data)


def test_existing_org_policies_are_sorted_and_unique():
    data = helpers.minimal_data(
        existing_org_policies=[
            "storage.uniformBucketLevelAccess",
            "iam.allowedPolicyMemberDomains",
            "storage.uniformBucketLevelAccess",
        ]
    )
    answers = models.Answers.model_validate(data)
    assert answers.existing_org_policies == [
        "iam.allowedPolicyMemberDomains",
        "storage.uniformBucketLevelAccess",
    ]
    assert helpers.minimal_answers().existing_org_policies == []


@pytest.mark.parametrize(
    "name",
    [
        "noDot",
        "organizations/1/policies/iam.x",
        'iam.x"]',
        "iam.x ${y}",
        "",
    ],
)
def test_existing_org_policies_reject_non_constraints(name):
    data = helpers.minimal_data(existing_org_policies=[name])
    with pytest.raises(pydantic.ValidationError):
        models.Answers.model_validate(data)
