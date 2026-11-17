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

"""Tests for the `stellar iam snapshot`, `diff` and `restore` commands."""

import json

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine import iam_diff
from stellar_engine.gcp import api

pytestmark = pytest.mark.usefixtures("isolated_home")
# A role that Stage 0 binds authoritatively, and one it does not.
_STAGE0_ROLE = "roles/assuredworkloads.admin"
_OTHER_ROLE = "roles/viewer"
_OLD = "user:old@example.com"
_NEW = "user:new@example.com"


@pytest.fixture
def cloud_env(cli_runner, monkeypatch, fake_cloud):
    """Creates an environment and fixes the console, clock and engine.

    Returns:
        The FakeCloud the commands use.
    """
    helpers_deploy.fix_command_output(monkeypatch)
    assert helpers.init_env(cli_runner).exit_code == 0
    fake_cloud.policy = _policy({_STAGE0_ROLE: [_OLD], _OTHER_ROLE: [_OLD]})
    return fake_cloud


def _policy(bindings, etag=conftest.ETAG):
    return {
        "version": 1,
        "etag": etag,
        "bindings": [
            {"role": role, "members": members}
            for role, members in bindings.items()
        ],
    }


def _iam(cli_runner, *args):
    return helpers.invoke(cli_runner, "iam", *args)


def _snapshot(cli_runner, home):
    outcome = _iam(cli_runner, "snapshot")
    assert outcome.exit_code == 0, outcome.output
    (path,) = helpers.env(home).iam_snapshots.glob("*-manual.json")
    return path


def _row(output, *cells):
    """Returns whether one table line holds every cell."""
    return any(
        all(cell in line for cell in cells) for line in output.splitlines()
    )


_replies = helpers_deploy.scripted_replies


def test_snapshot_saves_the_policy_and_its_metadata(
    cli_runner, isolated_home, cloud_env
):
    path = _snapshot(cli_runner, isolated_home)
    assert path.name == "20261029T120001Z-manual.json"
    assert conftest.mode(path) == 0o600
    saved = json.loads(path.read_text())
    assert saved["bindings"][0]["members"] == [_OLD]
    # gcloud would send a stale etag, which setIamPolicy rejects.
    assert "etag" not in saved
    snap = iam_diff.read_snapshot(path)
    assert snap.meta is not None
    assert snap.meta.etag == conftest.ETAG
    assert snap.meta.org_id == conftest.ORG_ID
    assert snap.meta.engine_commit == helpers_deploy.COMMIT
    assert snap.meta.principal == conftest.USER


def test_snapshot_rejects_a_reason_that_is_no_slug(
    cli_runner, isolated_home, cloud_env
):
    outcome = _iam(cli_runner, "snapshot", "--reason", "Before Audit")
    assert outcome.exit_code == 2
    assert "not a slug" in outcome.output


def test_snapshot_reports_cloud_errors(cli_runner, isolated_home, cloud_env):
    cloud_env.policy = api.AccessDeniedError("denied")
    outcome = _iam(cli_runner, "snapshot")
    assert outcome.exit_code == 1
    assert "denied" in outcome.output


def test_diff_lists_the_changes_since_the_newest_snapshot(
    cli_runner, isolated_home, cloud_env
):
    _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW], _OTHER_ROLE: [_OLD]})
    outcome = _iam(cli_runner, "diff")
    assert outcome.exit_code == 0, outcome.output
    assert _row(outcome.output, "removed", _STAGE0_ROLE, _OLD)
    assert _row(outcome.output, "added", _STAGE0_ROLE, _NEW)
    assert "1 removed, 1 added, 1 kept" in outcome.output


def test_diff_against_a_named_snapshot(cli_runner, isolated_home, cloud_env):
    older = _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW], _OTHER_ROLE: [_OLD]})
    later = _iam(cli_runner, "snapshot", "--reason", "later")
    assert later.exit_code == 0, later.output
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW], _OTHER_ROLE: [_NEW]})
    outcome = _iam(cli_runner, "diff", "--snapshot", str(older))
    assert outcome.exit_code == 0, outcome.output
    assert f"Changes since {older.name}" in outcome.output
    assert _row(outcome.output, "removed", _STAGE0_ROLE, _OLD)
    assert _row(outcome.output, "removed", _OTHER_ROLE, _OLD)
    assert _row(outcome.output, "added", _OTHER_ROLE, _NEW)
    assert "2 removed, 2 added, 0 kept" in outcome.output


