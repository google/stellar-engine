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

"""Tests for loading, editing and saving answers.yaml."""

import json

import pytest

import conftest
import helpers
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.preflight import inputs as inputs_lib


@pytest.fixture
def answers_path(tmp_path):
    return tmp_path / "home" / "envs" / "tst" / "answers.yaml"


def test_save_and_load_round_trip(answers_path):
    answers = helpers.minimal_answers(
        bootstrap_user=conftest.USER,
        resman={"tenants": {"ten1": {"descriptive_name": "Tenant"}}},
        imports={
            "0-bootstrap": {conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0"}
        },
        overrides={"0-bootstrap": {"iam": {"roles/browser": ["domain:x"]}}},
    )
    schema = answers_path.parents[2] / "answers.schema.json"
    answers_lib.save(answers_path, answers, home=answers_path.parents[2])
    assert answers_lib.load(answers_path) == answers
    text = answers_path.read_text(encoding="utf-8")
    assert text.splitlines()[0] == answers_lib.SCHEMA_COMMENT
    assert text.count(answers_lib.SCHEMA_COMMENT) == 1
    # Derived values stay unset in the file.
    assert "kms_protection_level" not in text
    assert conftest.mode(answers_path) == 0o600
    assert json.loads(schema.read_text(encoding="utf-8"))["properties"]


def test_schema_comment_points_at_home_schema(answers_path):
    home = answers_path.parents[2]
    relative = answers_lib.SCHEMA_COMMENT.split("$schema=")[1]
    assert (answers_path.parent / relative).resolve() == (
        home / "answers.schema.json"
    ).resolve()


def test_save_keeps_operator_comments(answers_path):
    answers_lib.save(answers_path, helpers.minimal_answers())
    text = answers_path.read_text(encoding="utf-8")
    text = text.replace(
        "region: us-east4",
        "# Pinned by the network team.\nregion: us-east4  # keep",
    ).replace(
        "  regime: IL5",
        "  # Lab runs IL5.\n  regime: IL5",
    )
    text = text.replace(
        answers_lib.SCHEMA_COMMENT,
        f"{answers_lib.SCHEMA_COMMENT}\n# Lab environment answers.",
    )
    answers_path.write_text(text, encoding="utf-8")

    previous = answers_lib.load_data(answers_path)
    updated = answers_lib.load(answers_path).model_copy(
        update={"alert_email": "ops@example.com", "kms_protection_level": "HSM"}
    )
    answers_lib.save(answers_path, updated, previous=previous)

    saved = answers_path.read_text(encoding="utf-8")
    lines = saved.splitlines()
    assert lines[0] == answers_lib.SCHEMA_COMMENT
    assert lines[1] == "# Lab environment answers."
    assert "# Pinned by the network team.\nregion: us-east4  # keep" in saved
    assert "  # Lab runs IL5.\n  regime: IL5" in saved
    assert "alert_email: ops@example.com" in saved
    assert "kms_protection_level: HSM" in saved
    assert answers_lib.load(answers_path) == updated


def test_save_drops_keys_that_become_unset(answers_path):
    answers_lib.save(
        answers_path, helpers.minimal_answers(kms_protection_level="HSM")
    )
    previous = answers_lib.load_data(answers_path)
    answers_lib.save(answers_path, helpers.minimal_answers(), previous=previous)
    assert "kms_protection_level" not in answers_path.read_text(
        encoding="utf-8"
    )


def _save_without(path, *keys):
    previous = answers_lib.load_data(path)
    data = answers_lib.plain(previous)
    for key in keys:
        parent = data
        *parents, last = key.split(".")
        for name in parents:
            parent = parent[name]
        parent.pop(last)
    answers_lib.save(path, answers_lib.parse(data), previous=previous)
    return path.read_text(encoding="utf-8")


def _il5_answers(answers_path, replacements):
    answers_path.parent.mkdir(parents=True)
    text = (helpers.ANSWERS_DIR / "il5.yaml").read_text("utf-8")
    for old, new in replacements:
        assert old in text
        text = text.replace(old, new)
    answers_path.write_text(text, encoding="utf-8")


def test_comment_above_key_survives_removal_of_previous_key(answers_path):
    _il5_answers(
        answers_path,
        [
            (
                "kms_protection_level: SOFTWARE\n",
                "kms_protection_level: SOFTWARE  # explicit\n"
                "# Operator note about alerts\n",
            )
        ],
    )
    saved = _save_without(answers_path, "kms_protection_level")
    assert "kms_protection_level" not in saved
    assert "# explicit" not in saved
    assert "# Operator note about alerts\nalert_email:" in saved


def test_nested_comment_survives_removal_of_last_nested_key(answers_path):
    _il5_answers(
        answers_path,
        [
            (
                "  regime: IL5\n",
                "  regime: IL5\n  location: us-west1\n"
                "# Operator note about KMS\n",
            )
        ],
    )
    saved = _save_without(answers_path, "compliance.location")
    assert "location" not in saved
    assert "# Operator note about KMS\nkms_protection_level:" in saved


def test_nested_comment_survives_removal_of_previous_nested_key(
    answers_path,
):
    _il5_answers(
        answers_path,
        [
            (
                "  regime: IL5\n",
                "  location: us-west1\n  # Lab runs IL5.\n  regime: IL5\n",
            )
        ],
    )
    saved = _save_without(answers_path, "compliance.location")
    assert "compliance:\n  # Lab runs IL5.\n  regime: IL5\n" in saved


def test_save_does_not_modify_previous(answers_path):
    answers_lib.save(answers_path, helpers.minimal_answers())
    previous = answers_lib.load_data(answers_path)
    answers_lib.save(
        answers_path, helpers.minimal_answers(prefix="abc"), previous=previous
    )
    assert previous["prefix"] == "tst"


def test_save_replaces_atomically_with_private_mode(answers_path):
    answers_path.parent.mkdir(parents=True)
    answers_path.write_text("old: true\n", encoding="utf-8")
    answers_path.chmod(0o644)
    answers_lib.save(answers_path, helpers.minimal_answers())
    assert conftest.mode(answers_path) == 0o600
    assert [path.name for path in answers_path.parent.iterdir()] == [
        "answers.yaml"
    ]


def test_save_rejects_values_inside_the_home(answers_path):
    home = answers_path.parents[2]
    answers = helpers.minimal_answers(
        overrides={"0-bootstrap": {"outputs_location": str(home / "x")}}
    )
    with pytest.raises(answers_lib.AnswersError, match="points into the home"):
        answers_lib.save(answers_path, answers, home=home)
    assert not answers_path.exists()


def test_save_without_a_home_skips_the_home_check(tmp_path):
    path = tmp_path / "answers.yaml"
    answers = helpers.minimal_answers(
        overrides={"0-bootstrap": {"outputs_location": str(tmp_path)}}
    )
    answers_lib.save(path, answers)
    assert answers_lib.load(path) == answers


def test_load_empty_file_is_an_empty_map(tmp_path):
    path = tmp_path / "answers.yaml"
    path.write_text("# nothing yet\n", encoding="utf-8")
    assert dict(answers_lib.load_data(path)) == {}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("prefix: [unterminated\n", "not valid YAML"),
        ("- a\n- b\n", "must contain a mapping"),
    ],
)
def test_load_data_errors(tmp_path, text, message):
    path = tmp_path / "answers.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(answers_lib.AnswersError, match=message):
        answers_lib.load_data(path)


