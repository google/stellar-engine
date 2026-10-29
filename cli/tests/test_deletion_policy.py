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

"""Tests for keeping imported Stage 0 projects on destroy."""

import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import derive
from stellar_engine.config import seed
from stellar_engine.config import validate
from stellar_engine.render import hcl
from stellar_engine.render import stages
from stellar_engine.wizard import discovery
from stellar_engine.wizard import flow
from stellar_engine.wizard import prompts

# The worktree of the Stage 0 change that adds project_deletion_policies,
# present only on machines that check it out.
KEYS = {
    "automation-project": "automation",
    "log-export-project": "logging",
    repo_lib.BILLING_EXPORT_MODULE: "billing",
}
KEEP_QUESTION = "Keep these projects when Stage 0 is destroyed?"
EXPECTED_BLOCK = """\
# Deletion policy of the Stage 0 projects that the imports adopt.
# stellar writes ABANDON while keep_imported_projects is true in
# answers.yaml, so terraform destroy keeps those projects.
project_deletion_policies = {
  automation = "ABANDON"
  logging    = "ABANDON"
}
"""


@pytest.fixture
def policy_repo(tmp_path):
    """Returns a Repo whose Stage 0 declares project_deletion_policies."""
    return repo_lib.Repo(helpers.deletion_policy_engine(tmp_path / "engine"))


@pytest.fixture
def legacy_repo(tmp_path):
    """Returns a Repo whose Stage 0 lacks project_deletion_policies."""
    return repo_lib.Repo(
        helpers.deletion_policy_engine(tmp_path / "legacy", declared=False)
    )


def _bootstrap(repo, name="lab", **updates):
    answers = helpers.load_fixture(name, **updates)
    return stages.build(
        paths.BOOTSTRAP, answers, repo, helpers.env_paths(answers)
    )


def _all_imports(prefix="lab1"):
    return {
        paths.BOOTSTRAP: {
            conftest.AUTOMATION_ADDRESS: f"{prefix}-prod-iac-core-0",
            conftest.LOG_EXPORT_ADDRESS: f"{prefix}-prod-audit-logs-0",
            conftest.BILLING_EXPORT_ADDRESS: f"{prefix}-prod-billing-exp-0",
        }
    }


def test_keys_are_empty_without_the_variable(legacy_repo):
    assert legacy_repo.project_deletion_policy_keys() == {}
    assert set(legacy_repo.stage0_deletion_policies().values()) == {"DELETE"}


def test_keys_come_from_the_project_modules(policy_repo):
    assert policy_repo.project_deletion_policy_keys() == KEYS
    assert policy_repo.stage0_deletion_policies() == dict.fromkeys(
        KEYS, "DELETE"
    )


def test_default_policy_follows_the_variable_type(policy_repo):
    # Nothing has read the copied files yet, so the edit is what parses.
    variables = policy_repo.bootstrap_dir / "variables.tf"
    text = variables.read_text(encoding="utf-8")
    variables.write_text(
        text.replace(
            'optional(string, "DELETE")\n  })',
            'optional(string, "PREVENT")\n  })',
        ),
        encoding="utf-8",
    )
    assert policy_repo.stage0_deletion_policies()["log-export-project"] == (
        "PREVENT"
    )


def test_render_abandons_imported_projects(policy_repo):
    rendered = _bootstrap(policy_repo)
    # The lab answers set billing.no_iam, so Stage 0 creates no billing
    # export project and the billing key stays at its default.
    assert rendered.values["project_deletion_policies"] == {
        "automation": "ABANDON",
        "logging": "ABANDON",
    }
    assert f"\n\n{EXPECTED_BLOCK}\n" in rendered.text
    assert hcl.loads(rendered.text) == rendered.values


def test_render_includes_an_imported_billing_export_project(policy_repo):
    rendered = _bootstrap(
        policy_repo,
        billing={"account_id": conftest.BILLING},
        imports=_all_imports(),
    )
    assert rendered.values["project_deletion_policies"] == {
        "automation": "ABANDON",
        "logging": "ABANDON",
        "billing": "ABANDON",
    }


@pytest.mark.parametrize(
    "updates", [{"keep_imported_projects": False}, {"imports": {}}]
)
def test_render_omits_the_key(policy_repo, updates):
    rendered = _bootstrap(policy_repo, **updates)
    assert "project_deletion_policies" not in rendered.values
    assert "project_deletion_policies" not in rendered.text


