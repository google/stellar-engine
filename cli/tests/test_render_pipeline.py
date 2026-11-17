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

"""Tests for the render steps that `stellar render` runs."""

import datetime

import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine import workspace
from stellar_engine.config import models
from stellar_engine.config import validate
from stellar_engine.render import imports
from stellar_engine.render import phase
from stellar_engine.render import pipeline
from stellar_engine.render import stages
from stellar_engine.render import writer

NOW = datetime.datetime(2026, 10, 23, 12, 30, 5, tzinfo=datetime.UTC)
_IMPORTS = {
    paths.BOOTSTRAP: {conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0"}
}


def _never(target, changes):
    raise AssertionError(f"confirm called for {target} with {changes!r}")


def _unexpected(message):
    raise AssertionError(f"unexpected report: {message}")


def _options(**overrides):
    values = {
        "force": False,
        "interactive": False,
        "confirm": _never,
        "now": NOW,
        "warn": _unexpected,
        "error": _unexpected,
    }
    values.update(overrides)
    return pipeline.WriteOptions(**values)


@pytest.fixture
def env(tmp_path):
    return helpers.env_paths(helpers.minimal_answers(), home=tmp_path / "home")


def test_replace_question_names_the_file(tmp_path):
    target = tmp_path / "terraform.tfvars"
    assert pipeline.replace_question(target) == (
        f"{target} has manual edits. Back it up and replace it?"
    )


def test_errors_are_the_exceptions_the_pipeline_raises():
    expected = (
        workspace.WorkspaceError,
        stages.RenderError,
        imports.ImportBlockError,
        phase.PhaseFileError,
    )
    assert expected == pipeline.ERRORS


@pytest.fixture
def render(repo, env, local_tools):
    """Returns a function that renders one stage with default options."""

    def run(stage, answers, **overrides):
        return pipeline.render_stage(
            stage, answers, repo, env, local_tools, _options(**overrides)
        )

    return run


def _tfvars(env, stage=paths.BOOTSTRAP):
    return env.workspace(stage) / "terraform.tfvars"


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (None, [paths.BOOTSTRAP, paths.RESMAN]),
        ([], [paths.BOOTSTRAP, paths.RESMAN]),
        (["1"], [paths.RESMAN]),
        (["1-resman", "0", paths.BOOTSTRAP], [paths.BOOTSTRAP, paths.RESMAN]),
    ],
)
def test_select_stages_in_deployment_order(names, expected):
    assert pipeline.select_stages(names) == expected


def test_select_stages_rejects_an_unknown_stage():
    with pytest.raises(ValueError, match="Unknown stage '9'"):
        pipeline.select_stages(["0", "9"])


def test_warnings_follow_the_stage_order(repo, env, monkeypatch):
    monkeypatch.setattr(
        imports, "warnings", lambda answers, stage, repo: [f"imports {stage}"]
    )
    monkeypatch.setattr(
        stages, "warnings", lambda answers, stage, repo: [f"stages {stage}"]
    )
    monkeypatch.setattr(
        phase, "warnings", lambda workspace, answers: [f"phase {workspace}"]
    )
    monkeypatch.setattr(validate, "warnings", lambda answers: ["billing"])
    found = pipeline.warnings(
        ["0", paths.RESMAN], helpers.minimal_answers(), repo, env
    )
    assert found == [
        f"imports {paths.BOOTSTRAP}",
        f"stages {paths.BOOTSTRAP}",
        f"phase {env.workspace(paths.BOOTSTRAP)}",
        f"imports {paths.RESMAN}",
        f"stages {paths.RESMAN}",
        "billing",
    ]


def test_warnings_name_a_redundant_external_grant(repo, env):
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "external_grant": True}
    )
    (found,) = pipeline.warnings([paths.RESMAN], answers, repo, env)
    assert "billing.external_grant is set while billing.no_iam" in found
    stage0 = pipeline.warnings([paths.BOOTSTRAP], answers, repo, env)
    assert not any("external_grant" in line for line in stage0)


def test_warnings_report_an_import_that_would_fail(repo, env):
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "no_iam": True},
        imports={
            paths.BOOTSTRAP: {conftest.BILLING_EXPORT_ADDRESS: "tst-bill-0"}
        },
    )
    (found,) = pipeline.warnings(paths.STAGES, answers, repo, env)
    assert "billing export project" in found
    assert pipeline.warnings([paths.RESMAN], answers, repo, env) == []