def test_load_missing_file(tmp_path):
    with pytest.raises(answers_lib.AnswersError, match="Cannot read"):
        answers_lib.load(tmp_path / "missing.yaml")


def test_load_reports_every_invalid_field(tmp_path):
    path = tmp_path / "answers.yaml"
    path.write_text("prefix: Bad\nbilling: {}\n", encoding="utf-8")
    with pytest.raises(answers_lib.AnswersError) as error:
        answers_lib.load(path)
    message = str(error.value)
    assert "- prefix: String should match pattern" in message
    assert "- billing.account_id: Field required" in message
    assert "- organization: Field required" in message


def test_apply_sets_parses_yaml_values():
    data = {"billing": {"account_id": conftest.BILLING}}
    result = answers_lib.apply_sets(
        data,
        [
            "billing.no_iam=true",
            "org_policies.allowed_policy_member_domains=[C01, C02]",
            "resman.tenants.ten1={descriptive_name: tenant-1}",
            "organization.id=123456789012",
            "bootstrap_user=null",
            "budget.amount=1000",
            "alert_email=",
            "region=no",
        ],
    )
    assert result == {
        "billing": {"account_id": conftest.BILLING, "no_iam": True},
        "org_policies": {"allowed_policy_member_domains": ["C01", "C02"]},
        "resman": {"tenants": {"ten1": {"descriptive_name": "tenant-1"}}},
        "organization": {"id": 123456789012},
        "bootstrap_user": None,
        "budget": {"amount": 1000},
        "alert_email": "",
        "region": "no",
    }
    assert data == {"billing": {"account_id": conftest.BILLING}}