def test_diff_without_a_snapshot(cli_runner, isolated_home, cloud_env):
    outcome = _iam(cli_runner, "diff")
    assert outcome.exit_code == 2
    assert "no IAM snapshot yet" in outcome.output


def test_diff_of_a_saved_plan(cli_runner, isolated_home, cloud_env, tmp_path):
    doc = helpers_deploy.plan_doc(
        [helpers_deploy.binding(_STAGE0_ROLE, [_NEW])]
    )
    plan = tmp_path / "0-s0.apply_final-20261029T120000Z.json"
    plan.write_text(json.dumps(doc))
    tfplan = plan.with_suffix(".tfplan")
    outcome = _iam(cli_runner, "diff", "--plan", str(tfplan))
    assert outcome.exit_code == 0, outcome.output
    assert f"Changes of {tfplan.name}" in outcome.output
    assert "1 removed, 1 added, 0 kept" in outcome.output
    both = _iam(cli_runner, "diff", "--plan", str(plan), "--snapshot", "x")
    assert both.exit_code == 2
    missing = _iam(cli_runner, "diff", "--plan", str(tmp_path / "no.json"))
    assert missing.exit_code == 2


def test_diff_reads_relative_paths_from_the_environment(
    cli_runner, isolated_home, cloud_env, tmp_path, monkeypatch
):
    snap = _snapshot(cli_runner, isolated_home)
    env = helpers.env(isolated_home)
    doc = helpers_deploy.plan_doc(
        [helpers_deploy.binding(_STAGE0_ROLE, [_NEW])]
    )
    plan = env.plans / "0-s0.apply_final-20261029T120000Z.json"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(json.dumps(doc))
    # The paths that the deploy prints are relative to the environment.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW], _OTHER_ROLE: [_OLD]})
    outcome = _iam(
        cli_runner, "diff", "--snapshot", f"iam-snapshots/{snap.name}"
    )
    assert outcome.exit_code == 0, outcome.output
    assert "1 removed, 1 added, 1 kept" in outcome.output
    tfplan = f"plans/{plan.with_suffix('.tfplan').name}"
    outcome = _iam(cli_runner, "diff", "--plan", tfplan)
    assert outcome.exit_code == 0, outcome.output
    assert "0 removed, 0 added" in outcome.output
    # A file of the current directory wins.
    local = elsewhere / "iam-snapshots" / snap.name
    local.parent.mkdir()
    local.write_text(json.dumps(_policy({_OTHER_ROLE: [_OLD]})))
    outcome = _iam(
        cli_runner, "diff", "--snapshot", f"iam-snapshots/{snap.name}"
    )
    assert outcome.exit_code == 0, outcome.output
    assert _row(outcome.output, "added", _STAGE0_ROLE, _NEW)
    assert "0 removed, 1 added" in outcome.output


def test_restore_writes_the_snapshot_back(
    cli_runner, isolated_home, cloud_env, monkeypatch
):
    path = _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW]}, etag="BwYAAAAAAAB=")
    prompter = _replies(monkeypatch, f" {conftest.ORG_ID} ")
    outcome = _iam(cli_runner, "restore", str(path))
    assert outcome.exit_code == 0, outcome.output
    assert prompter.asked == [
        f"This replaces the IAM policy of organization {conftest.ORG_ID}. "
        f"Type {conftest.ORG_ID} to confirm:"
    ]
    (write,) = cloud_env.writes
    method, org_id, policy, etag, mask = write
    assert (method, org_id, etag) == (
        "set_org_iam_policy",
        conftest.ORG_ID,
        "BwYAAAAAAAB=",
    )
    assert policy == iam_diff.read_snapshot(path).policy
    assert mask == ("bindings", "etag", "auditConfigs")
    (backup,) = helpers.env(isolated_home).iam_snapshots.glob("*-restore.json")
    assert json.loads(backup.read_text())["bindings"][0]["members"] == [_NEW]


def test_restore_needs_the_typed_organization(
    cli_runner, isolated_home, cloud_env, monkeypatch
):
    path = _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW]})
    outcome = _iam(cli_runner, "restore", str(path), "--non-interactive")
    assert outcome.exit_code == 4
    _replies(monkeypatch, "yes")
    outcome = _iam(cli_runner, "restore", str(path))
    assert outcome.exit_code == 4
    assert "did not match" in outcome.output
    assert not cloud_env.writes


