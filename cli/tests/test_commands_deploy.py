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

"""Tests for the `stellar deploy` command."""

import json

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine import workspace as workspace_lib
from stellar_engine.commands import common
from stellar_engine.commands import deploy as deploy_cmd
from stellar_engine.deploy import catalog
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import run_state
from stellar_engine.gcp import api
from stellar_engine.terraform import runner as runner_lib

pytestmark = pytest.mark.usefixtures("isolated_home")
_MANUAL = ("pre.super_admin", "pre.access_transparency", "pre.project_quota")
_BUCKET = "tst-prod-iac-core-bootstrap-0"
_ROLE = "roles/logging.admin"
_WORKLOAD = "google_assured_workloads_workload.primary[0]"
_LOCKED = (
    "Error: Error acquiring the state lock\n\nLock Info:\n  ID: 1234-abcd\n"
)
_TIMEOUT = (
    "Error: Error waiting for Creating LogBucket: timeout while waiting\n\n"
    '  with module.log-export-logbucket["audit-logs"].'
    "google_logging_project_bucket_config.bucket[0],\n"
)
# Failures whose remedy prompts, and the step that lists the remedy.
_REMEDY_SITES = {
    "state_lock": (_LOCKED, "s0.apply_workload"),
    "bucket_fix": (_TIMEOUT, "s0.apply_bootstrap"),
}


class _Applying(conftest.FakeTerraform):
    """A FakeTerraform whose apply writes a local state, as Terraform does."""

    state = b""

    def run(self, workspace, args, *, env, log, timeout):
        result = super().run(workspace, args, env=env, log=log, timeout=timeout)
        if args[0] == "apply":
            (workspace / probe_lib.STATE_FILE).write_bytes(self.state)
        return result


@pytest.fixture
def runner(monkeypatch, fake_cloud):
    """Fixes the console, clock and engine, and fakes Terraform.

    Returns:
        The FakeTerraform that every command uses.
    """
    del fake_cloud  # Only its patches matter.
    helpers_deploy.fix_command_output(monkeypatch)
    for name in ("CLOUDSDK_CONFIG", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(name, raising=False)
    fake = _Applying()
    monkeypatch.setattr(
        runner_lib, "SystemRunner", lambda console=None, **kwargs: fake
    )
    return fake


_replies = helpers_deploy.scripted_replies


def _deploy(cli_runner, *args):
    return helpers.invoke(cli_runner, "deploy", *args)


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)


def test_deploy_renders_and_records_the_run(cli_runner, isolated_home, runner):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = _deploy(cli_runner, "--only", "s0.render", "--non-interactive")
    assert outcome.exit_code == 0, outcome.output
    lines = outcome.output.splitlines()
    assert lines[0] == f"engine {helpers_deploy.COMMIT}"
    assert "== s0.render (auto) Render the Stage 0 workspace ==" in lines
    assert lines[-1] == "The selected steps are done. Next: stellar deploy"
    workspace = helpers.workspace(isolated_home, "0-bootstrap")
    assert (workspace / "terraform.tfvars").is_file()
    state = helpers.run_state(isolated_home)
    assert state.steps["s0.render"].status == "done"
    assert state.last_run is not None
    assert state.last_run.command == "deploy --only s0.render"
    assert state.last_run.exit == 0
    assert run_state.lock_holder(helpers.env(isolated_home)) is None
    assert runner.calls == []


def test_deploy_finishes_a_stage(
    cli_runner, isolated_home, runner, monkeypatch
):
    assert helpers.init_env(cli_runner).exit_code == 0
    _replies(monkeypatch, True, True, True)
    outcome = _deploy(cli_runner, "--stage", "pre")
    assert outcome.exit_code == 0, outcome.output
    assert outcome.output.splitlines()[-1] == (
        "Prerequisites complete. Next: stellar deploy --stage 0"
    )
    state = helpers.run_state(isolated_home)
    for step_id in _MANUAL:
        (confirmation,) = state.steps[step_id].confirmations
        assert confirmation.kind == "manual"
        assert confirmation.principal == conftest.USER


