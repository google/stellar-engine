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

"""Tests for the deploy engine: step semantics, remedies and selection.

The exit statuses come from `commands.deploy.exit_code`, which maps the
error that stopped a run to the status the command exits with.
"""

import dataclasses

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine.commands import common
from stellar_engine.commands import deploy as deploy_cmd
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import remedies
from stellar_engine.gcp import api

_S = model.StepStatus
_K = model.StepKind
Script = helpers_deploy.Script
_GROUP = helpers_deploy.ADMINS
_SA_ERROR = (
    "Error: googleapi: Error 403: Permission "
    "'iam.serviceAccounts.getAccessToken' denied for "
    "tst-prod-bootstrap-0@tst-prod-iac-core-0.iam.gserviceaccount.com"
)
_LOCK_ERROR = (
    "Error: Error acquiring the state lock\n\nLock Info:\n"
    "  ID:        1234-abcd\n  Operation: OperationTypePlan\n"
)
_UNLOCK_QUESTION = (
    "Release the state lock 1234-abcd? Answer yes only when no other "
    "Terraform run uses this state."
)
_ctx = helpers_deploy.scripted_ctx
_asked = helpers_deploy.asked


def _status(ctx, step_id):
    return ctx.run_state.steps[step_id].status


class TestRun:
    def test_done_steps_are_skipped(self, tmp_path):
        script = Script([_S.DONE])
        ctx = _ctx(tmp_path)
        report = engine.run(ctx, [script.step("a.x")])
        assert (deploy_cmd.exit_code(report), report.stopped_at) == (0, None)
        assert script.runs == 0
        assert _status(ctx, "a.x") == _S.DONE
        assert "== a.x (auto) Title of a.x ==" in helpers_deploy.output(ctx)
        assert "Explains a.x." in helpers_deploy.output(ctx)

    def test_pending_auto_steps_run(self, tmp_path):
        script = Script([_S.PENDING, _S.DONE])
        ctx = _ctx(tmp_path)
        report = engine.run(ctx, [script.step()])
        assert deploy_cmd.exit_code(report) == 0
        assert script.runs == 1
        assert report.results[0].status == _S.DONE
        assert _asked(ctx) == []

    def test_a_run_must_make_the_check_pass(self, tmp_path):
        script = Script([_S.PENDING])
        ctx = _ctx(tmp_path)
        report = engine.run(ctx, [script.step()])
        assert deploy_cmd.exit_code(report) == common.EXIT_FAILED
        assert "its check says pending" in (report.reason or "")
        assert _status(ctx, "t.step") == _S.FAILED

    def test_unknown_asks_before_running(self, tmp_path):
        script = Script([_S.UNKNOWN, _S.DONE])
        ctx = _ctx(tmp_path, [True])
        assert deploy_cmd.exit_code(engine.run(ctx, [script.step()])) == 0
        assert script.runs == 1
        assert _asked(ctx) == [
            "t.step cannot tell. Run Title of t.step anyway?"
        ]
        (confirmation,) = ctx.record("t.step").confirmations
        assert (confirmation.kind, confirmation.decision) == ("unknown", "run")

    def test_unknown_declined_stops(self, tmp_path):
        script = Script([_S.UNKNOWN])
        ctx = _ctx(tmp_path, [False])
        report = engine.run(ctx, [script.step()])
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
        assert script.runs == 0

    def test_cloud_errors_in_checks_are_unknown(self, tmp_path):
        def broken(ctx):
            raise api.AccessDeniedError("denied")

        step = Script([_S.DONE]).step(kind=_K.CHECK)
        step = dataclasses.replace(step, check=broken)
        ctx = _ctx(tmp_path, [False])
        report = engine.run(ctx, [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
        assert "Cannot check: denied" in (report.reason or "")

    def test_not_applicable_steps_are_not_checked(self, tmp_path):
        script = Script([_S.PENDING])
        ctx = _ctx(tmp_path)
        step = script.step(applies_when=lambda ctx: False)
        report = engine.run(ctx, [step])
        assert report.results[0].status == _S.NOT_APPLICABLE
        assert (script.checks, script.runs) == (0, 0)

    def test_blocked_and_failed_verdicts_stop(self, tmp_path):
        blocked = model.Verdict(_S.BLOCKED, "blocked here", remedy="unblock")
        report = engine.run(_ctx(tmp_path), [Script([blocked]).step()])
        assert (deploy_cmd.exit_code(report), report.remedy) == (
            common.EXIT_STOPPED,
            "unblock",
        )
        failed = model.Verdict(_S.FAILED, "broken")
        report = engine.run(_ctx(tmp_path / "f"), [Script([failed]).step()])
        assert deploy_cmd.exit_code(report) == common.EXIT_FAILED

    def test_a_stop_ends_the_run(self, tmp_path):
        first, second = Script([_S.PENDING]), Script([_S.PENDING])
        ctx = _ctx(tmp_path)
        steps = [
            first.step("a.first", kind=_K.CHECK),
            second.step("a.second"),
        ]
        report = engine.run(ctx, steps)
        assert report.stopped_at == "a.first"
        assert report.remedy == "fix it"
        assert second.checks == 0

    def test_run_records_the_last_run(self, tmp_path):
        ctx = _ctx(tmp_path)
        engine.run(ctx, [Script([_S.DONE]).step()], command="deploy --stage 0")
        last = ctx.run_state.last_run
        assert last is not None
        assert last.command == "deploy --stage 0"
        assert last.principal == conftest.USER
        # The command maps the report to the exit status and records it.
        assert (last.finished, last.exit) == (None, None)
        engine.finish_run(ctx, 0)
        assert last.exit == 0
        assert last.finished is not None
        assert ctx.env.run_state.is_file()


class TestRequires:
    def _steps(self, first):
        second = Script([_S.PENDING, _S.DONE])
        steps = [
            first.step("a.first"),
            second.step("a.second", requires=("a.first",)),
        ]
        return second, steps

    def test_unmet_requirements_stop(self, tmp_path):
        first = Script([_S.PENDING])
        second, steps = self._steps(first)
        ctx = _ctx(tmp_path)
        report = engine.run(ctx, steps[1:], catalog=steps)
        assert (deploy_cmd.exit_code(report), report.stopped_at) == (
            common.EXIT_STOPPED,
            "a.second",
        )
        assert "stellar deploy --only a.first --prefix tst" in (
            report.remedy or ""
        )
        assert (first.runs, second.runs) == (0, 0)

    def test_run_state_meets_requirements_the_check_cannot_tell(self, tmp_path):
        first = Script([_S.UNKNOWN])
        second, steps = self._steps(first)
        ctx = _ctx(tmp_path)
        ctx.record("a.first").status = _S.DONE
        assert (
            deploy_cmd.exit_code(engine.run(ctx, steps[1:], catalog=steps)) == 0
        )
        assert (first.checks, first.runs, second.runs) == (1, 0, 1)

    def test_a_pending_check_overrides_a_done_record(self, tmp_path):
        first = Script([_S.PENDING])
        second, steps = self._steps(first)
        ctx = _ctx(tmp_path)
        ctx.record("a.first").status = _S.DONE
        report = engine.run(ctx, steps[1:], catalog=steps)
        assert (deploy_cmd.exit_code(report), report.stopped_at) == (
            common.EXIT_STOPPED,
            "a.second",
        )
        assert (first.checks, first.runs, second.runs) == (1, 0, 0)

    def test_unknown_checks_without_a_record_stop(self, tmp_path):
        first = Script([_S.UNKNOWN])
        second, steps = self._steps(first)
        report = engine.run(_ctx(tmp_path), steps[1:], catalog=steps)
        assert report.stopped_at == "a.second"
        assert second.runs == 0

    def test_checks_meet_requirements(self, tmp_path):
        first = Script([_S.DONE])
        second, steps = self._steps(first)
        assert (
            deploy_cmd.exit_code(
                engine.run(_ctx(tmp_path), steps[1:], catalog=steps)
            )
            == 0
        )
        assert (first.runs, second.runs) == (0, 1)

    def test_steps_that_do_not_apply_meet_requirements(self, tmp_path):
        first = Script([_S.PENDING])
        second = Script([_S.PENDING, _S.DONE])
        steps = [
            first.step("a.first", applies_when=lambda ctx: False),
            second.step("a.second", requires=("a.first",)),
        ]
        assert (
            deploy_cmd.exit_code(
                engine.run(_ctx(tmp_path), steps[1:], catalog=steps)
            )
            == 0
        )


class TestManual:
    def _step(self, verdicts=(_S.PENDING,), **fields):
        return Script(list(verdicts)).step(
            kind=_K.MANUAL, runnable=False, **fields
        )

    def test_a_person_confirms(self, tmp_path):
        ctx = _ctx(tmp_path, [True])
        assert deploy_cmd.exit_code(engine.run(ctx, [self._step()])) == 0
        assert _asked(ctx) == ["Mark t.step done?"]
        (confirmation,) = ctx.record("t.step").confirmations
        assert (confirmation.kind, confirmation.decision) == (
            "manual",
            "confirmed",
        )
        assert confirmation.principal == conftest.USER

    def test_yes_never_answers_manual_steps(self, tmp_path):
        ctx = _ctx(tmp_path, [False], yes=True)
        assert (
            deploy_cmd.exit_code(engine.run(ctx, [self._step()]))
            == common.EXIT_STOPPED
        )
        assert _asked(ctx) == ["Mark t.step done?"]

    def test_recorded_confirmations_count_while_unknown(self, tmp_path):
        ctx = _ctx(tmp_path)
        ctx.confirmed("t.step", "manual", "done")
        report = engine.run(ctx, [self._step([_S.UNKNOWN])])
        assert deploy_cmd.exit_code(report) == 0
        assert _asked(ctx) == []

    def test_recorded_confirmations_never_override_pending(self, tmp_path):
        ctx = _ctx(tmp_path, [False])
        ctx.confirmed("t.step", "manual", "done")
        assert (
            deploy_cmd.exit_code(engine.run(ctx, [self._step()]))
            == common.EXIT_STOPPED
        )

    def test_a_runnable_manual_step_offers_to_run(self, tmp_path):
        script = Script([_S.PENDING, _S.DONE])
        step = script.step(kind=_K.MANUAL)
        ctx = _ctx(tmp_path, [True])
        assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0
        assert script.runs == 1
        assert _asked(ctx) == ["Run Title of t.step now?"]


_ADMIN = model.fixed(model.Identity.BILLING_ADMIN)


class TestIdentity:
    def _denied(self):
        return conftest.FakeCloud(
            denied_billing_perms={"billing.accounts.setIamPolicy"}
        )

    def test_handoff_blocks(self, tmp_path):
        script = Script([_S.PENDING])
        ctx = _ctx(tmp_path, cloud=self._denied())
        step = script.step("s0.x", stage="0", identity=_ADMIN)
        report = engine.run(ctx, [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
        assert _status(ctx, "s0.x") == _S.BLOCKED
        assert script.runs == 0
        card = report.remedy or ""
        assert "can grant roles on the billing account" in card
        assert f"The current identity is {conftest.USER}." in card
        assert _GROUP in card
        assert "gcloud auth application-default login" in card
        assert "stellar deploy --only s0.x --prefix tst" in card
        assert f"terraform -chdir={ctx.workspace('0')} init" in card

    def test_matching_identities_run(self, tmp_path):
        script = Script([_S.PENDING, _S.DONE])
        step = script.step(identity=_ADMIN)
        assert deploy_cmd.exit_code(engine.run(_ctx(tmp_path), [step])) == 0
        assert script.runs == 1

    def test_done_steps_need_no_identity(self, tmp_path):
        step = Script([_S.DONE]).step(identity=_ADMIN)
        ctx = _ctx(tmp_path, cloud=self._denied())
        assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0

    def test_unreadable_permissions_hand_off(self, tmp_path):
        cloud = conftest.FakeCloud(billing_perm_error=api.CloudError("x"))
        step = Script([_S.PENDING]).step(identity=_ADMIN)
        report = engine.run(_ctx(tmp_path, cloud=cloud), [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
        assert "terraform -chdir" not in (report.remedy or "")

    def test_manual_steps_hand_off_when_pending(self, tmp_path):
        step = Script([_S.PENDING]).step(kind=_K.MANUAL, identity=_ADMIN)
        ctx = _ctx(tmp_path, cloud=self._denied())
        report = engine.run(ctx, [step])
        assert _status(ctx, "t.step") == _S.BLOCKED
        assert _asked(ctx) == []
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED

    def test_manual_steps_can_be_marked_when_unknown(self, tmp_path):
        step = Script([_S.UNKNOWN]).step(kind=_K.MANUAL, identity=_ADMIN)
        ctx = _ctx(tmp_path, [True], cloud=self._denied())
        assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0
        assert _asked(ctx) == ["Mark t.step done?"]


class TestCheckSteps:
    def test_pending_checks_stop(self, tmp_path):
        script = Script([_S.PENDING])
        report = engine.run(_ctx(tmp_path), [script.step(kind=_K.CHECK)])
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
        assert report.remedy == "fix it"

    def test_unknown_checks_may_be_passed(self, tmp_path):
        ctx = _ctx(tmp_path, [True])
        step = Script([_S.UNKNOWN]).step(kind=_K.CHECK)
        assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0
        assert _status(ctx, "t.step") == _S.UNKNOWN
        assert ctx.record("t.step").confirmations[0].decision == "continued"


class TestNonInteractive:
    @pytest.mark.parametrize(
        ("verdicts", "kind"),
        [
            ([_S.PENDING], _K.MANUAL),
            ([_S.UNKNOWN], _K.AUTO),
            ([_S.UNKNOWN], _K.CHECK),
        ],
    )
    def test_prompt_sites_stop(self, tmp_path, verdicts, kind):
        script = Script(verdicts)
        ctx = _ctx(tmp_path, interactive=False, yes=True)
        report = engine.run(ctx, [script.step(kind=kind)])
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
        assert "needs an answer" in (report.reason or "")
        assert script.runs == 0


class TestRemedies:
    def _failing(self, count, keys=(remedies.SA_PROPAGATION,)):
        error = model.CommandError("apply", _SA_ERROR)
        script = Script([_S.PENDING, _S.DONE], errors=[error] * count)
        return script, script.step(remedies=keys)

    def test_attempts_are_bounded(self, tmp_path):
        script, step = self._failing(10)
        slept = []
        ctx = _ctx(tmp_path, sleep=slept.append)
        report = engine.run(ctx, [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_FAILED
        assert script.runs == 4
        assert slept == [10, 30, 60]
        assert ctx.record("t.step").attempts == {remedies.SA_PROPAGATION: 3}
        assert "gcp-organization-admins" in (report.remedy or "")

    def test_a_remedy_then_success(self, tmp_path):
        script, step = self._failing(1)
        slept = []
        ctx = _ctx(tmp_path, sleep=slept.append)
        assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0
        assert (script.runs, slept) == (2, [10])
        assert ctx.record("t.step").attempts == {}

    def test_attempts_persist_until_done(self, tmp_path):
        script, step = self._failing(1)
        ctx = _ctx(tmp_path)
        ctx.record("t.step").attempts[remedies.SA_PROPAGATION] = 3
        assert (
            deploy_cmd.exit_code(engine.run(ctx, [step])) == common.EXIT_FAILED
        )
        assert script.runs == 1

    def test_only_the_step_remedies_apply(self, tmp_path):
        script, step = self._failing(1, keys=(remedies.STATE_LOCK,))
        report = engine.run(_ctx(tmp_path), [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_FAILED
        assert script.runs == 1
        assert "getAccessToken" in (report.remedy or "")

    def test_remedies_without_actions_explain(self, tmp_path):
        error = model.CommandError(
            "init", "Error: Backend initialization required"
        )
        script = Script([_S.PENDING], errors=[error])
        step = script.step(remedies=(remedies.BACKEND_INIT_REQUIRED,))
        report = engine.run(_ctx(tmp_path), [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_FAILED
        assert "Rerun stellar deploy" in (report.remedy or "")
        assert script.runs == 1

    def test_cloud_errors_match_remedies(self, tmp_path):
        error = api.ApiDisabledError("pubsub.googleapis.com", "123456789012")
        script = Script([_S.PENDING, _S.DONE], errors=[error])
        step = script.step(remedies=(remedies.API_DISABLED,))
        cloud = conftest.FakeCloud()
        assert (
            deploy_cmd.exit_code(
                engine.run(_ctx(tmp_path, cloud=cloud), [step])
            )
            == 0
        )
        assert cloud.writes == [
            ("enable_services", "123456789012", ("pubsub.googleapis.com",))
        ]

    def test_missing_credentials_fail_the_step(self, tmp_path):
        script = Script([_S.PENDING], errors=[api.CredentialsError("no ADC")])
        report = engine.run(_ctx(tmp_path), [script.step()])
        assert deploy_cmd.exit_code(report) == common.EXIT_FAILED
        assert "application-default login" in (report.remedy or "")

    def test_failing_remedy_actions_fail_the_step(self, tmp_path):
        error = api.ApiDisabledError("pubsub.googleapis.com", "123456789012")
        script = Script([_S.PENDING], errors=[error])
        step = script.step(remedies=(remedies.API_DISABLED,))
        cloud = conftest.FakeCloud(
            write_errors={"enable_services": api.AccessDeniedError("no")}
        )
        report = engine.run(_ctx(tmp_path, cloud=cloud), [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_FAILED
        assert "the remedy api_disabled failed" in (report.reason or "")

    def _locked(self):
        """Returns a Stage 0 step whose first run hits a state lock."""
        error = model.CommandError("plan", _LOCK_ERROR)
        script = Script([_S.PENDING, _S.DONE], errors=[error])
        return script, script.step(stage="0", remedies=(remedies.STATE_LOCK,))

    @pytest.mark.parametrize(
        "kwargs", [{"replies": [False]}, {"interactive": False}]
    )
    def test_an_unanswered_prompt_keeps_the_attempt(self, tmp_path, kwargs):
        # The remedy allows one attempt; a declined or impossible prompt
        # must not use it up, or the rerun could only fail with exit 5.
        script, step = self._locked()
        ctx = _ctx(tmp_path, **kwargs)
        report = engine.run(ctx, [step])
        assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
        assert "1234-abcd" in (report.reason or "")
        assert script.runs == 1
        assert ctx.record("t.step").attempts == {}
        assert _status(ctx, "t.step") == _S.PENDING
        # The rerun offers the remedy again, and the answer makes it run.
        script, step = self._locked()
        runner = conftest.FakeTerraform()
        ctx = _ctx(tmp_path, [True], runner=runner)
        assert ctx.record("t.step").attempts == {}
        assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0
        assert script.runs == 2
        assert _asked(ctx) == [_UNLOCK_QUESTION]
        assert helpers_deploy.subcommands(runner) == ["force-unlock"]


class TestSelect:
    _CATALOG = tuple(
        Script([_S.DONE]).step(step_id, stage=stage)
        for step_id, stage in (
            ("pre.a", "pre"),
            ("pre.b", "pre"),
            ("s0.c", "0"),
            ("s0.d", "0"),
            ("s1.e", "1"),
        )
    )

    def _ids(self, **kwargs):
        return [step.id for step in engine.select(self._CATALOG, **kwargs)]

    def test_select(self):
        assert self._ids() == ["pre.a", "pre.b", "s0.c", "s0.d", "s1.e"]
        assert self._ids(stages=["0"]) == ["s0.c", "s0.d"]
        assert self._ids(stages=["0-bootstrap", "pre"]) == [
            "pre.a",
            "pre.b",
            "s0.c",
            "s0.d",
        ]
        assert self._ids(only=["s0.d", "pre.a"]) == ["pre.a", "s0.d"]
        assert self._ids(from_step="pre.b") == ["pre.b", "s0.c", "s0.d", "s1.e"]
        assert self._ids(stages=["0"], from_step="s0.d") == ["s0.d"]

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"only": ["nope"]},
            {"from_step": "nope"},
            {"stages": ["1"], "from_step": "pre.a"},
            {"stages": ["2"]},
        ],
    )
    def test_select_rejects(self, kwargs):
        with pytest.raises(ValueError):
            engine.select(self._CATALOG, **kwargs)


class TestRender:
    def test_render_writes_the_workspace(self, tmp_path):
        ctx = _ctx(tmp_path)
        rendered = engine.render(ctx, "0")
        assert not rendered.refused
        assert (ctx.workspace("0") / "terraform.tfvars").is_file()

    def test_edited_tfvars_block_without_a_terminal(self, tmp_path):
        ctx = _ctx(tmp_path, interactive=False)
        engine.render(ctx, "0")
        tfvars = ctx.workspace("0") / "terraform.tfvars"
        tfvars.write_text(tfvars.read_text() + "# edited\n")
        ctx.answers = helpers.minimal_answers(region="us-central1")
        with pytest.raises(model.BlockedError, match="manual edits"):
            engine.render(ctx, "0")

    def test_render_errors_block(self, tmp_path):
        ctx = _ctx(tmp_path)
        ctx.workspace("0").mkdir(parents=True)
        (ctx.workspace("0") / "0-bootstrap-phase.auto.tfvars").write_text(
            'bootstrap_user = "x"\n'
        )
        with pytest.raises(model.BlockedError, match="stellar did not write"):
            engine.render(ctx, "0")
