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

"""Tests for the log bucket state fix of provider bug #15725."""

import io
import json
import os
import pathlib

import pytest
from rich import console as rich_console

import conftest
import helpers
import helpers_deploy
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import state_fix
from stellar_engine.terraform import runner as runner_lib
from stellar_engine.wizard import prompts

_PROJECT = "tst-prod-audit-logs-0"
_BUCKET_TYPE = "google_logging_project_bucket_config"


def _bucket(sink, project=f"projects/{_PROJECT}"):
    return helpers_deploy.resource(
        f'{state_fix.LOG_BUCKET_MODULE}["{sink}"]',
        _BUCKET_TYPE,
        "bucket",
        [
            helpers_deploy.instance(
                {"project": project, "bucket_id": sink, "location": "us-east4"},
                0,
            )
        ],
    )


def _projects(doc):
    return {
        address: instance["attributes"]["project"]
        for address, instance in probe_lib.instances(doc)
        if address.startswith(state_fix.LOG_BUCKET_MODULE)
    }


def _ctx(tmp_path, replies=(), **kwargs):
    prompter = prompts.ScriptedPrompter(list(replies))
    return helpers_deploy.make_ctx(tmp_path, prompter=prompter, **kwargs)


def test_log_buckets(tmp_path, repo):
    found = state_fix.log_buckets(_ctx(tmp_path))
    assert [bucket.sink for bucket in found] == repo.log_sink_names()
    first = found[0]
    assert first.address == (
        f'module.log-export-logbucket["{first.sink}"]'
        ".google_logging_project_bucket_config.bucket[0]"
    )
    assert first.import_id == (
        f"projects/{_PROJECT}/locations/us-east4/buckets/{first.sink}"
    )
    (only,) = state_fix.log_buckets(_ctx(tmp_path / "x"), ["vpc-sc"])
    assert only.sink == "vpc-sc"


def test_log_buckets_need_logging_sinks(tmp_path):
    answers = helpers.minimal_answers(logging={"sink_type": "storage"})
    assert state_fix.log_buckets(_ctx(tmp_path, answers=answers)) == []


def test_sinks_of():
    addresses = [
        'module.log-export-logbucket["vpc-sc"].google_logging_project_bucket'
        "_config.bucket[0]",
        'module.log-export-logbucket["audit-logs"].x',
        "module.organization.google_org_policy_policy.default",
        None,
    ]
    assert state_fix.sinks_of(addresses) == ["audit-logs", "vpc-sc"]


def test_rewrite_projects():
    doc = helpers_deploy.state_doc(
        [_bucket("audit-logs"), _bucket("vpc-sc"), _bucket("bare", _PROJECT)]
    )
    targets = {address for address, _ in probe_lib.instances(doc)} - {
        f'{state_fix.LOG_BUCKET_MODULE}["vpc-sc"].'
        f"{state_fix.LOG_BUCKET_RESOURCE}"
    }
    assert state_fix.rewrite_projects(doc, targets) == 1
    assert sorted(_projects(doc).values()) == [
        f"projects/{_PROJECT}",
        _PROJECT,
        _PROJECT,
    ]


def _script_pulls(runner, *docs):
    runner.results["state pull"] = [
        helpers_deploy.completed(json.dumps(doc)) for doc in docs
    ]


def test_fix_imports_the_missing_and_rewrites(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, [True], runner=runner)
    buckets = state_fix.log_buckets(ctx)
    before = helpers_deploy.state_doc([_bucket(buckets[0].sink)], serial=206)
    after = helpers_deploy.state_doc(
        [_bucket(bucket.sink) for bucket in buckets], serial=210
    )
    _script_pulls(runner, before, after)
    assert state_fix.fix_log_buckets(ctx, buckets, step_id="s0.apply_final")
    calls = [args for args, _ in runner.calls]
    assert [args for args in calls if args[0] == "import"] == [
        ("import", "-no-color", "-input=false", b.address, b.import_id)
        for b in buckets[1:]
    ]
    (push,) = [args for args in calls if args[:2] == ("state", "push")]
    pushed_path = pathlib.Path(push[-1])
    pushed = json.loads(pushed_path.read_text(encoding="utf-8"))
    assert pushed["serial"] == 211
    assert set(_projects(pushed).values()) == {_PROJECT}
    assert conftest.mode(pushed_path) == 0o600
    (backup,) = ctx.env.plans.glob(
        f"terraform.tfstate.before-{state_fix.STEP}.*"
    )
    assert json.loads(backup.read_text(encoding="utf-8")) == before
    assert conftest.mode(backup) == 0o600
    (confirmation,) = ctx.record("s0.apply_final").confirmations
    assert confirmation.kind == "bucket_fix"
    assert "serial 206 to 211" in confirmation.detail


