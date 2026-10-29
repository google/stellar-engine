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

"""Tests for the Stage 0 phase file that sets bootstrap_user."""

import shutil

import hcl2
import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import models
from stellar_engine.render import hcl
from stellar_engine.render import phase
from stellar_engine.render import stages
from stellar_engine.render import writer

_USER = f"admin@{conftest.DOMAIN}"


def _answers(**overrides):
    return helpers.minimal_answers(**overrides)


def _final():
    return _answers(stage0_phase=models.STAGE0_FINAL)


@pytest.fixture
def workspace(tmp_path):
    path = tmp_path / "ws"
    path.mkdir()
    return path


def test_filename_is_an_auto_tfvars_file():
    assert phase.FILENAME == "0-bootstrap-phase.auto.tfvars"
    assert phase.FILENAME.endswith(".auto.tfvars")


def test_stage0_declares_the_variable(repo):
    assert phase.VARIABLE in repo.stage_variable_names(paths.BOOTSTRAP)


def test_text_sets_only_the_bootstrap_user(repo):
    text = phase.text(_answers(), repo)
    assert text.startswith(
        "# stellar render writes this file from envs/tst/answers.yaml "
        "stage0_phase and bootstrap_user.\n"
    )
    assert "stellar init --set stage0_phase=final" in text
    values = {
        key: hcl.unquote(value)
        for key, value in hcl2.loads(text).items()
        if key != "__comments__"
    }
    assert values == {"bootstrap_user": _USER}


def test_text_is_empty_in_the_final_phase(repo):
    assert phase.text(_final(), repo) == ""


def test_text_needs_a_bootstrap_user(repo):
    with pytest.raises(
        phase.PhaseFileError, match="bootstrap_user is required"
    ):
        phase.text(_answers(bootstrap_user=None), repo)


def test_text_needs_the_stage_variable(repo, monkeypatch):
    monkeypatch.setattr(
        repo_lib.Repo, "stage_variable_names", lambda self, stage: frozenset()
    )
    with pytest.raises(phase.PhaseFileError, match="declares no variable"):
        phase.text(_answers(), repo)
    # The final phase writes nothing, so it works with any engine version.
    assert phase.text(_final(), repo) == ""


def test_write_creates_then_keeps_the_file(workspace, repo):
    target = workspace / phase.FILENAME
    assert phase.write(workspace, _answers(), repo) is writer.Outcome.CREATED
    assert conftest.mode(target) == 0o600
    assert phase.write(workspace, _answers(), repo) is writer.Outcome.UNCHANGED
    assert phase.is_generated(target)


def test_write_updates_a_changed_user(workspace, repo):
    phase.write(workspace, _answers(), repo)
    other = _answers(bootstrap_user=f"ops@{conftest.DOMAIN}")
    assert phase.write(workspace, other, repo) is writer.Outcome.UPDATED
    assert f"ops@{conftest.DOMAIN}" in (workspace / phase.FILENAME).read_text()


def test_write_removes_the_file_in_the_final_phase(workspace, repo):
    phase.write(workspace, _answers(), repo)
    assert phase.write(workspace, _final(), repo) is writer.Outcome.REMOVED
    assert not (workspace / phase.FILENAME).exists()
    assert phase.write(workspace, _final(), repo) is None


@pytest.mark.parametrize("phase_name", ["bootstrap", "final"])
def test_write_refuses_a_file_it_did_not_write(workspace, repo, phase_name):
    target = workspace / phase.FILENAME
    target.write_text(f'bootstrap_user = "{_USER}"\n')
    answers = _answers(stage0_phase=phase_name)
    with pytest.raises(phase.PhaseFileError, match="stellar did not write"):
        phase.write(workspace, answers, repo)
    assert target.read_text() == f'bootstrap_user = "{_USER}"\n'


def test_write_refuses_a_symlink(workspace, repo, tmp_path):
    source = tmp_path / "elsewhere.tfvars"
    source.write_text(phase.text(_answers(), repo))
    (workspace / phase.FILENAME).symlink_to(source)
    with pytest.raises(phase.PhaseFileError, match="stellar did not write"):
        phase.write(workspace, _final(), repo)
    assert source.exists()


def test_planned_writes_nothing(workspace, repo):
    assert phase.planned(workspace, _answers(), repo) == phase.text(
        _answers(), repo
    )
    assert not (workspace / phase.FILENAME).exists()


_REMOTE_PROVIDERS = """terraform {
  backend "gcs" {
    bucket = "abc-prod-iac-core-0"
  }
}
"""


def test_warnings_flag_a_migrated_bootstrap_workspace(workspace):
    providers = workspace / workspace_lib.BOOTSTRAP_PROVIDERS
    assert phase.warnings(workspace, _answers()) == []
    providers.write_text('provider "google" {}\n')
    assert phase.warnings(workspace, _answers()) == []
    providers.write_text(_REMOTE_PROVIDERS)
    (found,) = phase.warnings(workspace, _answers())
    assert "remote state backend" in found
    assert "stellar init --set stage0_phase=final" in found
    assert phase.warnings(workspace, _final()) == []


def _harness(tmp_path, repo, answers):
    """Builds a Stage 0 harness of only variables.tf and the inputs."""
    env = helpers.env_paths(answers, home=tmp_path / "home")
    rendered = stages.build(paths.BOOTSTRAP, answers, repo, env)
    harness = tmp_path / "harness"
    harness.mkdir()
    stage_dir = paths.stage_dir(repo.root, paths.BOOTSTRAP)
    shutil.copy(stage_dir / "variables.tf", harness / "variables.tf")
    (harness / "terraform.tfvars").write_text(rendered.text, encoding="utf-8")
    phase.write(harness, answers, repo)
    helpers.terraform_init(harness)
    return harness


@pytest.mark.terraform
@pytest.mark.parametrize(
    ("phase_name", "expected"),
    [("bootstrap", f'"{_USER}"'), ("final", '"unset"')],
)
def test_terraform_reads_the_phase_without_var(
    tmp_path, repo, phase_name, expected
):
    answers = helpers.load_fixture(
        "il5", bootstrap_user=_USER, stage0_phase=phase_name
    )
    harness = _harness(tmp_path, repo, answers)
    plan = helpers.terraform(harness, "plan", "-input=false")
    assert plan.returncode == 0, plan.stderr
    console = helpers.terraform(
        harness, "console", stdin='coalesce(var.bootstrap_user, "unset")\n'
    )
    assert console.returncode == 0, console.stderr
    assert console.stdout.strip() == expected