def test_deploy_rejects_an_unknown_step(cli_runner, isolated_home, runner):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = _deploy(cli_runner, "--only", "s0.nothing")
    assert outcome.exit_code == 2
    assert "Unknown step s0.nothing" in outcome.output
    outcome = _deploy(cli_runner, "--stage", "2")
    assert outcome.exit_code == 2


def test_deploy_refuses_a_held_lock(cli_runner, isolated_home, runner):
    assert helpers.init_env(cli_runner).exit_code == 0
    run_state.Lock(
        helpers.env(isolated_home), "deploy", helpers_deploy.NOW
    ).acquire()
    outcome = _deploy(cli_runner, "--only", "s0.render")
    assert outcome.exit_code == 4
    assert "Another deploy holds" in outcome.output
    assert not helpers.workspace(isolated_home, "0-bootstrap").exists()


def test_deploy_stops_on_an_unreadable_run_state(
    cli_runner, isolated_home, runner
):
    assert helpers.init_env(cli_runner).exit_code == 0
    helpers.env(isolated_home).run_state.write_text('{"schema_version": 9}')
    outcome = _deploy(cli_runner, "--only", "s0.render")
    assert outcome.exit_code == 5
    assert "schema_version 9" in outcome.output
    # The lock is taken before the read and released on the way out.
    assert run_state.lock_holder(helpers.env(isolated_home)) is None


def _rendered(cli_runner):
    """Creates the environment and renders Stage 0, which links it."""
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render", "--stage", "0").exit_code == 0


def _gate_answers(cli_runner, cloud):
    """Prepares a bootstrap apply whose plan removes a live grant."""
    _rendered(cli_runner)
    cloud.policy = {
        "version": 1,
        "etag": conftest.ETAG,
        "bindings": [{"role": _ROLE, "members": ["user:old@example.com"]}],
    }


def _prompt_site(name, cli_runner, home, runner, cloud):
    """Sets up a deploy that reaches one prompt; returns its arguments."""
    if name == "manual":
        assert helpers.init_env(cli_runner).exit_code == 0
        return ["--only", "pre.super_admin"]
    if name == "apply":
        _rendered(cli_runner)
        helpers_deploy.script_plan(
            runner, helpers.plan_fixture("targeted-workload")
        )
        return ["--only", "s0.apply_workload"]
    if name == "workload":
        _rendered(cli_runner)
        cloud.denied_billing_perms = {"roles/billing.admin.permission"}
        return ["--only", "s0.ready"]
    if name == "unknown":
        assert helpers.init_env(cli_runner).exit_code == 0
        _remote_providers(home)
        cloud.objects[(_BUCKET, probe_lib.REMOTE_OBJECT)] = api.CloudError(
            "unavailable"
        )
        return ["--only", "s0.migrate_state"]
    if name in _REMEDY_SITES:
        return _remedy_site(name, cli_runner, runner)
    _gate_answers(cli_runner, cloud)
    helpers_deploy.script_plan(
        runner,
        helpers_deploy.plan_doc(
            [helpers_deploy.binding(_ROLE, ["group:admins@example.com"])],
            bootstrap_user="admin@example.com",
        ),
    )
    return ["--only", "s0.apply_bootstrap", "--yes"]


def _remedy_site(name, cli_runner, runner):
    """Scripts a plan that fails twice, so a remedy prompt can be hit twice."""
    _rendered(cli_runner)
    output, step_id = _REMEDY_SITES[name]
    runner.results["plan"] = [helpers_deploy.completed(output, 1)] * 2
    return ["--only", step_id]


def _remote_providers(home):
    providers = (
        'terraform {\n  backend "gcs" {\n    bucket = "' + _BUCKET + '"\n'
        "  }\n}\n"
    )
    env = helpers.env(home)
    name = workspace_lib.BOOTSTRAP_PROVIDERS
    _write(env.workspace("0") / name, providers)
    _write(env.fast_config / "providers" / name, providers)
    cached = {"backend": {"type": "gcs", "config": {"bucket": _BUCKET}}}
    _write(env.workspace("0") / probe_lib.CACHED_BACKEND, json.dumps(cached))


