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

"""Tests for the stage tfvars builders."""

import shutil

import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine.config import validate
from stellar_engine.render import hcl
from stellar_engine.render import stages


def _build(repo, stage, name="fedramp_high", **updates):
    return helpers.render(repo, name, stage, **updates)


@pytest.mark.parametrize("stage", paths.STAGES)
@pytest.mark.parametrize("name", helpers.ALL_FIXTURES)
def test_snapshot(name, stage, repo, snapshot):
    rendered = helpers.render(repo, name, stage)
    assert rendered.stage == stage
    assert rendered.text == snapshot


@pytest.mark.parametrize("stage", paths.STAGES)
@pytest.mark.parametrize("name", helpers.ALL_FIXTURES)
def test_text_parses_back_to_values(name, stage, repo):
    rendered = helpers.render(repo, name, stage)
    assert hcl.loads(rendered.text) == rendered.values
    assert list(hcl.loads(rendered.text)) == list(rendered.values)


def test_aliases_resolve(repo):
    answers = helpers.load_fixture("fedramp_high")
    env = helpers.env_paths(answers)
    assert stages.build("0", answers, repo, env).stage == "0-bootstrap"
    assert stages.build("1", answers, repo, env).stage == "1-resman"


def test_unknown_stage(repo):
    answers = helpers.load_fixture("fedramp_high")
    with pytest.raises(ValueError, match="2-networking"):
        stages.build("2-networking", answers, repo, helpers.env_paths(answers))


def test_header_names_sources(repo):
    text = _build(repo, "0-bootstrap").text
    lines = text.splitlines()
    assert lines[0] == (
        "# stellar render writes this file from "
        "fast/stages-aw/0-bootstrap/terraform.tfvars.sample and "
        "envs/frh/answers.yaml."
    )
    assert lines[1] == (
        "# Edit answers.yaml and rerun stellar render; manual edits trigger "
        "an overwrite prompt."
    )


def test_stage0_follows_sample_order(repo):
    values = _build(repo, "0-bootstrap", "fedramp_moderate").values
    assert list(values) == [
        "billing_account",
        "billing_budget_amount",
        "regions",
        "organization",
        "outputs_location",
        "logging_bucket_retention",
        "prefix",
        "log_sinks",
        "org_policies_config",
        "fast_features",
        "assured_workloads",
        "bootstrap_project",
        "alert_email",
        "kms_protection_level",
        "essential_contacts",
        "groups",
    ]


def test_stage0_minimal_values(repo, tmp_path):
    answers = helpers.load_fixture("fedramp_high")
    env = helpers.env_paths(answers, home=tmp_path)
    values = stages.build("0", answers, repo, env).values
    assert values["billing_account"] == {"id": conftest.BILLING}
    assert values["organization"] == {
        "domain": conftest.DOMAIN,
        "id": int(conftest.ORG_ID),
        "customer_id": conftest.CUSTOMER_ID,
    }
    assert values["outputs_location"] == str(env.fast_config)
    assert values["assured_workloads"] == {
        "regime": "FEDRAMP_HIGH",
        "location": "us-east4",
    }
    assert values["kms_protection_level"] == "HSM"
    for absent in (
        "billing_budget_amount",
        "logging_bucket_retention",
        "essential_contacts",
        "groups",
        "billing_override",
        "bootstrap_user",
    ):
        assert absent not in values


def test_stage0_never_writes_bootstrap_user(repo):
    rendered = _build(repo, "0", "lab", bootstrap_user=conftest.USER)
    assert "bootstrap_user" not in rendered.values
    assert conftest.USER not in rendered.text


def test_stage0_billing_flags_only_when_not_default(repo):
    assert _build(repo, "0", "il4").values["billing_account"] == {
        "id": conftest.BILLING,
        "is_org_level": False,
    }
    assert _build(repo, "0", "lab").values["billing_account"] == {
        "id": conftest.BILLING,
        "no_iam": True,
    }