def test_apply_sets_keeps_leading_zeros():
    result = answers_lib.apply_sets({}, ["a=0123", "b=1e3", "c=12"])
    assert result == {"a": "0123", "b": "1e3", "c": 12}


def test_apply_sets_quoted_segments_hold_addresses():
    result = answers_lib.apply_sets(
        {},
        [
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            'imports.0-bootstrap."module.a[\\"k=v\\"].x.y"=id=with=equals',
        ],
    )
    assert result == {
        "imports": {
            "0-bootstrap": {
                conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0",
                'module.a["k=v"].x.y': "id=with=equals",
            }
        }
    }


def test_apply_sets_result_validates():
    data = answers_lib.apply_sets(
        helpers.minimal_data(),
        ["organization.id=123456789012", "billing.no_iam=true"],
    )
    answers = answers_lib.parse(data)
    assert answers.organization.id == "123456789012"
    assert answers.billing.no_iam


@pytest.mark.parametrize(
    "assignment",
    [
        "no-equals",
        "=value",
        "a..b=1",
        "a.=1",
        '"unterminated=1',
        '"a"b=1',
        '""=1',
    ],
)
def test_apply_sets_rejects_malformed(assignment):
    with pytest.raises(ValueError):
        answers_lib.apply_sets({}, [assignment])


def test_apply_sets_rejects_path_through_a_value():
    with pytest.raises(ValueError, match="prefix is not a map"):
        answers_lib.apply_sets({"prefix": "tst"}, ["prefix.x=1"])


def test_apply_sets_rejects_unparsable_value():
    with pytest.raises(ValueError, match="Cannot parse value"):
        answers_lib.apply_sets({}, ["a=[1, 2"])


def test_from_config_env(tmp_path):
    path = tmp_path / "config.env"
    path.write_text(
        "\n".join(
            [
                f"BILLING_ACCOUNT={conftest.BILLING}",
                f"BOOTSTRAP_PROJECT_ID={conftest.PROJECT}",
                "COMPLIANCE_REGIME=il5",
                f"DIRECTORY_CUSTOMER_ID={conftest.CUSTOMER_ID}",
                f"DEPLOYER_EMAIL_ADDRESS={conftest.USER}",
                f"FULLY_QUALIFIED_DOMAIN_NAME={conftest.DOMAIN}",
                f"LOGGING_ALERTS_EMAIL_ADDRESS=alerts@{conftest.DOMAIN}",
                f"ORGANIZATION_ID={conftest.ORG_ID}",
                "PREFIX=tst",
                "REGION=us-east4",
                "AW_REGION=us-east4",
                "TENANT_NAME=ten1",
            ]
        ),
        encoding="utf-8",
    )
    data = answers_lib.from_config_env(path)
    assert data == {
        "prefix": "tst",
        "organization": {
            "id": conftest.ORG_ID,
            "domain": conftest.DOMAIN,
            "customer_id": conftest.CUSTOMER_ID,
        },
        "billing": {"account_id": conftest.BILLING},
        "bootstrap_project": conftest.PROJECT,
        "region": "us-east4",
        "compliance": {"regime": "IL5"},
        "alert_email": f"alerts@{conftest.DOMAIN}",
        "bootstrap_user": conftest.USER,
        "resman": {"tenants": {"ten1": {"descriptive_name": "ten1"}}},
    }
    answers_lib.parse(data)