@pytest.mark.parametrize(
    ("site", "reason"),
    [
        ("manual", "needs an answer: Mark pre.super_admin done?"),
        ("apply", "needs an answer: Apply"),
        ("workload", "needs the name of the pre-created workload"),
        ("unknown", "needs an answer: s0.migrate_state cannot tell"),
        ("gate", "needs an answer: How do you want to go on?"),
        ("state_lock", "needs an answer: Release the state lock 1234-abcd?"),
        ("bucket_fix", "The log buckets need a state fix"),
    ],
)
def test_non_interactive_stops_at_every_prompt_site(
    cli_runner, isolated_home, runner, cloud, site, reason
):
    args = _prompt_site(site, cli_runner, isolated_home, runner, cloud)
    outcome = _deploy(cli_runner, *args, "--non-interactive")
    assert outcome.exit_code == 4, outcome.output
    assert reason in outcome.output
    assert "Resume with stellar deploy." in outcome.output
    assert "?." not in outcome.output
    assert not any(args[0] == "apply" for args, _ in runner.calls)
    assert not cloud.writes


@pytest.mark.parametrize("site", ["state_lock", "bucket_fix"])
def test_an_unanswered_remedy_prompt_is_offered_again(
    cli_runner, isolated_home, runner, cloud, site
):
    # The remedy allows one attempt, which an unanswered prompt must not
    # use up: the rerun stops at the question again instead of failing.
    args = _prompt_site(site, cli_runner, isolated_home, runner, cloud)
    for _ in range(2):
        outcome = _deploy(cli_runner, *args, "--non-interactive")
        assert outcome.exit_code == 4, outcome.output
        assert "attempt 1 of 1" in outcome.output
    step_id = args[1]
    record = helpers.run_state(isolated_home).steps[step_id]
    assert (record.status, record.attempts) == ("pending", {})


def test_yes_applies_a_reviewed_plan_without_a_terminal(
    cli_runner, isolated_home, runner
):
    _rendered(cli_runner)
    helpers_deploy.script_plan(
        runner, helpers.plan_fixture("targeted-workload")
    )
    workload = helpers_deploy.resource(
        None,
        "google_assured_workloads_workload",
        "primary",
        [helpers_deploy.instance({"name": helpers_deploy.WORKLOAD}, 0)],
    )
    runner.state = helpers_deploy.state_bytes(
        helpers_deploy.state_doc([workload])
    )
    outcome = _deploy(
        cli_runner,
        "--only",
        "s0.apply_workload",
        "--yes",
        "--non-interactive",
    )
    assert outcome.exit_code == 0, outcome.output
    plans = [args for args, _ in runner.calls if args[0] == "plan"]
    assert f"-target={_WORKLOAD}" in plans[0]
    (apply,) = [args for args, _ in runner.calls if args[0] == "apply"]
    assert not any(arg.startswith(("-target", "-var")) for arg in apply)
    record = helpers.run_state(isolated_home).steps["s0.apply_workload"]
    assert record.status == "done"
    # The fake plan writes no plan file, but the deploy saves its JSON.
    assert record.artifacts.plan_json is not None
    assert (
        helpers.env(isolated_home).root / record.artifacts.plan_json
    ).is_file()


def test_yes_never_answers_the_iam_review(
    cli_runner, isolated_home, runner, cloud, monkeypatch
):
    args = _prompt_site("gate", cli_runner, isolated_home, runner, cloud)
    prompter = _replies(monkeypatch, "abort")
    outcome = _deploy(cli_runner, *args)
    assert outcome.exit_code == 4, outcome.output
    assert prompter.asked == ["How do you want to go on?"]
    assert "user:old@example.com" in outcome.output
    (snapshot,) = helpers.env(isolated_home).iam_snapshots.glob("*-gate.json")
    assert json.loads(snapshot.read_text())["bindings"][0]["role"] == _ROLE