def test_fix_without_changes(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, [True], runner=runner)
    buckets = state_fix.log_buckets(ctx)
    done = helpers_deploy.state_doc(
        [_bucket(bucket.sink, _PROJECT) for bucket in buckets]
    )
    _script_pulls(runner, done, done)
    assert not state_fix.fix_log_buckets(ctx, buckets)
    subcommands = helpers_deploy.subcommands(runner)
    assert subcommands == ["state pull", "state pull"]


def test_fix_nothing_to_fix(tmp_path):
    runner = conftest.FakeTerraform()
    assert not state_fix.fix_log_buckets(_ctx(tmp_path, runner=runner), [])
    assert runner.calls == []


def test_fix_without_a_terminal_lists_the_commands(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, runner=runner, interactive=False, yes=True)
    buckets = state_fix.log_buckets(ctx)
    with pytest.raises(model.InputRequiredError) as raised:
        state_fix.fix_log_buckets(ctx, buckets)
    remedy = raised.value.remedy or ""
    assert f"terraform -chdir={ctx.workspace('0')} state pull" in remedy
    assert buckets[0].import_id in remedy
    assert "state push" in remedy
    assert runner.calls == []


def test_fix_stops_on_environment_problems(tmp_path):
    # Terraform would push the state with other credentials than preflight.
    empty = tmp_path / "gcloud"
    empty.mkdir()
    runner = conftest.FakeTerraform()
    ctx = _ctx(
        tmp_path, [True], runner=runner, environ={"CLOUDSDK_CONFIG": str(empty)}
    )
    with pytest.raises(model.BlockedError, match="CLOUDSDK_CONFIG"):
        state_fix.fix_log_buckets(ctx, state_fix.log_buckets(ctx))
    assert runner.calls == []
    assert helpers_deploy.asked(ctx) == []


def test_fix_declined(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, [False], runner=runner)
    with pytest.raises(model.StoppedError):
        state_fix.fix_log_buckets(ctx, state_fix.log_buckets(ctx))
    assert runner.calls == []


def test_fix_stops_at_a_failed_import(tmp_path):
    runner = conftest.FakeTerraform(
        results={"import": [helpers_deploy.completed("Error: no", 1)]}
    )
    ctx = _ctx(tmp_path, [True], runner=runner)
    _script_pulls(runner, helpers_deploy.state_doc())
    with pytest.raises(model.CommandError) as raised:
        state_fix.fix_log_buckets(ctx, state_fix.log_buckets(ctx))
    assert raised.value.command == "import"
    assert "state push" not in helpers_deploy.subcommands(runner)


def test_fix_stops_at_a_failed_pull(tmp_path):
    runner = conftest.FakeTerraform(
        results={"state pull": [helpers_deploy.completed("", 1, "locked")]}
    )
    ctx = _ctx(tmp_path, [True], runner=runner)
    with pytest.raises(model.CommandError, match="state pull") as raised:
        state_fix.fix_log_buckets(ctx, state_fix.log_buckets(ctx))
    assert raised.value.output == "locked"


@pytest.mark.terraform
def test_fix_pulls_rewrites_and_pushes_with_terraform(tmp_path):
    runner = runner_lib.SystemRunner(rich_console.Console(file=io.StringIO()))
    ctx = _ctx(tmp_path, [True], runner=runner, environ=dict(os.environ))
    buckets = state_fix.log_buckets(ctx)
    stand_in = helpers_deploy.resource(
        None,
        "terraform_data",
        "stand_in",
        [helpers_deploy.instance({"id": "x", "input": None, "output": None})],
    )
    stand_in["provider"] = 'provider["terraform.io/builtin/terraform"]'
    state = helpers_deploy.state_doc(
        [*(_bucket(bucket.sink) for bucket in buckets), stand_in], serial=206
    )
    workspace = ctx.workspace("0")
    workspace.mkdir(parents=True)
    state_file = workspace / probe_lib.STATE_FILE
    state_file.write_text(json.dumps(state), encoding="utf-8")
    assert state_fix.fix_log_buckets(ctx, buckets)
    fixed = json.loads(state_file.read_text(encoding="utf-8"))
    assert fixed["lineage"] == helpers_deploy.LINEAGE
    assert fixed["serial"] > 206
    assert set(_projects(fixed).values()) == {_PROJECT}
    assert len(_projects(fixed)) == len(buckets)
    (kept,) = [r for r in fixed["resources"] if r["type"] == "terraform_data"]
    assert kept["instances"][0]["attributes"]["id"] == "x"
    assert list(ctx.env.plans.glob("terraform.tfstate.before-bucket-fix.*"))
