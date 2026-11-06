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

"""Tests for the `stellar status` command."""

import json

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine.deploy import run_state
from stellar_engine.gcp import api

pytestmark = pytest.mark.usefixtures("isolated_home")
_MANUAL = ("pre.super_admin", "pre.access_transparency", "pre.project_quota")


@pytest.fixture
def stellar(monkeypatch, fake_cloud):
    """Fixes the console, the clock, the engine commit and the variables."""
    helpers_deploy.fix_command_output(monkeypatch)
    for name in ("CLOUDSDK_CONFIG", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(name, raising=False)
    return fake_cloud


def _status(cli_runner, home, *args):
    outcome = helpers.invoke(cli_runner, "status", *args)
    text = outcome.output.replace(str(home), "$STELLAR_HOME")
    return outcome, text.replace(str(conftest.REPO_ROOT), "$ENGINE")


def _rendered(cli_runner):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "render", "--stage", "0").exit_code == 0


def _confirm_manual_steps(home):
    env = helpers.env(home)
    state = run_state.load(env)
    for step_id in _MANUAL:
        state.step(step_id).confirmations.append(
            run_state.Confirmation(
                kind="manual", decision="confirmed", at=helpers_deploy.NOW
            )
        )
    run_state.save(env, state, helpers_deploy.NOW)


def test_status_json_snapshot(cli_runner, isolated_home, stellar, snapshot):
    _rendered(cli_runner)
    outcome, text = _status(cli_runner, isolated_home, "--json")
    assert outcome.exit_code == 4, outcome.output
    assert text == snapshot


def test_status_leaves_the_environment_byte_identical(
    cli_runner, isolated_home, stellar
):
    _rendered(cli_runner)
    _confirm_manual_steps(isolated_home)
    helpers.env(isolated_home).deploy_lock.write_text(
        '{"command": "deploy", "started": "2026-10-29T12:00:00+00:00"}\n'
    )

    def tree():
        # Every path, directories and links included, so a directory that
        # status creates fails the test too.
        return {
            path: (
                path.lstat().st_mode,
                path.read_bytes()
                if path.is_file() and not path.is_symlink()
                else None,
            )
            for path in sorted(isolated_home.rglob("*"))
        }

    before = tree()
    for args in ((), ("--json",)):
        assert _status(cli_runner, isolated_home, *args)[0].exit_code == 4
    assert tree() == before
    assert not stellar.writes


def test_status_table_shows_the_header_and_each_stage(
    cli_runner, isolated_home, stellar
):
    _rendered(cli_runner)
    outcome, text = _status(cli_runner, isolated_home)
    assert outcome.exit_code == 4
    assert "Stage 0 phase: bootstrap" in text
    assert "Engine: current $ENGINE" in text
    assert "Lock: free" in text
    assert "Pending manual steps: pre.super_admin" in text
    for title in ("Prerequisites", "Stage 0 - Bootstrap", "Stage 1"):
        assert title in text
    assert "s0.apply_workload" in text
    assert "Fix: " in text
    assert "Summary: " in text


def test_status_exits_0_when_the_selected_stage_is_done(
    cli_runner, isolated_home, stellar
):
    _rendered(cli_runner)
    _confirm_manual_steps(isolated_home)
    outcome, text = _status(cli_runner, isolated_home, "--stage", "pre")
    assert outcome.exit_code == 0, text
    assert "Pending manual steps: none" in text
    assert "s0.render" not in text


def test_status_reports_the_lock_holder(cli_runner, isolated_home, stellar):
    _rendered(cli_runner)
    lock = run_state.Lock(
        helpers.env(isolated_home), "deploy --stage 0", helpers_deploy.NOW
    )
    lock.acquire()
    outcome, text = _status(cli_runner, isolated_home, "--json")
    header = json.loads(text)["header"]
    assert header["lock"] == (
        "held by deploy --stage 0 since 2026-10-29T12:00:00+00:00"
    )
    assert outcome.exit_code == 4


def test_status_reads_the_recorded_history(cli_runner, isolated_home, stellar):
    _rendered(cli_runner)
    env = helpers.env(isolated_home)
    state = run_state.load(env)
    state.last_run = run_state.LastRun(
        command="deploy --stage 0",
        principal="user@example.com",
        started=helpers_deploy.NOW,
        exit=4,
    )
    record = state.step("s0.apply_bootstrap")
    record.finished = helpers_deploy.NOW
    record.artifacts.plan = "plans/0-s0.apply_bootstrap.tfplan"
    record.summary = {"create": 3, "no-op": 2}
    record.findings = ["confirm delete_confirm google_folder.x"]
    record.confirmations.append(
        run_state.Confirmation(
            kind="iam_gate",
            decision="skipped",
            at=helpers_deploy.NOW,
            detail="2 removed",
        )
    )
    run_state.save(env, state, helpers_deploy.NOW)
    _, text = _status(cli_runner, isolated_home, "--json")
    header = json.loads(text)["header"]
    assert header["last_run"] == (
        "deploy --stage 0 by user@example.com, started "
        "2026-10-29T12:00:00+00:00, exit 4"
    )
    assert header["last_plan"] == (
        "s0.apply_bootstrap plans/0-s0.apply_bootstrap.tfplan: 3 create; "
        "confirm delete_confirm google_folder.x"
    )
    assert header["iam_review"].startswith("skipped for s0.apply_bootstrap")


def test_status_unreadable_run_state_exits_5(
    cli_runner, isolated_home, stellar
):
    _rendered(cli_runner)
    helpers.env(isolated_home).run_state.write_text("{not json")
    outcome, _ = _status(cli_runner, isolated_home)
    assert outcome.exit_code == 5
    assert "Move it away" in outcome.output


def test_status_reports_cloud_errors_as_manual(
    cli_runner, isolated_home, stellar
):
    _rendered(cli_runner)
    stellar.services = api.CloudError("denied")
    _, text = _status(cli_runner, isolated_home, "--json")
    (apis,) = [
        step
        for step in json.loads(text)["steps"]
        if step["check_id"] == "pre.apis"
    ]
    assert apis["status"] == "manual"
    assert "denied" in apis["detail"]


def test_status_leads_failures_with_the_step_status(
    cli_runner, isolated_home, stellar
):
    _rendered(cli_runner)
    _, text = _status(cli_runner, isolated_home, "--json")
    steps = {step["check_id"]: step for step in json.loads(text)["steps"]}
    assert steps["s0.apply_workload"]["status"] == "fail"
    assert steps["s0.apply_workload"]["detail"].startswith("pending: ")
    assert steps["s1.billing_grant"]["status"] == "skip"
    assert steps["pre.apis"]["status"] == "pass"
    assert steps["pre.apis"]["category"] == "Deploy steps"
    assert steps["pre.apis"]["title"] == (
        "pre.apis\nPrerequisites: Enable the bootstrap project APIs"
    )


def test_status_rejects_an_unknown_stage(cli_runner, isolated_home, stellar):
    _rendered(cli_runner)
    outcome, text = _status(cli_runner, isolated_home, "--stage", "9")
    assert outcome.exit_code == 2
    assert "Unknown stage" in text