def test_restore_retries_a_stale_etag(
    cli_runner, isolated_home, cloud_env, monkeypatch
):
    path = _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW]})
    cloud_env.write_errors["set_org_iam_policy"] = api.ConflictError("etag")
    prompter = _replies(monkeypatch, conftest.ORG_ID)
    outcome = _iam(cli_runner, "restore", str(path))
    assert outcome.exit_code == 1
    assert "changed during each of 3 writes" in outcome.output
    assert "gcloud organizations set-iam-policy" in outcome.output
    assert len(cloud_env.writes) == 3
    # The changes stayed the same, so the retries asked nothing more.
    assert len(prompter.asked) == 1
    snapshots = helpers.env(isolated_home).iam_snapshots
    assert len(list(snapshots.glob("*-restore*.json"))) == 6


_LATE = "user:late@example.com"


def _grant_during_the_first_write(cloud):
    """Adds a grant to the live policy when the restore first writes."""
    write = cloud.set_org_iam_policy

    def concurrent(org_id, policy, *, etag, update_mask):
        if not cloud.writes:
            cloud.policy = _policy(
                {_STAGE0_ROLE: [_NEW], _OTHER_ROLE: [_LATE]},
                etag="BwYCCCCCCCC=",
            )
        return write(org_id, policy, etag=etag, update_mask=update_mask)

    cloud.set_org_iam_policy = concurrent


def test_restore_asks_again_after_a_concurrent_change(
    cli_runner, isolated_home, cloud_env, monkeypatch
):
    path = _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW]})
    _grant_during_the_first_write(cloud_env)
    prompter = _replies(monkeypatch, conftest.ORG_ID, conftest.ORG_ID)
    outcome = _iam(cli_runner, "restore", str(path))
    assert outcome.exit_code == 0, outcome.output
    assert len(prompter.asked) == 2
    # The operator saw the grant that the restore now removes.
    assert "after a concurrent change" in outcome.output
    assert _row(outcome.output, "removed", _OTHER_ROLE, _LATE)
    backups = sorted(
        helpers.env(isolated_home).iam_snapshots.glob("*-restore*.json")
    )
    late = [p for p in backups if not p.name.endswith(".meta.json")][-1]
    assert _LATE in late.read_text()
    assert len(cloud_env.writes) == 2


def test_restore_stops_when_the_concurrent_change_is_declined(
    cli_runner, isolated_home, cloud_env, monkeypatch
):
    path = _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW]})
    _grant_during_the_first_write(cloud_env)
    _replies(monkeypatch, conftest.ORG_ID, "no")
    outcome = _iam(cli_runner, "restore", str(path))
    assert outcome.exit_code == 4
    assert "did not match" in outcome.output
    assert len(cloud_env.writes) == 1


def test_restore_of_a_matching_policy_writes_nothing(
    cli_runner, isolated_home, cloud_env
):
    path = _snapshot(cli_runner, isolated_home)
    outcome = _iam(cli_runner, "restore", str(path), "--non-interactive")
    assert outcome.exit_code == 0, outcome.output
    assert "already matches the snapshot" in outcome.output
    assert not cloud_env.writes


def test_restore_refuses_another_organization(
    cli_runner, isolated_home, cloud_env
):
    path = _snapshot(cli_runner, isolated_home)
    meta = path.with_name(path.name.replace(".json", ".meta.json"))
    data = json.loads(meta.read_text())
    data["org_id"] = "999999999999"
    meta.write_text(json.dumps(data))
    outcome = _iam(cli_runner, "restore", str(path))
    assert outcome.exit_code == 2
    assert "999999999999" in outcome.output


def test_restore_emits_overrides_for_stage0_roles(
    cli_runner, isolated_home, cloud_env
):
    path = _snapshot(cli_runner, isolated_home)
    cloud_env.policy = _policy({_STAGE0_ROLE: [_NEW]})
    outcome = _iam(cli_runner, "restore", str(path), "--emit-overrides")
    assert outcome.exit_code == 0, outcome.output
    assert f"Stage 0 does not manage {_OTHER_ROLE} {_OLD}" in outcome.output
    assert "Added 1 grants to overrides.0-bootstrap.iam" in outcome.output
    answers = helpers.load_answers(isolated_home)
    assert answers.overrides["0-bootstrap"]["iam"] == {_STAGE0_ROLE: [_OLD]}
    assert not cloud_env.writes
