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

"""Tests for the `stellar init` command."""

import pytest
from ruamel import yaml

import conftest
import helpers
import helpers_deploy
from stellar_engine import cli
from stellar_engine import paths
from stellar_engine.commands import common
from stellar_engine.config import answers as answers_lib
from stellar_engine.deploy import run_state
from stellar_engine.wizard import flow

pytestmark = pytest.mark.usefixtures("isolated_home")


def test_init_non_interactive_with_sets(cli_runner, isolated_home):
    outcome = helpers.init_env(
        cli_runner,
        sets=(
            "billing.no_iam=true",
            "org_policies.allowed_policy_member_domains=[is:C0AAAAAAA, "
            '"is:principalSet://iam.googleapis.com/organizations/'
            f'{conftest.ORG_ID}"]',
            "resman.tenants.ten1={descriptive_name: tenant-1}",
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            'overrides.0-bootstrap.iam={"roles/viewer": '
            '["user:admin@example.com"]}',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    answers = helpers.load_answers(isolated_home)
    assert answers.organization.id == conftest.ORG_ID
    assert answers.billing.no_iam is True
    assert answers.org_policies.allowed_policy_member_domains[1].startswith(
        "is:principalSet://"
    )
    assert answers.resman.tenants["ten1"].descriptive_name == "tenant-1"
    assert answers.imports == {
        "0-bootstrap": {conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0"}
    }
    assert answers.overrides["0-bootstrap"]["iam"] == {
        "roles/viewer": ["user:admin@example.com"]
    }
    assert answers.engine is not None
    assert answers.engine.path == str(conftest.REPO_ROOT)
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    assert conftest.mode(path) == 0o600
    assert (isolated_home / "answers.schema.json").is_file()
    assert (isolated_home / ".gitignore").is_file()
    assert (isolated_home / "current").read_text().strip() == "tst"
    assert "Next: stellar render" in outcome.output


def test_init_reports_every_problem(cli_runner, isolated_home):
    outcome = helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--prefix",
        "tst",
        "--set",
        "region=us-east4",
    )
    assert outcome.exit_code == 2
    for field in ("organization", "billing", "compliance", "alert_email"):
        assert field in outcome.output
    assert not (isolated_home / "envs" / "tst").exists()


def test_init_rejects_repo_rules(cli_runner, isolated_home):
    outcome = helpers.init_env(cli_runner, sets=("region=europe-west1",))
    assert outcome.exit_code == 2
    assert "region europe-west1" in outcome.output


def test_init_malformed_set_exits_2(cli_runner):
    outcome = helpers.init_env(cli_runner, sets=("nonsense",))
    assert outcome.exit_code == 2
    assert "KEY=VALUE" in outcome.output


def test_section_needs_interactive(cli_runner):
    outcome = helpers.init_env(cli_runner, "tst", "--section", "groups")
    assert outcome.exit_code == 2
    assert "interactive" in outcome.output


def test_init_rerun_keeps_comments(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    text = path.read_text().replace(
        "region: us-east4", "# Closest to the operators.\nregion: us-east4"
    )
    path.write_text(text)
    outcome = helpers.invoke(
        cli_runner, "init", "--non-interactive", "--set", "budget.amount=100"
    )
    assert outcome.exit_code == 0, outcome.output
    saved = path.read_text()
    assert "# Closest to the operators.\nregion: us-east4" in saved
    assert helpers.load_answers(isolated_home).budget.amount == 100


def test_init_repairs_answers_that_fail_the_model(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    text = path.read_text()
    assert "region: us-east4" in text
    path.write_text(text.replace("region: us-east4", "region: [1]"))
    outcome = helpers.invoke(
        cli_runner,
        "init",
        "--prefix",
        "tst",
        "--non-interactive",
        "--offline",
        "--set",
        "region=us-east4",
    )
    assert outcome.exit_code == 0, outcome.output
    assert helpers.load_answers(isolated_home).region == "us-east4"


def test_init_refuses_to_replace_another_env(cli_runner):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = helpers.init_env(
        cli_runner, None, "--answers-from", "tst", sets=("prefix=tst",)
    )
    assert outcome.exit_code == 2
    assert "already exists" in outcome.output


def test_answers_from_seeds_and_notes_regime_change(cli_runner, isolated_home):
    first = helpers.init_env(
        cli_runner,
        sets=(
            "kms_protection_level=HSM",
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
        ),
    )
    assert first.exit_code == 0, first.output
    outcome = helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--prefix",
        "new",
        "--answers-from",
        "tst",
        "--set",
        "compliance.regime=FEDRAMP_MODERATE",
    )
    assert outcome.exit_code == 0, outcome.output
    assert "Seeding from" in outcome.output
    assert "kms_protection_level HSM is explicit" in outcome.output
    assert "the copy drops the imports" in outcome.output
    seeded = helpers.load_answers(isolated_home, "new")
    assert seeded.prefix == "new"
    assert seeded.organization.domain == conftest.DOMAIN
    assert seeded.compliance.regime == "FEDRAMP_MODERATE"
    assert seeded.imports == {}
    assert (isolated_home / "current").read_text().strip() == "new"


def test_answers_from_a_file(cli_runner, isolated_home, tmp_path):
    assert helpers.init_env(cli_runner).exit_code == 0
    source = tmp_path / "elsewhere.yaml"
    source.write_text(
        (isolated_home / "envs" / "tst" / "answers.yaml").read_text()
    )
    outcome = helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--prefix",
        "oth",
        "--answers-from",
        str(source),
    )
    assert outcome.exit_code == 0, outcome.output
    assert helpers.load_answers(isolated_home, "oth").region == "us-east4"


def test_new_prefix_suggests_one(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--answers-from",
        "tst",
        "--new-prefix",
    )
    assert outcome.exit_code == 0, outcome.output
    current = (isolated_home / "current").read_text().strip()
    assert current != "tst"
    assert current.startswith("tst")
    assert len(current) <= 7
    assert f"Suggested prefix {current}." in outcome.output
    assert helpers.load_answers(isolated_home, current).prefix == current


def test_interactive_init_runs_the_wizard(
    cli_runner, isolated_home, fake_tools, monkeypatch
):
    calls = {}

    def fake_run(data, *, prompter, repo, discovered, sections):
        calls["sections"] = sections
        calls["discovered"] = discovered
        return {**data, "alert_email": "wizard@example.com"}

    monkeypatch.setattr(common, "stdin_is_tty", lambda: True)
    monkeypatch.setattr(flow, "run", fake_run)
    outcome = cli_runner.invoke(
        cli.app,
        [
            "init",
            "--prefix",
            "tst",
            "--offline",
            "--section",
            "contacts",
            *helpers.set_args(),
            "--repo",
            str(conftest.REPO_ROOT),
        ],
    )
    assert outcome.exit_code == 0, outcome.output
    assert calls["sections"] == ["contacts"]
    assert calls["discovered"].organizations == ()
    assert calls["discovered"].gcloud_account == conftest.USER
    assert (
        helpers.load_answers(isolated_home).alert_email == "wizard@example.com"
    )


def test_saved_answers_are_valid_yaml(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner).exit_code == 0
    text = (isolated_home / "envs" / "tst" / "answers.yaml").read_text()
    assert text.startswith(answers_lib.SCHEMA_COMMENT + "\n")
    assert yaml.YAML(typ="safe").load(text)["prefix"] == "tst"


@pytest.mark.parametrize(
    "args",
    [
        ["--set", "prefix=xyz"],
        ["--prefix", "abc", "--set", "prefix=xyz"],
    ],
)
def test_init_refuses_to_change_the_prefix(cli_runner, isolated_home, args):
    outcome = helpers.init_env(
        cli_runner,
        "abc",
        sets=(
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=abc-prod-iac-core-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    changed = helpers.invoke(cli_runner, "init", "--non-interactive", *args)
    assert changed.exit_code == 2
    assert "stellar init --answers-from abc --prefix xyz" in changed.output
    assert not (isolated_home / "envs" / "xyz").exists()


def test_init_rejects_overrides_that_render_would_reject(
    cli_runner, isolated_home
):
    outcome = helpers.init_env(
        cli_runner,
        sets=(
            "overrides.0-bootstrap.prefix=other",
            "overrides.0-bootstrap.not_a_var=1",
            "overrides.1-resman.prefix=zzz",
        ),
    )
    assert outcome.exit_code == 2
    assert "overrides.0-bootstrap sets prefix, which stellar" in outcome.output
    assert "overrides.0-bootstrap sets not_a_var" in outcome.output
    assert "overrides.1-resman sets prefix" in outcome.output
    assert not (isolated_home / "envs" / "tst").exists()


def test_init_rejects_import_ids_of_another_prefix(cli_runner, isolated_home):
    outcome = helpers.init_env(
        cli_runner,
        sets=(
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=old-prod-iac-core-0',
        ),
    )
    assert outcome.exit_code == 2
    assert "Stage 0 names that project tst-prod-iac-core-0" in outcome.output


def test_init_errors_name_their_source(cli_runner, tmp_path):
    config = tmp_path / "config.env"
    config.write_text("PREFIX=abc\nORGANIZATION_ID=x\n", encoding="utf-8")
    outcome = helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--from-config-env",
        str(config),
    )
    assert outcome.exit_code == 2
    assert f"Invalid answers from --from-config-env {config}:" in (
        outcome.output
    )
    bare = helpers.invoke(
        cli_runner, "init", "--non-interactive", "--prefix", "abc"
    )
    assert "Error: Invalid answers:" in bare.output


def test_init_accepts_a_home_that_holds_the_engine(cli_runner, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    engine = helpers.engine_copy(home)
    outcome = cli_runner.invoke(
        cli.app,
        [
            "init",
            "--non-interactive",
            "--prefix",
            "tst",
            *helpers.set_args(),
            "--home",
            str(home),
            "--repo",
            str(engine),
        ],
    )
    assert outcome.exit_code == 0, outcome.output
    answers = answers_lib.load(home / "envs" / "tst" / "answers.yaml")
    assert answers.engine is not None
    assert answers.engine.path == str(engine)


def test_init_requires_bootstrap_user_in_the_bootstrap_phase(
    cli_runner, isolated_home
):
    outcome = cli_runner.invoke(
        cli.app,
        [
            "init",
            "--non-interactive",
            "--repo",
            str(conftest.REPO_ROOT),
            "--prefix",
            "tst",
            *[
                arg
                for assignment in helpers.REQUIRED_SETS
                if not assignment.startswith("bootstrap_user=")
                for arg in ("--set", assignment)
            ],
        ],
    )
    assert outcome.exit_code == 2, outcome.output
    assert "bootstrap_user is required while stage0_phase is bootstrap" in (
        outcome.output
    )


def _final_env(cli_runner, home, *, final_applied):
    """Creates an environment in the final phase with recorded history."""
    assert helpers.init_env(cli_runner).exit_code == 0
    final = helpers.invoke(
        cli_runner, "init", "--non-interactive", "--set", "stage0_phase=final"
    )
    assert final.exit_code == 0, final.output
    env = paths.EnvPaths(home / "envs" / "tst", "tst")
    state = run_state.RunState(prefix="tst")
    state.stage0.final_applied = final_applied
    run_state.save(env, state, helpers_deploy.NOW)
    return env


def _back_to_bootstrap(cli_runner):
    return helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--set",
        "stage0_phase=bootstrap",
    )


def test_init_refuses_bootstrap_after_a_final_apply(cli_runner, isolated_home):
    _final_env(cli_runner, isolated_home, final_applied=True)
    outcome = _back_to_bootstrap(cli_runner)
    assert outcome.exit_code == 2, outcome.output
    assert "stage0_phase cannot return from final to bootstrap" in (
        outcome.output
    )
    assert helpers.load_answers(isolated_home).stage0_phase == "final"


def test_init_allows_bootstrap_before_a_final_apply(cli_runner, isolated_home):
    _final_env(cli_runner, isolated_home, final_applied=False)
    outcome = _back_to_bootstrap(cli_runner)
    assert outcome.exit_code == 0, outcome.output
    assert helpers.load_answers(isolated_home).stage0_phase == "bootstrap"


def test_init_keeps_the_phase_without_readable_history(
    cli_runner, isolated_home
):
    env = _final_env(cli_runner, isolated_home, final_applied=False)
    env.run_state.write_text("{broken")
    outcome = _back_to_bootstrap(cli_runner)
    assert outcome.exit_code == 2, outcome.output
    assert "Move it away" in outcome.output
    # Other changes need no history.
    other = helpers.invoke(
        cli_runner, "init", "--non-interactive", "--set", "region=us-east4"
    )
    assert other.exit_code == 0, other.output