def test_render_text_prefers_terraform_fmt(repo, env, local_tools):
    answers = helpers.minimal_answers()
    rendered = stages.build(paths.BOOTSTRAP, answers, repo, env).text
    text = pipeline.render_text("0", answers, repo, env, local_tools)
    assert text == rendered
    local_tools.terraform_fmt = lambda text: "formatted\n"
    text = pipeline.render_text("0", answers, repo, env, local_tools)
    assert text == "formatted\n"


def test_render_stage_writes_the_stage0_files(env, render):
    answers = helpers.minimal_answers(imports=_IMPORTS)
    workspace = env.workspace(paths.BOOTSTRAP)
    files = [
        workspace / "terraform.tfvars",
        workspace / imports.filename(paths.BOOTSTRAP),
        workspace / phase.FILENAME,
    ]
    first = render("0", answers)
    assert first.sync.path == workspace
    assert first.rows == [
        (paths.BOOTSTRAP, path, "created", None) for path in files
    ]
    assert not first.refused
    again = render(paths.BOOTSTRAP, answers)
    assert again.rows == [
        (paths.BOOTSTRAP, path, "unchanged", None) for path in files
    ]


def test_render_stage_reports_removed_files(env, render):
    render("0", helpers.minimal_answers(imports=_IMPORTS))
    final = helpers.minimal_answers(stage0_phase=models.STAGE0_FINAL)
    workspace = env.workspace(paths.BOOTSTRAP)
    result = render("0", final)
    assert result.rows == [
        (paths.BOOTSTRAP, _tfvars(env), "updated", None),
        (
            paths.BOOTSTRAP,
            workspace / imports.filename(paths.BOOTSTRAP),
            "removed",
            None,
        ),
        (paths.BOOTSTRAP, workspace / phase.FILENAME, "removed", None),
    ]
    assert render("0", final).rows == [
        (paths.BOOTSTRAP, _tfvars(env), "unchanged", None)
    ]


def _shadows(path):
    return (
        f"{path} is a real file that shadows the engine's file of the same "
        "name."
    )


def test_render_stage_returns_the_sync_report(env, render):
    result = render("1", helpers.minimal_answers())
    assert result.rows == [
        (paths.RESMAN, _tfvars(env, paths.RESMAN), "created", None)
    ]
    assert result.sync.stage == paths.RESMAN
    assert result.sync.pending
    workspace = env.workspace(paths.BOOTSTRAP)
    workspace.mkdir(parents=True)
    (workspace / "main.tf").write_text("# local copy\n")
    found = []
    result = render("0", helpers.minimal_answers(), warn=found.append)
    assert result.sync.conflicts == ["main.tf"]
    assert found == [_shadows(workspace / "main.tf")]


def test_render_stage_warns_before_a_later_error(env, render):
    render("0", helpers.minimal_answers())
    workspace = env.workspace(paths.BOOTSTRAP)
    (workspace / "main.tf").unlink()
    (workspace / "main.tf").write_text("# local copy\n")
    (workspace / phase.FILENAME).write_text('bootstrap_user = "x"\n')
    found = []
    with pytest.raises(phase.PhaseFileError):
        render("0", helpers.minimal_answers(), warn=found.append)
    assert found == [_shadows(workspace / "main.tf")]


def test_render_stage_keeps_an_edited_tfvars(env, render):
    answers = helpers.minimal_answers()
    render("0", answers)
    tfvars = _tfvars(env)
    edited = tfvars.read_text() + "# operator note\n"
    tfvars.write_text(edited)
    phase_file = env.workspace(paths.BOOTSTRAP) / phase.FILENAME
    phase_file.unlink()
    errors = []
    result = render("0", answers, error=errors.append)
    assert result.refused
    (refusal,) = errors
    assert refusal.startswith(f"{tfvars} has manual edits")
    assert result.rows == [
        (paths.BOOTSTRAP, tfvars, "refused", None),
        (paths.BOOTSTRAP, phase_file, "created", None),
    ]
    assert tfvars.read_text() == edited


def test_render_stage_reports_a_refusal_before_a_later_error(env, render):
    answers = helpers.minimal_answers(imports=_IMPORTS)
    render("0", answers)
    tfvars = _tfvars(env)
    tfvars.write_text(tfvars.read_text() + "# operator note\n")
    imports_file = env.workspace(paths.BOOTSTRAP) / imports.filename(
        paths.BOOTSTRAP
    )
    imports_file.write_text("# mine\n")
    errors = []
    with pytest.raises(imports.ImportBlockError):
        render("0", answers, error=errors.append)
    (refusal,) = errors
    assert refusal.startswith(f"{tfvars} has manual edits")


