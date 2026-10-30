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

"""Tests for the deploy step model and its context."""

import pathlib

import pytest

import conftest
import helpers_deploy
from stellar_engine.config import answers as answers_lib
from stellar_engine.deploy import model
from stellar_engine.gcp import api
from stellar_engine.terraform import runner as runner_lib
from stellar_engine.wizard import prompts


def test_step_defaults(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    step = helpers_deploy.Script([model.StepStatus.DONE]).step()
    assert step.applies_when(ctx) is True
    assert step.identity(ctx) is model.Identity.DEPLOYER
    assert step.requires == ()
    assert step.remedies == ()


def test_fixed_identity(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    resolve = model.fixed(model.Identity.BILLING_ADMIN)
    assert resolve(ctx) is model.Identity.BILLING_ADMIN


@pytest.mark.parametrize(
    ("name", "stage"),
    [
        ("pre", "pre"),
        ("0", "0"),
        ("0-bootstrap", "0"),
        ("1", "1"),
        ("1-resman", "1"),
    ],
)
def test_catalog_stage(name, stage):
    assert model.catalog_stage(name) == stage


def test_catalog_stage_rejects_unknown_stages():
    with pytest.raises(ValueError, match="Unknown stage"):
        model.catalog_stage("2")


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (model.StoppedError, model.StepStatus.PENDING),
        (model.BlockedError, model.StepStatus.BLOCKED),
        (model.InputRequiredError, model.StepStatus.PENDING),
        (model.FailedError, model.StepStatus.FAILED),
    ],
)
def test_stop_statuses(error, status):
    stop = error("why", remedy="what next")
    assert stop.status == status
    assert (stop.reason, stop.remedy) == ("why", "what next")
    assert isinstance(stop, model.DeployError)


