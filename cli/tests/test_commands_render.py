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

"""Tests for the `stellar render` command."""

import os
import pathlib

import pytest

import conftest
import helpers
from stellar_engine import cli
from stellar_engine import paths
from stellar_engine.commands import common
from stellar_engine.render import stages

pytestmark = pytest.mark.usefixtures("isolated_home")


def test_render_creates_workspace_tfvars_and_imports(
    cli_runner, isolated_home, fake_tools
):
    assert (
        helpers.init_env(
            cli_runner,
            sets=(
                f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            ),
        ).exit_code
        == 0
    )
    outcome = helpers.invoke(cli_runner, "render")
    assert outcome.exit_code == 0, outcome.output
    workspace = helpers.workspace(isolated_home, "0-bootstrap")
    tfvars = workspace / "terraform.tfvars"
    assert 'prefix = "tst"' in tfvars.read_text()
    assert conftest.mode(tfvars) == 0o600
    imports_file = workspace / "0-bootstrap-imports.tf"
    assert "tst-prod-iac-core-0" in imports_file.read_text()
    assert (workspace / "main.tf").is_symlink()
    # The home lives outside the repository, so the links are absolute.
    target = pathlib.Path(os.readlink(workspace / "main.tf"))
    assert target.is_absolute()
    assert target.is_relative_to(conftest.REPO_ROOT)
    assert (workspace / "0-bootstrap-providers.tf").is_file()
    assert (
        helpers.workspace(isolated_home, "1-resman") / "terraform.tfvars"
    ).is_file()
    assert f"created    {tfvars}" in outcome.output
    assert f"created    {imports_file}" in outcome.output
    phase_file = workspace / "0-bootstrap-phase.auto.tfvars"
    assert 'bootstrap_user = "admin@example.com"' in phase_file.read_text()
    assert conftest.mode(phase_file) == 0o600
    assert f"created    {phase_file}" in outcome.output
    assert "Next: stellar deploy --stage 0" in outcome.output
    assert "terraform -chdir" not in outcome.output
    assert "-var" not in outcome.output
    assert "switches stage0_phase to final" in outcome.output
    assert "1-resman waits for Stage 0 outputs" in outcome.output
    assert "stellar deploy --stage 1 then fetches them" in outcome.output


def test_render_rerun_is_unchanged(cli_runner, isolated_home, fake_tools):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    again = helpers.invoke(cli_runner, "render")
    assert again.exit_code == 0, again.output
    assert "created" not in again.output
    # The two tfvars files and the Stage 0 phase file.
    assert again.output.count("  unchanged  ") == 3


def test_render_one_stage_by_alias(cli_runner, isolated_home, fake_tools):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = helpers.invoke(cli_runner, "render", "--stage", "0")
    assert outcome.exit_code == 0, outcome.output
    assert (
        helpers.workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    ).exists()
    assert not helpers.workspace(isolated_home, "1-resman").exists()
    assert helpers.invoke(cli_runner, "render", "--stage", "9").exit_code == 2


def test_render_removes_dropped_imports(cli_runner, isolated_home, fake_tools):
    assert (
        helpers.init_env(
            cli_runner,
            sets=(
                f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            ),
        ).exit_code
        == 0
    )
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    rerun = helpers.invoke(
        cli_runner, "init", "--non-interactive", "--set", "imports={}"
    )
    assert rerun.exit_code == 0, rerun.output
    outcome = helpers.invoke(cli_runner, "render")
    imports_file = helpers.workspace(isolated_home, "0-bootstrap") / (
        "0-bootstrap-imports.tf"
    )
    assert f"removed    {imports_file}" in outcome.output
    assert not imports_file.exists()