def test_from_config_env_partial_values(tmp_path):
    path = tmp_path / "config.env"
    path.write_text(
        "PREFIX=tst\nREGION=us-east4\nAW_REGION=us\n"
        "DEPLOYER_EMAIL_ADDRESS=tf@x.iam.gserviceaccount.com\n",
        encoding="utf-8",
    )
    assert answers_lib.from_config_env(path) == {
        "prefix": "tst",
        "region": "us-east4",
        "compliance": {"location": "us"},
    }


def test_from_config_env_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        answers_lib.from_config_env(tmp_path / "missing.env")


def test_to_preflight():
    answers = helpers.minimal_answers(
        bootstrap_user=conftest.USER,
        billing={"account_id": conftest.BILLING, "no_iam": True},
        groups={"gcp-devops": "platform"},
        resman={
            "envs": {"Prod": {}},
            "tenants": {"ten1": {"descriptive_name": "Tenant"}},
        },
        imports={
            "0-bootstrap": {
                conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0",
                conftest.LOG_EXPORT_ADDRESS: ("tst-prod-audit-logs-0"),
                "module.x.google_storage_bucket.bucket[0]": "a-bucket",
            },
            "1-resman": {
                'module.tenant-self-iac-projects["prod-ten1"]'
                ".google_project.project[0]": "tst-prod-ten1-iac-core-0",
            },
        },
        existing_org_policies=["iam.allowedPolicyMemberDomains"],
    )
    values = answers_lib.to_preflight(answers)
    assert values == {
        "org_id": conftest.ORG_ID,
        "billing_account": conftest.BILLING,
        "billing_no_iam": True,
        "billing_is_org_level": True,
        "bootstrap_project": conftest.PROJECT,
        "prefix": "tst",
        "regime": "IL5",
        "region": "us-east4",
        "domain": conftest.DOMAIN,
        "customer_id": conftest.CUSTOMER_ID,
        "bootstrap_user": conftest.USER,
        "groups": {"gcp-devops": "platform"},
        "tenant_project_ids": (
            "tst-prod-ten1-iac-core-0",
            "tst-prod-ten1-main-0",
        ),
        "imported_project_ids": (
            "tst-prod-audit-logs-0",
            "tst-prod-iac-core-0",
            "tst-prod-ten1-iac-core-0",
        ),
        "imported_addresses": (
            conftest.AUTOMATION_ADDRESS,
            conftest.LOG_EXPORT_ADDRESS,
            "module.x.google_storage_bucket.bucket[0]",
        ),
        "billing_budget": False,
        "existing_org_policies": ("iam.allowedPolicyMemberDomains",),
    }


def test_to_preflight_reports_a_budget():
    # Stage 0 creates the budget on the billing account, so preflight needs
    # to know about it to judge billing access.
    answers = helpers.minimal_answers().model_copy(
        update={"budget": models.Budget(amount=100)}
    )
    assert answers_lib.to_preflight(answers)["billing_budget"] is True


def test_to_preflight_fits_preflight_inputs():
    values = answers_lib.to_preflight(
        helpers.minimal_answers(bootstrap_user=None, stage0_phase="final")
    )
    assert "bootstrap_user" not in values
    known = set(inputs_lib.PreflightInputs.model_fields)
    assert set(values) <= known
    inputs_lib.PreflightInputs.model_validate(
        {key: value for key, value in values.items() if key in known}
    )