def test_stage0_kms_level_is_derived_or_explicit(repo):
    moderate = _build(repo, "0", "fedramp_moderate")
    assert moderate.values["kms_protection_level"] == "SOFTWARE"
    assert "stellar derives it from the" in moderate.text
    explicit = _build(repo, "0", "il5")
    assert explicit.values["kms_protection_level"] == "SOFTWARE"
    assert "which answers.yaml sets" in explicit.text
    assert "Leave unset" not in explicit.text


def test_stage0_log_sink_type_replaces_sample_type(repo):
    sinks = _build(repo, "0", "fedramp_moderate").values["log_sinks"]
    assert set(sinks) == set(repo.log_sink_names())
    assert {sink["type"] for sink in sinks.values()} == {"storage"}


def test_stage0_groups_only_renamed(repo):
    values = _build(repo, "0", "fedramp_moderate").values
    assert values["groups"] == {"gcp-devops": "platform-devops"}


def test_stage0_drs_list(repo):
    constraints = _build(repo, "0", "lab").values["org_policies_config"]
    assert constraints == {
        "import_defaults": False,
        "constraints": {
            "allowed_policy_member_domains": [
                "is:C0AAAAAAA",
                "is:C0BBBBBBB",
                "is:principalSet://iam.googleapis.com/organizations/"
                "123456789012",
            ]
        },
    }


def test_stage0_compliance_location_override(repo):
    location = _build(repo, "0", "il4").values["assured_workloads"]["location"]
    assert location == "us"


def test_overrides_merge_last(repo):
    rendered = _build(
        repo,
        "0",
        overrides={
            "0-bootstrap": {
                "org_policies_config": {"import_defaults": True},
                "iam": {"roles/viewer": ["group:viewers@example.com"]},
                "regions": {"primary": "us-west1"},
            }
        },
    )
    assert rendered.values["org_policies_config"] == {
        "import_defaults": True,
        "constraints": {"allowed_policy_member_domains": []},
    }
    assert rendered.values["regions"] == {"primary": "us-west1"}
    assert list(rendered.values)[-1] == "iam"
    assert (
        "# overrides.0-bootstrap in answers.yaml sets this value.\niam = {"
        in (rendered.text)
    )
    # A sample key keeps its guidance comment when an override changes it.
    assert "# Default to us-east4 for IL5/FedRAMP High/Moderate" in (
        rendered.text
    )


def test_overrides_list_replaces(repo):
    rendered = _build(
        repo,
        "0",
        "lab",
        overrides={
            "0-bootstrap": {
                "org_policies_config": {
                    "constraints": {"allowed_policy_member_domains": ["C0X"]}
                }
            }
        },
    )
    constraints = rendered.values["org_policies_config"]["constraints"]
    assert constraints["allowed_policy_member_domains"] == ["C0X"]


def test_override_of_auto_key_is_rejected(repo):
    with pytest.raises(stages.RenderError, match=r"prefix.*auto\.tfvars"):
        _build(repo, "1", overrides={"1-resman": {"prefix": "other"}})


def test_override_of_unknown_variable_is_rejected(repo):
    with pytest.raises(
        stages.RenderError,
        match="sets not_a_var, but 0-bootstrap declares no such",
    ):
        _build(repo, "0", overrides={"0-bootstrap": {"not_a_var": 1}})


@pytest.mark.parametrize(
    ("stage", "key"),
    [
        ("0-bootstrap", "prefix"),
        ("0-bootstrap", "outputs_location"),
        ("0-bootstrap", "bootstrap_user"),
        ("1-resman", "outputs_location"),
    ],
)
def test_override_of_cli_owned_key_is_rejected(repo, stage, key):
    with pytest.raises(stages.RenderError, match=f"sets {key}, which stellar"):
        _build(repo, stage, overrides={stage: {key: "other"}})


def test_override_problems_cover_every_stage(repo):
    answers = helpers.load_fixture("il5").model_copy(
        update={
            "overrides": {
                "0-bootstrap": {"not_a_var": 1, "iam": {}},
                "1-resman": {"prefix": "zzz"},
            }
        }
    )
    found = validate.override_problems(answers, repo)
    assert len(found) == 2
    assert "overrides.0-bootstrap sets not_a_var" in found[0]
    assert "overrides.1-resman sets prefix" in found[1]


