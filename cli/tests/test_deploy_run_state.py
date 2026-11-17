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

"""Tests for the deploy run-state file and the deploy lock."""

import json

import pytest

import conftest
import helpers_deploy
from stellar_engine import paths
from stellar_engine.deploy import model
from stellar_engine.deploy import run_state as run_state_lib

_NOW = helpers_deploy.NOW


@pytest.fixture
def env(tmp_path):
    found = paths.EnvPaths(tmp_path / "envs" / "abc", "abc")
    found.ensure()
    return found


def _filled(env):
    state = run_state_lib.load(env)
    state.engine = run_state_lib.EngineRecord(
        path="/engine", commit=helpers_deploy.COMMIT, terraform_version="1.13.3"
    )
    state.last_run = run_state_lib.LastRun(
        command="deploy --stage 0", principal=conftest.USER, started=_NOW
    )
    record = state.step("s0.apply_final")
    record.status = model.StepStatus.DONE
    record.attempts["state_lock"] = 1
    record.artifacts.plan = "plans/0-s0.apply_final-x.tfplan"
    record.summary = {"create": 3}
    record.tfvars_sha256 = "a" * 64
    record.state = run_state_lib.StateRecord(
        lineage=helpers_deploy.LINEAGE, serial=298, remote_generation=17
    )
    record.confirmations.append(
        run_state_lib.Confirmation(
            kind="iam_gate", decision="confirmed", at=_NOW, detail="ok"
        )
    )
    state.stage0.final_applied = True
    state.stage0.migration = run_state_lib.Migration(
        backup="plans/terraform.tfstate.before-migrate.x",
        local=run_state_lib.StateRecord(lineage="l", serial=297),
        remote_after=run_state_lib.StateRecord(
            lineage="l", serial=297, remote_generation=1
        ),
    )
    state.iam.snapshots.append(
        run_state_lib.SnapshotRecord(
            path="iam-snapshots/x.json", etag="e", taken=_NOW, reason="gate"
        )
    )
    return state


def test_missing_file_is_unknown_history(env):
    state = run_state_lib.load(env)
    assert state.prefix == "abc"
    assert state.updated is None
    assert state.steps == {}
    assert not env.run_state.exists()


def test_round_trip(env):
    state = _filled(env)
    run_state_lib.save(env, state, _NOW)
    assert conftest.mode(env.run_state) == 0o600
    loaded = run_state_lib.load(env)
    assert loaded.updated == _NOW
    assert loaded == state
    assert loaded.step("s0.apply_final").status == model.StepStatus.DONE


def test_file_shape(env):
    run_state_lib.save(env, _filled(env), _NOW)
    data = json.loads(env.run_state.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert set(data) == {
        "schema_version",
        "prefix",
        "updated",
        "engine",
        "last_run",
        "steps",
        "stage0",
        "iam",
    }
    step = data["steps"]["s0.apply_final"]
    assert step["state"] == {
        "lineage": helpers_deploy.LINEAGE,
        "serial": 298,
        "remote_generation": 17,
    }
    assert step["confirmations"][0]["decision"] == "confirmed"


def test_step_adds_a_record_once(env):
    state = run_state_lib.load(env)
    record = state.step("s.x")
    assert state.step("s.x") is record


def test_confirmed_and_confirmations(env):
    state = _filled(env)
    step_id = "s0.apply_final"
    assert state.confirmed(step_id, run_state_lib.IAM_GATE)
    assert not state.confirmed(
        step_id, run_state_lib.IAM_GATE, run_state_lib.SKIPPED
    )
    assert not state.confirmed(step_id, run_state_lib.MANUAL)
    assert not state.confirmed("s0.missing", run_state_lib.IAM_GATE)
    found = list(state.confirmations(run_state_lib.IAM_GATE))
    assert [(found_id, item.decision) for found_id, item in found] == [
        (step_id, run_state_lib.CONFIRMED)
    ]
    assert list(state.confirmations(run_state_lib.MANUAL)) == []


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ('{"schema_version": 2, "prefix": "abc"}', "schema_version 2"),
        ("[]", "schema_version None"),
        ("{not json", "Cannot read"),
        ('{"schema_version": 1, "prefix": "abc", "bad": 1}', "is invalid"),
    ],
)
def test_unreadable_files_refuse(env, text, match):
    env.run_state.write_text(text, encoding="utf-8")
    with pytest.raises(run_state_lib.RunStateError, match=match):
        run_state_lib.load(env)


def test_lock_holds_the_command(env):
    lock = run_state_lib.Lock(env, "deploy --stage 0", _NOW)
    lock.acquire()
    assert conftest.mode(lock.path) == 0o600
    holder = run_state_lib.lock_holder(env)
    assert holder == {
        "command": "deploy --stage 0",
        "started": _NOW.isoformat(),
    }
    lock.release()
    assert not lock.path.exists()
    assert run_state_lib.lock_holder(env) is None


def test_lock_conflict(env):
    run_state_lib.Lock(env, "deploy --stage 0", _NOW).acquire()
    other = run_state_lib.Lock(env, "deploy --stage 1", _NOW)
    with pytest.raises(run_state_lib.LockHeldError) as raised:
        other.acquire()
    message = str(raised.value)
    assert "deploy --stage 0" in message
    assert f"Delete {env.root / 'deploy.lock'}" in message
    assert raised.value.path == env.root / "deploy.lock"


def test_release_keeps_the_lock_of_another_deploy(env):
    stale = run_state_lib.Lock(env, "deploy --stage 0", _NOW)
    stale.acquire()
    # The operator deletes the stale lock, and another deploy takes it.
    env.deploy_lock.unlink()
    run_state_lib.Lock(env, "deploy --stage 1", _NOW).acquire()
    stale.release()
    assert run_state_lib.lock_holder(env) == {
        "command": "deploy --stage 1",
        "started": _NOW.isoformat(),
    }


def test_unreadable_lock_still_blocks(env):
    env.deploy_lock.write_text("garbage", encoding="utf-8")
    assert run_state_lib.lock_holder(env) == {}
    with pytest.raises(run_state_lib.LockHeldError, match="unknown command"):
        run_state_lib.Lock(env, "deploy", _NOW).acquire()