def test_render_without_the_variable_omits_the_key_and_warns(legacy_repo):
    rendered = _bootstrap(legacy_repo)
    assert "project_deletion_policies" not in rendered.values
    answers = helpers.load_fixture("lab")
    assert stages.warnings(answers, "0", legacy_repo) == [
        "keep_imported_projects is true, but this engine version of "
        "0-bootstrap cannot keep imported projects on destroy yet, so "
        "terraform destroy deletes lab1-prod-iac-core-0, "
        "lab1-prod-audit-logs-0."
    ]


@pytest.mark.parametrize(
    ("stage", "updates"),
    [
        ("0", {"keep_imported_projects": False}),
        ("0", {"imports": {}}),
        ("1", {}),
    ],
)
def test_no_warning_when_nothing_is_kept(legacy_repo, stage, updates):
    answers = helpers.load_fixture("lab", **updates)
    assert stages.warnings(answers, stage, legacy_repo) == []


def test_no_warning_when_the_variable_exists(policy_repo):
    answers = helpers.load_fixture("lab")
    assert stages.warnings(answers, "0", policy_repo) == []


def test_effective_policies(policy_repo, legacy_repo):
    answers = helpers.load_fixture("lab")
    assert derive.stage0_deletion_policies(answers, policy_repo) == {
        "lab1-prod-iac-core-0": "ABANDON",
        "lab1-prod-audit-logs-0": "ABANDON",
    }
    assert derive.stage0_deletion_policies(answers, legacy_repo) == {
        "lab1-prod-iac-core-0": "DELETE",
        "lab1-prod-audit-logs-0": "DELETE",
    }


def test_override_is_cli_owned_when_declared(policy_repo, legacy_repo):
    answers = helpers.minimal_answers(
        overrides={
            paths.BOOTSTRAP: {
                "project_deletion_policies": {"automation": "ABANDON"}
            }
        }
    )
    found = validate.stage_override_problems(
        answers, policy_repo, paths.BOOTSTRAP
    )
    assert len(found) == 1
    assert "keep_imported_projects" in found[0]
    with pytest.raises(stages.RenderError, match="keep_imported_projects"):
        stages.build(
            paths.BOOTSTRAP, answers, policy_repo, helpers.env_paths(answers)
        )
    # An engine without the variable rejects it as an unknown variable.
    found = validate.stage_override_problems(
        answers, legacy_repo, paths.BOOTSTRAP
    )
    assert len(found) == 1
    assert "declares no such variable" in found[0]


def test_seed_carries_the_preference():
    data = helpers.minimal_data(
        keep_imported_projects=False, imports=_all_imports("tst")
    )
    carried = seed.seed(data)
    assert carried["keep_imported_projects"] is False
    assert "imports" not in carried


def test_answers_default_to_keeping():
    assert helpers.minimal_answers().keep_imported_projects is True


@pytest.fixture
def discovered(cloud, local_tools):
    return discovery.discover(cloud, local_tools)


@pytest.mark.parametrize(
    ("data", "answer", "expected"),
    [
        ({}, None, True),
        ({}, False, False),
        ({"keep_imported_projects": False}, None, False),
    ],
)
def test_wizard_asks_after_precreated_projects(
    repo, discovered, data, answer, expected
):
    prompter = prompts.ScriptedPrompter([None, True, answer])
    result = flow.run(
        helpers.minimal_data(**data),
        prompter=prompter,
        repo=repo,
        discovered=discovered,
        sections=["bootstrap"],
    )
    assert prompter.answers == []
    assert prompter.asked[-1] == KEEP_QUESTION
    assert result["keep_imported_projects"] is expected


def test_wizard_skips_the_question_without_precreated_projects(
    repo, discovered
):
    prompter = prompts.ScriptedPrompter([None, False])
    result = flow.run(
        helpers.minimal_data(),
        prompter=prompter,
        repo=repo,
        discovered=discovered,
        sections=["bootstrap"],
    )
    assert prompter.answers == []
    assert KEEP_QUESTION not in prompter.asked
    assert "keep_imported_projects" not in result


def test_engine_shapes_wire_the_variable_once(legacy_repo, policy_repo):
    # Each shape declares the variable at most once and wires each project
    # module at most once, whichever shape the checkout has.
    for engine, count in ((legacy_repo, 0), (policy_repo, 1)):
        bootstrap = engine.bootstrap_dir
        text = (bootstrap / "variables.tf").read_text(encoding="utf-8")
        assert text.count('variable "project_deletion_policies"') == count
        for filename in ("automation.tf", "log-export.tf", "billing.tf"):
            text = (bootstrap / filename).read_text(encoding="utf-8")
            assert text.count("var.project_deletion_policies.") == count


def test_bootstrap_section_owns_the_field():
    assert flow.owners("keep_imported_projects") == ("bootstrap",)