def test_surviving_placeholder_is_rejected(repo):
    with pytest.raises(stages.RenderError, match=r"iam\.roles/viewer"):
        _build(
            repo,
            "0",
            overrides={
                "0-bootstrap": {"iam": {"roles/viewer": ["user:<user>"]}}
            },
        )


def test_placeholder_in_key_is_rejected(repo):
    with pytest.raises(stages.RenderError, match="placeholders"):
        _build(
            repo,
            "0",
            overrides={"0-bootstrap": {"iam": {"<role>": ["user:a@b.c"]}}},
        )


def test_stage1_values(repo, tmp_path):
    answers = helpers.load_fixture("fedramp_moderate")
    env = helpers.env_paths(answers, home=tmp_path)
    values = stages.build("1-resman", answers, repo, env).values
    assert list(values) == ["tenants", "envs_folders", "outputs_location"]
    assert values["tenants"] == {
        "apps": {
            "admin_principal": "group:apps-admins@example.com",
            "descriptive_name": "Applications",
            "locations": {"gcs": "us", "kms": "us-central1"},
        }
    }
    assert values["envs_folders"] == {
        env_key: {"admin": "gcp-organization-admins@example.com"}
        for env_key in ("Prod", "Int", "Test")
    }
    assert values["outputs_location"] == str(env.fast_config)


def test_stage1_default_admin_follows_renamed_group(repo):
    tenant = _build(
        repo,
        "1",
        "fedramp_moderate",
        resman={"tenants": {"web": {"descriptive_name": "Web"}}},
    ).values["tenants"]["web"]
    assert tenant["admin_principal"] == "group:platform-devops@example.com"
    assert tenant["locations"] == {"gcs": "us-central1", "kms": "us-central1"}


def test_stage1_sample_tenants_never_leak(repo):
    values = _build(repo, "1", "unspecified").values
    assert values["tenants"] == {}
    text = _build(repo, "1", "fedramp_high").text
    assert "ten-1" not in text
    assert "ten-2" not in text


def test_stage1_drops_auto_keys(repo):
    values = _build(repo, "1", "lab").values
    assert "fast_features" not in values
    assert not set(values) & repo.auto_tfvars_keys("1-resman")


def test_stage1_billing_override(repo):
    values = _build(repo, "1", "lab").values
    assert values["billing_override"] == {
        "project": conftest.PROJECT,
        "billing_project": conftest.PROJECT,
    }


@pytest.mark.terraform
@pytest.mark.parametrize("stage", paths.STAGES)
@pytest.mark.parametrize("name", helpers.ALL_FIXTURES)
def test_terraform_fmt_keeps_text(name, stage, repo):
    text = helpers.render(repo, name, stage).text
    result = helpers.terraform_fmt(text)
    assert result.returncode == 0, result.stderr
    assert result.stdout == text


@pytest.mark.terraform
@pytest.mark.parametrize("stage", paths.STAGES)
@pytest.mark.parametrize("name", helpers.ALL_FIXTURES)
def test_terraform_accepts_variables(name, stage, repo, tmp_path):
    # Only variables.tf and the inputs: a plan with no resources still
    # converts every value to its declared type and runs every validation,
    # without credentials or providers.
    answers = helpers.load_fixture(name)
    env = helpers.env_paths(answers, home=tmp_path / "home")
    rendered = stages.build(stage, answers, repo, env)
    harness = tmp_path / "harness"
    harness.mkdir()
    stage_dir = paths.stage_dir(repo.root, stage)
    shutil.copy(stage_dir / "variables.tf", harness / "variables.tf")
    (harness / "terraform.tfvars").write_text(rendered.text, encoding="utf-8")
    if stage == "1-resman":
        for path in helpers.STAGE_OUTPUTS_DIR.glob("*.auto.tfvars.json"):
            shutil.copy(path, harness / path.name)
    helpers.terraform_init(harness)
    plan = helpers.terraform(harness, "plan", "-input=false")
    assert plan.returncode == 0, plan.stderr
    # Stage 0 outputs keys such as `logging` that Stage 1 does not declare,
    # so only the rendered file must be free of undeclared variables.
    assert 'file "terraform.tfvars"' not in plan.stdout + plan.stderr