def test_render_warns_on_billing_export_import(
    cli_runner, isolated_home, fake_tools
):
    outcome = helpers.init_env(
        cli_runner,
        sets=(
            "billing.no_iam=true",
            f'imports.0-bootstrap."{conftest.BILLING_EXPORT_ADDRESS}"=tst-prod-billing-exp-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    assert "Warning: imports.0-bootstrap" in outcome.output
    rendered = helpers.invoke(cli_runner, "render")
    assert rendered.exit_code == 0
    assert "billing export project" in rendered.output


def test_render_manual_edit_exits_3(cli_runner, isolated_home, fake_tools):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    tfvars = (
        helpers.workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    )
    edited = tfvars.read_text() + "# operator note\n"
    tfvars.write_text(edited)
    outcome = helpers.invoke(cli_runner, "render")
    assert outcome.exit_code == 3
    assert "manual edits" in outcome.output
    assert tfvars.read_text() == edited
    # The other stage still renders.
    assert "1-resman     unchanged" in outcome.output


def test_render_force_backs_up(cli_runner, isolated_home, fake_tools):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    workspace = helpers.workspace(isolated_home, "0-bootstrap")
    tfvars = workspace / "terraform.tfvars"
    rendered = tfvars.read_text()
    tfvars.write_text(rendered + "# operator note\n")
    outcome = helpers.invoke(cli_runner, "render", "--force")
    assert outcome.exit_code == 0, outcome.output
    assert tfvars.read_text() == rendered
    backups = list(workspace.glob("terraform.tfvars.backup.*"))
    assert len(backups) == 1
    assert backups[0].read_text().endswith("# operator note\n")
    assert f"backup {backups[0]}" in outcome.output


def test_render_interactive_confirm(
    cli_runner, isolated_home, fake_tools, monkeypatch
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    tfvars = (
        helpers.workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    )
    tfvars.write_text(tfvars.read_text() + "# operator note\n")
    monkeypatch.setattr(common, "stdin_is_tty", lambda: True)
    declined = helpers.invoke(cli_runner, "render", "--stage", "0", input="n\n")
    assert declined.exit_code == 0, declined.output
    assert "skipped" in declined.output
    assert tfvars.read_text().endswith("# operator note\n")
    accepted = helpers.invoke(cli_runner, "render", "--stage", "0", input="y\n")
    assert accepted.exit_code == 0, accepted.output
    assert not tfvars.read_text().endswith("# operator note\n")


def test_render_diff_writes_nothing(cli_runner, isolated_home, fake_tools):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = helpers.invoke(cli_runner, "render", "--diff")
    assert outcome.exit_code == 0, outcome.output
    assert '+prefix = "tst"' in outcome.output
    assert not (
        paths.stage_dir(isolated_home / "envs" / "tst", paths.BOOTSTRAP)
        / "terraform.tfvars"
    ).exists()
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    assert (
        "No changes." in helpers.invoke(cli_runner, "render", "--diff").output
    )


def test_render_without_answers_exits_2(cli_runner):
    outcome = helpers.invoke(cli_runner, "render", "--prefix", "nope")
    assert outcome.exit_code == 2
    assert "stellar init --prefix nope" in outcome.output


def test_render_invalid_answers_exit_2(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text(path.read_text().replace("IL5", "PCI"))
    outcome = helpers.invoke(cli_runner, "render")
    assert outcome.exit_code == 2
    assert "compliance.regime PCI" in outcome.output


@pytest.mark.terraform
def test_rendered_bootstrap_workspace_validates(cli_runner, isolated_home):
    outcome = helpers.init_env(
        cli_runner,
        sets=(
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    assert helpers.invoke(cli_runner, "render", "--stage", "0").exit_code == 0
    workspace = helpers.workspace(isolated_home, "0-bootstrap")
    # The phase file sets bootstrap_user, so no command passes -var.
    assert (workspace / "0-bootstrap-phase.auto.tfvars").is_file()
    env = {**os.environ, "TF_IN_AUTOMATION": "1"}
    helpers.terraform_init(workspace, env=env)
    completed = helpers.terraform(workspace, "validate", env=env)
    assert completed.returncode == 0, completed.stderr


def test_render_rejects_answers_of_another_prefix(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text(path.read_text().replace("prefix: tst", "prefix: qqq"))
    outcome = helpers.invoke(cli_runner, "render", "--stage", "0")
    assert outcome.exit_code == 2
    assert "sets prefix qqq, but it belongs to environment tst" in (
        outcome.output
    )
    assert not (helpers.workspace(isolated_home, "0-bootstrap")).exists()
    listed = helpers.invoke(cli_runner, "env", "list")
    assert "answers set prefix qqq" in listed.output


_AUTOMATION_IMPORT = (
    f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0'
)


def _engine_invoke(cli_runner, engine, *args):
    return cli_runner.invoke(cli.app, [*args, "--repo", str(engine)])


def _init_engine(cli_runner, engine):
    return _engine_invoke(
        cli_runner,
        engine,
        "init",
        "--non-interactive",
        "--prefix",
        "tst",
        *helpers.set_args(_AUTOMATION_IMPORT),
    )


def test_render_warns_when_the_engine_cannot_keep_projects(
    cli_runner, isolated_home, fake_tools, tmp_path
):
    engine = helpers.deletion_policy_engine(tmp_path / "engine", declared=False)
    assert _init_engine(cli_runner, engine).exit_code == 0
    outcome = _engine_invoke(cli_runner, engine, "render", "--stage", "0")
    assert outcome.exit_code == 0, outcome.output
    assert (
        "Warning: keep_imported_projects is true, but this engine version "
        "of 0-bootstrap cannot keep imported projects on destroy yet, so "
        "terraform destroy deletes tst-prod-iac-core-0."
    ) in outcome.output
    show = _engine_invoke(cli_runner, engine, "env", "show")
    assert "    tst-prod-iac-core-0  DELETE" in show.output


def test_render_and_show_keep_imported_projects(
    cli_runner, isolated_home, fake_tools, tmp_path
):
    engine = helpers.deletion_policy_engine(tmp_path / "engine")
    outcome = _init_engine(cli_runner, engine)
    assert outcome.exit_code == 0, outcome.output
    rendered = _engine_invoke(cli_runner, engine, "render", "--stage", "0")
    assert rendered.exit_code == 0, rendered.output
    assert "keep_imported_projects" not in rendered.output
    tfvars = (
        helpers.workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    )
    assert 'automation = "ABANDON"' in tfvars.read_text()
    show = _engine_invoke(cli_runner, engine, "env", "show")
    assert show.exit_code == 0, show.output
    assert "    tst-prod-iac-core-0  ABANDON" in show.output
    assert "    tst-prod-audit-logs-0  DELETE" in show.output


def _phase_file(home):
    return (
        helpers.workspace(home, "0-bootstrap") / "0-bootstrap-phase.auto.tfvars"
    )


def test_render_final_phase_removes_the_phase_file(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    phase_file = _phase_file(isolated_home)
    assert phase_file.is_file()
    switch = helpers.invoke(
        cli_runner, "init", "--non-interactive", "--set", "stage0_phase=final"
    )
    assert switch.exit_code == 0, switch.output
    outcome = helpers.invoke(cli_runner, "render")
    assert outcome.exit_code == 0, outcome.output
    assert f"removed    {phase_file}" in outcome.output
    assert not phase_file.exists()
    assert "Next: stellar deploy --stage 0" in outcome.output
    assert "stage0_phase" not in outcome.output
    again = helpers.invoke(cli_runner, "render")
    assert str(phase_file) not in again.output
    show = helpers.invoke(cli_runner, "env", "show")
    assert "Stage 0 phase: final" in show.output


def test_render_updates_the_phase_file_for_a_new_user(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    change = helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--set",
        "bootstrap_user=ops@example.com",
    )
    assert change.exit_code == 0, change.output
    outcome = helpers.invoke(cli_runner, "render", "--stage", "0")
    phase_file = _phase_file(isolated_home)
    assert f"updated    {phase_file}" in outcome.output
    assert "ops@example.com" in phase_file.read_text()


def test_render_refuses_a_phase_file_it_did_not_write(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    phase_file = _phase_file(isolated_home)
    phase_file.write_text('bootstrap_user = "someone@example.com"\n')
    for args in (["render"], ["render", "--diff"]):
        outcome = helpers.invoke(cli_runner, *args)
        assert outcome.exit_code == 2, outcome.output
        assert f"stellar did not write {phase_file}" in outcome.output
    assert phase_file.read_text() == 'bootstrap_user = "someone@example.com"\n'


def test_render_refuses_a_foreign_phase_file_before_any_write(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    tfvars = (
        helpers.workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    )
    before = tfvars.read_text()
    change = helpers.invoke(
        cli_runner,
        "init",
        "--non-interactive",
        "--set",
        "alert_email=changed@example.com",
    )
    assert change.exit_code == 0, change.output
    _phase_file(isolated_home).write_text('bootstrap_user = "x@example.com"\n')
    outcome = helpers.invoke(cli_runner, "render")
    assert outcome.exit_code == 2, outcome.output
    assert tfvars.read_text() == before


def test_render_diff_shows_the_phase_file(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = helpers.invoke(cli_runner, "render", "--diff")
    assert outcome.exit_code == 0, outcome.output
    assert '+bootstrap_user = "admin@example.com"' in outcome.output
    assert not _phase_file(isolated_home).exists()
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    switch = helpers.invoke(
        cli_runner, "init", "--non-interactive", "--set", "stage0_phase=final"
    )
    assert switch.exit_code == 0, switch.output
    removal = helpers.invoke(cli_runner, "render", "--diff")
    assert '-bootstrap_user = "admin@example.com"' in removal.output
    assert _phase_file(isolated_home).is_file()


def _shadow(workspace, name):
    """Replaces an engine link of the workspace with a real file."""
    link = workspace / name
    text = link.read_text()
    link.unlink()
    link.write_text(text)
    return link


def test_render_warns_about_a_shadowing_file_before_an_error(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    shadow = _shadow(helpers.workspace(isolated_home, "0-bootstrap"), "main.tf")
    phase_file = _phase_file(isolated_home)
    phase_file.write_text('bootstrap_user = "x@example.com"\n')
    outcome = helpers.invoke(cli_runner, "render", "--stage", "0")
    assert outcome.exit_code == 2, outcome.output
    warning, error = outcome.stderr.splitlines()
    assert warning == (
        f"Warning: {shadow} is a real file that shadows the engine's file "
        "of the same name."
    )
    assert error.startswith(f"Error: stellar did not write {phase_file}")


def test_render_reports_a_refusal_before_an_import_error(
    cli_runner, isolated_home, fake_tools
):
    address = conftest.AUTOMATION_ADDRESS
    sets = (f'imports.0-bootstrap."{address}"=tst-prod-iac-core-0',)
    assert helpers.init_env(cli_runner, sets=sets).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    workspace = helpers.workspace(isolated_home, "0-bootstrap")
    tfvars = workspace / "terraform.tfvars"
    tfvars.write_text(tfvars.read_text() + "# operator note\n")
    imports_file = workspace / "0-bootstrap-imports.tf"
    imports_file.write_text("# mine\n")
    outcome = helpers.invoke(
        cli_runner, "render", "--stage", "0", "--non-interactive"
    )
    assert outcome.exit_code == 2, outcome.output
    refusal, error = outcome.stderr.splitlines()
    assert refusal.startswith(f"Error: {tfvars} has manual edits")
    assert error.startswith(f"Error: stellar did not write {imports_file}")


def test_render_interactive_warns_before_the_prompt(
    cli_runner, isolated_home, fake_tools, monkeypatch
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render").exit_code == 0
    workspace = helpers.workspace(isolated_home, "0-bootstrap")
    shadow = _shadow(workspace, "outputs.tf")
    tfvars = workspace / "terraform.tfvars"
    tfvars.write_text(tfvars.read_text() + "# operator note\n")
    monkeypatch.setattr(common, "stdin_is_tty", lambda: True)
    outcome = cli_runner.invoke(
        cli.app,
        ["render", "--stage", "0", "--repo", str(conftest.REPO_ROOT)],
        input="n\n",
    )
    assert outcome.exit_code == 0, outcome.output
    warning = outcome.output.index(f"Warning: {shadow} is a real file")
    prompt = outcome.output.index(f"{tfvars} has manual edits.")
    assert warning < prompt


def test_render_diff_prints_earlier_stages_before_an_error(
    cli_runner, isolated_home, fake_tools, monkeypatch
):
    assert helpers.init_env(cli_runner).exit_code == 0
    build = stages.build

    def fail_on_resman(stage, *args):
        if stage == paths.RESMAN:
            raise stages.RenderError("1-resman cannot render")
        return build(stage, *args)

    monkeypatch.setattr(stages, "build", fail_on_resman)
    outcome = helpers.invoke(cli_runner, "render", "--diff")
    assert outcome.exit_code == 2, outcome.output
    assert '+prefix = "tst"' in outcome.stdout
    assert outcome.stderr.endswith("Error: 1-resman cannot render\n")


def test_render_of_a_ready_stage1_points_at_its_deploy(
    cli_runner, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    fast_config = isolated_home / "envs" / "tst" / "fast-config"
    for name in (
        "providers/1-resman-providers.tf",
        "tfvars/0-globals.auto.tfvars.json",
        "tfvars/0-bootstrap.auto.tfvars.json",
    ):
        (fast_config / name).parent.mkdir(parents=True, exist_ok=True)
        (fast_config / name).write_text("{}\n")
    outcome = helpers.invoke(cli_runner, "render", "--stage", "1")
    assert outcome.exit_code == 0, outcome.output
    assert outcome.output.splitlines()[-1] == "Next: stellar deploy --stage 1"
    assert "waits for Stage 0 outputs" not in outcome.output