def test_static_explains_without_the_context(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    assert model.static("Does a thing.")(ctx) == "Does a thing."


def test_succeeded_passes_and_raises():
    ok = helpers_deploy.completed("fine")
    assert model.succeeded(ok, "plan") is ok
    failed = helpers_deploy.completed("out\n", returncode=1, stderr="err\n")
    log = pathlib.Path("/tmp/x.log")
    with pytest.raises(model.CommandError) as raised:
        model.succeeded(failed, "apply", log=log)
    assert raised.value.command == "apply"
    assert raised.value.output == "out\nerr\n"
    assert raised.value.log == log


def test_command_error_from_terraform_error():
    failed = helpers_deploy.completed("", returncode=1, stderr="no state\n")
    error = runner_lib.TerraformError("failed", failed, pathlib.Path("l.log"))
    found = model.command_error(error, "state pull")
    assert (found.command, found.output) == ("state pull", "no state\n")
    assert found.log == pathlib.Path("l.log")


def test_confirm_routine_with_yes_does_not_ask(tmp_path):
    prompter = prompts.ScriptedPrompter([])
    ctx = helpers_deploy.make_ctx(tmp_path, prompter=prompter, yes=True)
    assert ctx.confirm("Apply?", routine=True) is True
    assert prompter.asked == []


def test_confirm_not_routine_asks_even_with_yes(tmp_path):
    prompter = prompts.ScriptedPrompter([False])
    ctx = helpers_deploy.make_ctx(tmp_path, prompter=prompter, yes=True)
    assert ctx.confirm("Mark done?") is False
    assert prompter.asked == ["Mark done?"]


@pytest.mark.parametrize(
    "ask",
    [
        lambda ctx: ctx.confirm("q"),
        lambda ctx: ctx.confirm("q", routine=True),
        lambda ctx: ctx.select("q", ["a"]),
        lambda ctx: ctx.text("q"),
        lambda ctx: ctx.typed_confirm("q", "123"),
    ],
)
def test_prompts_stop_when_not_interactive(tmp_path, ask):
    ctx = helpers_deploy.make_ctx(tmp_path, interactive=False)
    with pytest.raises(model.InputRequiredError, match="needs an answer"):
        ask(ctx)


def test_routine_confirm_with_yes_runs_without_a_terminal(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path, interactive=False, yes=True)
    assert ctx.confirm("Apply?", routine=True) is True


def test_typed_confirm(tmp_path):
    prompter = prompts.ScriptedPrompter([" 123 ", "12"])
    ctx = helpers_deploy.make_ctx(tmp_path, prompter=prompter)
    assert ctx.typed_confirm("Change it.", "123") is True
    assert ctx.typed_confirm("Change it.", "123") is False
    assert prompter.asked[0] == "Change it. Type 123 to confirm:"


def test_preflight_runs_once_until_invalidated(tmp_path):
    cloud = conftest.FakeCloud()
    ctx = helpers_deploy.make_ctx(tmp_path, cloud=cloud)
    first = ctx.preflight()
    assert ctx.preflight() is first
    runs = [call for call in cloud.calls if call[0] == "org_perms"]
    assert len(runs) == 1
    assert first.rows("iam.")
    assert all(row.check_id.startswith("iam.") for row in first.rows("iam."))
    ctx.invalidate()
    assert ctx.preflight() is not first


def test_preflight_reports_billing_access(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    assert ctx.preflight().billing_access is True


def test_stage0_probe_is_cached(tmp_path):
    cloud = conftest.FakeCloud()
    ctx = helpers_deploy.make_ctx(tmp_path, cloud=cloud)
    probe = ctx.stage0()
    assert ctx.stage0() is probe
    reads = [call for call in cloud.calls if call[0] == "read_object"]
    assert len(reads) == 1
    ctx.invalidate()
    assert ctx.stage0() is not probe


def test_principal(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    assert ctx.principal() == conftest.USER
    cloud = conftest.FakeCloud(principal=api.CredentialsError("no ADC"))
    ctx = helpers_deploy.make_ctx(tmp_path / "other", cloud=cloud)
    assert ctx.principal() == "unknown"


def test_workspace(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    assert ctx.workspace("0") == ctx.env.workspace("0-bootstrap")
    assert ctx.workspace("1-resman") == ctx.env.workspace("1-resman")
    with pytest.raises(ValueError):
        ctx.workspace(model.PRE_STAGE)


def test_say_prints_markup_as_text(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    ctx.say('module.x["k"].y[0] [bold]not bold[/bold]')
    assert helpers_deploy.output(ctx) == (
        'module.x["k"].y[0] [bold]not bold[/bold]\n'
    )


def test_confirmed_records_the_answer(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    ctx.confirmed("s.x", "manual", "done by hand")
    ctx.confirmed("s.x", "iam_gate", "review", "skipped")
    first, second = ctx.record("s.x").confirmations
    assert (first.kind, first.decision, first.detail) == (
        "manual",
        "confirmed",
        "done by hand",
    )
    assert first.principal == conftest.USER
    assert (second.kind, second.decision) == ("iam_gate", "skipped")


def test_save_writes_run_state(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    assert ctx.run_state.updated is None
    ctx.record("s.x").status = model.StepStatus.DONE
    ctx.save()
    assert ctx.run_state.updated is not None
    assert conftest.mode(ctx.env.run_state) == 0o600


def _set_phase(phase):
    def change(data):
        data["stage0_phase"] = phase

    return change


def test_update_answers_adopts_the_change(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    ctx.stage0()
    outcome = ctx.update_answers(_set_phase("final"), source="test")
    assert outcome.changed
    assert ctx.answers.stage0_phase == "final"
    assert answers_lib.load(ctx.env.answers).stage0_phase == "final"
    # The probe reads the answers, so the change forgets it.
    assert ctx._probe is None


def test_update_answers_blocks_a_forbidden_change(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    ctx.update_answers(_set_phase("final"), source="test")
    ctx.run_state.stage0.final_applied = True
    with pytest.raises(model.BlockedError, match="bootstrap") as raised:
        ctx.update_answers(_set_phase("bootstrap"), source="test")
    assert raised.value.remedy
    assert ctx.answers.stage0_phase == "final"


def test_relative(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    assert ctx.relative(ctx.env.plans / "a.tfplan") == "plans/a.tfplan"
    assert ctx.relative(pathlib.Path("/elsewhere/x")) == "/elsewhere/x"
    assert ctx.relative(None) is None