def test_identity_mismatch_hands_off(cli_runner, isolated_home, runner, cloud):
    assert (
        helpers.init_env(
            cli_runner,
            sets=("billing.no_iam=true", "billing.external_grant=true"),
        ).exit_code
        == 0
    )
    cloud.denied_billing_perms = {"billing.accounts.setIamPolicy"}
    outcome = _deploy(cli_runner, "--only", "s1.billing_grant")
    assert outcome.exit_code == 4, outcome.output
    assert "Stopped at s1.billing_grant" in outcome.output
    assert "gcloud auth application-default login" in outcome.output
    assert (
        "stellar deploy --only s1.billing_grant --prefix tst" in outcome.output
    )
    assert (
        helpers.run_state(isolated_home).steps["s1.billing_grant"].status
        == "blocked"
    )
    assert not cloud.writes


def test_a_check_step_stops_with_its_remedy(cli_runner, isolated_home, runner):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = _deploy(cli_runner, "--only", "s0.quota_project")
    assert outcome.exit_code == 4, outcome.output
    assert (
        "gcloud auth application-default set-quota-project tst-prod-iac-core-0"
    ) in outcome.output


def test_unmet_requirements_stop_the_deploy(cli_runner, isolated_home, runner):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = _deploy(cli_runner, "--only", "s0.phase_final")
    assert outcome.exit_code == 4, outcome.output
    assert "s0.phase_final needs s0.migrate_state first" in outcome.output
    assert helpers.load_answers(isolated_home).stage0_phase == "bootstrap"


def test_a_failed_apply_exits_5(cli_runner, isolated_home, runner):
    _rendered(cli_runner)
    runner.results["plan"] = [helpers_deploy.completed("Error: boom", 1)]
    outcome = _deploy(
        cli_runner, "--only", "s0.apply_workload", "--non-interactive"
    )
    assert outcome.exit_code == 5, outcome.output
    assert "Stopped at s0.apply_workload" in outcome.output
    assert "Error: boom" in outcome.output
    assert (
        helpers.run_state(isolated_home).steps["s0.apply_workload"].status
        == "failed"
    )


def test_deploy_from_step_skips_the_steps_before_it(
    cli_runner, isolated_home, runner
):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = _deploy(
        cli_runner,
        "--stage",
        "pre",
        "--from-step",
        "pre.super_admin",
        "--non-interactive",
    )
    assert outcome.exit_code == 4, outcome.output
    assert "needs an answer: Mark pre.super_admin done?" in outcome.output
    state = helpers.run_state(isolated_home)
    assert state.last_run is not None
    assert state.last_run.command == (
        "deploy --stage pre --from-step pre.super_admin"
    )
    assert state.last_run.exit == 4
    assert "pre.apis" not in state.steps


@pytest.mark.parametrize(
    ("stage", "line"),
    [
        ("pre", "Prerequisites complete. Next: stellar deploy --stage 0"),
        ("0", "Stage 0 complete. Next: stellar deploy --stage 1"),
        ("1", "Stage 1 complete. Next: the DDG Stage 2 section"),
    ],
)
def test_deploy_names_the_next_stage(
    cli_runner, isolated_home, runner, monkeypatch, stage, line
):
    assert helpers.init_env(cli_runner).exit_code == 0
    done = helpers_deploy.Script([model.StepStatus.DONE])
    steps = tuple(
        done.step(f"x.{name}", stage=name) for name in ("pre", "0", "1")
    )
    monkeypatch.setattr(catalog, "catalog", lambda: steps)
    outcome = _deploy(cli_runner, "--stage", stage, "--non-interactive")
    assert outcome.exit_code == 0, outcome.output
    assert outcome.output.splitlines()[-1].startswith(line)


@pytest.mark.parametrize(
    ("stop", "code"),
    [
        (None, 0),
        (model.StoppedError("waits"), common.EXIT_STOPPED),
        (model.BlockedError("blocked"), common.EXIT_STOPPED),
        (model.InputRequiredError("asks"), common.EXIT_STOPPED),
        (model.FailedError("failed"), common.EXIT_FAILED),
    ],
)
def test_exit_code_follows_the_stop(stop, code):
    report = engine.Report((), "x.step" if stop else None, stop)
    assert deploy_cmd.exit_code(report) == code