@pytest.mark.parametrize(
    ("accept", "outcome"), [(False, "skipped"), (True, "updated")]
)
def test_render_stage_asks_before_replacing_an_edited_tfvars(
    env, render, accept, outcome
):
    answers = helpers.minimal_answers()
    render("0", answers)
    tfvars = _tfvars(env)
    tfvars.write_text(tfvars.read_text() + "# operator note\n")
    calls = []

    def confirm(target, changes):
        calls.append((target, changes))
        return accept

    result = render("0", answers, interactive=True, confirm=confirm)
    ((target, changes),) = calls
    assert target == tfvars
    assert "-# operator note" in changes
    assert not result.refused
    (_, path, written, backup) = result.rows[0]
    assert (path, written) == (tfvars, outcome)
    assert (backup is not None) == accept
    assert tfvars.read_text().endswith("# operator note\n") != accept


def test_render_stage_force_backs_up_without_asking(env, render):
    answers = helpers.minimal_answers()
    render("0", answers)
    tfvars = _tfvars(env)
    tfvars.write_text(tfvars.read_text() + "# operator note\n")
    (_, _, written, backup) = render("0", answers, force=True).rows[0]
    assert written == "updated"
    assert backup is not None
    assert backup.read_text().endswith("# operator note\n")


def test_render_stage_refuses_a_foreign_phase_file_before_any_write(
    env, render
):
    render("0", helpers.minimal_answers())
    before = _tfvars(env).read_text()
    phase_file = env.workspace(paths.BOOTSTRAP) / phase.FILENAME
    phase_file.write_text('bootstrap_user = "x@example.com"\n')
    changed = helpers.minimal_answers(alert_email="changed@example.com")
    with pytest.raises(phase.PhaseFileError, match="stellar did not write"):
        render("0", changed)
    assert _tfvars(env).read_text() == before


def test_diff_shows_new_files_and_writes_nothing(repo, env, local_tools):
    answers = helpers.minimal_answers(imports=_IMPORTS)
    text = pipeline.diff("0", answers, repo, env, local_tools)
    assert '+prefix = "tst"' in text
    assert "+  to = module.automation-project" in text
    assert f'+bootstrap_user = "admin@{conftest.DOMAIN}"' in text
    assert text.endswith("\n")
    resman = pipeline.diff(paths.RESMAN, answers, repo, env, local_tools)
    assert resman.startswith(f"--- {_tfvars(env, paths.RESMAN)}\n")
    assert "+  to = " not in resman
    assert not env.root.exists()


def test_diff_after_a_render_is_empty(repo, env, local_tools, render):
    answers = helpers.minimal_answers(imports=_IMPORTS)
    for stage in paths.STAGES:
        render(stage, answers)
    for stage in paths.STAGES:
        assert pipeline.diff(stage, answers, repo, env, local_tools) == ""


def test_diff_shows_removals(repo, env, local_tools, render):
    render("0", helpers.minimal_answers())
    final = helpers.minimal_answers(stage0_phase=models.STAGE0_FINAL)
    text = pipeline.diff("0", final, repo, env, local_tools)
    assert f'-bootstrap_user = "admin@{conftest.DOMAIN}"' in text
    assert (env.workspace(paths.BOOTSTRAP) / phase.FILENAME).is_file()


def test_diff_ends_every_change_with_a_newline(repo, env, local_tools, render):
    answers = helpers.minimal_answers()
    render("0", answers)
    tfvars = _tfvars(env)
    rendered = tfvars.read_text()
    tfvars.write_text(rendered + "# no newline")
    changes = writer.diff(tfvars, rendered)
    assert not changes.endswith("\n")
    text = pipeline.diff("0", answers, repo, env, local_tools)
    assert text == f"{changes}\n"


def test_diff_refuses_a_foreign_phase_file(repo, env, local_tools, render):
    render("0", helpers.minimal_answers())
    phase_file = env.workspace(paths.BOOTSTRAP) / phase.FILENAME
    phase_file.write_text('bootstrap_user = "x@example.com"\n')
    with pytest.raises(phase.PhaseFileError, match="stellar did not write"):
        pipeline.diff("0", helpers.minimal_answers(), repo, env, local_tools)
