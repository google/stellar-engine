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

"""Tests for the Terraform runner and its facade.

The unit tests fake `subprocess.Popen` or the runner. The tests that run a
small shell script as the binary cover streaming, teeing and timeouts with
a real process. The tests marked `terraform` check the argv order, the
saved-plan flow, the state migration and the environment scrub against the
real binary, with only the builtin `terraform_data` resource, so no
provider is downloaded.
"""

import datetime
import io
import json
import os
import pathlib
import subprocess
import time
import types

import pytest
from rich import console as rich_console

import conftest
import helpers
from stellar_engine.terraform import env as env_lib
from stellar_engine.terraform import guards
from stellar_engine.terraform import plan as plan_lib
from stellar_engine.terraform import runner

NOW = datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.UTC)
STAMP = "20260102T030405Z"
WORKSPACE = pathlib.Path("/envs/abc/fast/stages-aw/0-bootstrap")
PLAN = pathlib.Path("/envs/abc/plans/0-s0.apply_final.tfplan")
STATE = pathlib.Path("/envs/abc/plans/state-fixed.json")
ADDRESS = 'module.x["k"].google_logging_project_bucket_config.bucket[0]'


def _console():
    return rich_console.Console(file=io.StringIO(), width=200)


def _output(console):
    return console.file.getvalue()


class RecordingRunner:
    """A `Runner` that records each call and returns a scripted result."""

    def __init__(self, stdout="", stderr="", returncode=0):
        self.calls = []
        self.result = (stdout, stderr, returncode)

    def _call(self, kind, workspace, args, env, log, timeout):
        self.calls.append(
            types.SimpleNamespace(
                kind=kind,
                workspace=workspace,
                args=list(args),
                env=dict(env),
                log=log,
                timeout=timeout,
            )
        )
        stdout, stderr, returncode = self.result
        return subprocess.CompletedProcess(args, returncode, stdout, stderr)

    def run(self, workspace, args, *, env, log, timeout):
        return self._call("run", workspace, args, env, log, timeout)

    def capture(self, workspace, args, *, env, log, timeout):
        return self._call("capture", workspace, args, env, log, timeout)


def _facade(tmp_path, recording=None, environ=None, now=NOW):
    return runner.Terraform(
        recording or RecordingRunner(),
        environ if environ is not None else {"PATH": "/usr/bin"},
        tmp_path / "logs",
        lambda: now,
    )


@pytest.mark.parametrize(
    ("call", "kind", "args", "timeout"),
    [
        (
            lambda tf: tf.init(WORKSPACE),
            "run",
            ["init", "-no-color", "-input=false"],
            600,
        ),
        (
            lambda tf: tf.init(WORKSPACE, migrate=True, force_copy=True),
            "run",
            [
                "init",
                "-no-color",
                "-input=false",
                "-migrate-state",
                "-force-copy",
            ],
            600,
        ),
        (
            lambda tf: tf.plan(WORKSPACE, PLAN),
            "run",
            ["plan", "-no-color", "-input=false", f"-out={PLAN}"],
            900,
        ),
        (
            lambda tf: tf.plan(
                WORKSPACE, PLAN, targets=("google_x.y[0]", "module.z[0]")
            ),
            "run",
            [
                "plan",
                "-no-color",
                "-input=false",
                f"-out={PLAN}",
                "-target=google_x.y[0]",
                "-target=module.z[0]",
            ],
            900,
        ),
        (
            lambda tf: tf.apply(WORKSPACE, PLAN),
            "run",
            ["apply", "-no-color", "-input=false", str(PLAN)],
            7200,
        ),
        (
            lambda tf: tf.show_text(WORKSPACE, PLAN),
            "capture",
            ["show", "-no-color", str(PLAN)],
            300,
        ),
        (
            lambda tf: tf.state_push(WORKSPACE, STATE),
            "run",
            ["state", "push", "-no-color", str(STATE)],
            300,
        ),
        (
            lambda tf: tf.import_resource(WORKSPACE, ADDRESS, "projects/p"),
            "run",
            ["import", "-no-color", "-input=false", ADDRESS, "projects/p"],
            900,
        ),
        (
            lambda tf: tf.force_unlock(WORKSPACE, "1234"),
            "run",
            ["force-unlock", "-no-color", "-force", "1234"],
            120,
        ),
    ],
)
def test_facade_argv(tmp_path, call, kind, args, timeout):
    recording = RecordingRunner()
    call(_facade(tmp_path, recording))
    (made,) = recording.calls
    assert (made.kind, made.workspace, made.args) == (kind, WORKSPACE, args)
    assert made.timeout == timeout


@pytest.mark.parametrize(
    ("call", "args"),
    [
        (
            lambda tf: tf.show_json(WORKSPACE, PLAN),
            ["show", "-no-color", "-json", str(PLAN)],
        ),
        (lambda tf: tf.state_pull(WORKSPACE), ["state", "pull", "-no-color"]),
    ],
)
def test_facade_json_argv(tmp_path, call, args):
    recording = RecordingRunner(stdout='{"serial": 1}')
    assert call(_facade(tmp_path, recording)) == {"serial": 1}
    assert [made.args for made in recording.calls] == [args]
    assert recording.calls[0].kind == "capture"


def test_facade_makes_paths_absolute(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    recording = RecordingRunner()
    facade = _facade(tmp_path, recording)
    facade.plan(WORKSPACE, pathlib.Path("plans/x.tfplan"))
    facade.apply(WORKSPACE, pathlib.Path("plans/x.tfplan"))
    absolute = tmp_path / "plans/x.tfplan"
    assert recording.calls[0].args[-1] == f"-out={absolute}"
    assert recording.calls[1].args[-1] == str(absolute)


def test_facade_runs_with_the_scrubbed_environment(tmp_path):
    recording = RecordingRunner()
    facade = _facade(
        tmp_path,
        recording,
        environ={"PATH": "/usr/bin", "TF_VAR_x": "1", "TF_CLI_ARGS": "-x"},
    )
    facade.init(WORKSPACE)
    assert recording.calls[0].env == {
        "PATH": "/usr/bin",
        "TF_IN_AUTOMATION": "1",
        "TF_INPUT": "0",
    }
    assert facade.child_env.scrubbed == ("TF_CLI_ARGS", "TF_VAR_x")


def test_facade_names_one_private_log_per_command(tmp_path):
    recording = RecordingRunner()
    facade = _facade(
        tmp_path, recording, environ={"TF_VAR_x": "secret-value"}
    ).for_step("0", "s0.apply_final")
    facade.plan(WORKSPACE, PLAN)
    facade.plan(WORKSPACE, PLAN)
    facade.apply(WORKSPACE, PLAN)
    logs = tmp_path / "logs"
    assert [path.name for path in facade.logs] == [
        f"{STAMP}-0-s0.apply_final-plan.log",
        f"{STAMP}-0-s0.apply_final-plan.1.log",
        f"{STAMP}-0-s0.apply_final-apply.log",
    ]
    assert facade.last_log == logs / f"{STAMP}-0-s0.apply_final-apply.log"
    assert [made.log for made in recording.calls] == facade.logs
    assert conftest.mode(logs) == 0o700
    assert all(conftest.mode(log) == 0o600 for log in facade.logs)
    header = facade.logs[0].read_text(encoding="utf-8")
    assert f"# command: terraform -chdir={WORKSPACE} plan -no-color" in header
    assert "# scrubbed environment variables: TF_VAR_x" in header
    assert "secret-value" not in header


def test_for_step_keeps_the_original_unbound(tmp_path):
    facade = _facade(tmp_path)
    bound = facade.for_step("1", "s1.apply")
    bound.init(WORKSPACE)
    assert facade.logs == []
    assert facade.last_log is None
    facade.init(WORKSPACE)
    assert facade.last_log is not None
    assert facade.last_log.name == f"{STAMP}-init.log"
    assert bound.child_env is facade.child_env


def test_plan_files_and_backups(tmp_path):
    plans = tmp_path / "plans"
    later = NOW.astimezone(datetime.timezone(datetime.timedelta(hours=-5)))
    files = runner.plan_files(
        plans, stage="0", step="s0.apply_final", now=later
    )
    base = f"0-s0.apply_final-{STAMP}"
    assert files == runner.PlanFiles(
        tfplan=plans / f"{base}.tfplan",
        json=plans / f"{base}.json",
        text=plans / f"{base}.txt",
    )
    bound = _facade(tmp_path).for_step("0", "s0.apply_final")
    assert bound.plan_files(plans) == files
    assert runner.state_backup_path(plans, step="migrate", now=NOW) == (
        plans / f"terraform.tfstate.before-migrate.{STAMP}"
    )


@pytest.mark.parametrize(
    ("stdout", "message"),
    [("not json", "printed no JSON"), ("[1]", "printed no JSON object")],
)
def test_show_json_rejects_bad_output(tmp_path, stdout, message):
    facade = _facade(tmp_path, RecordingRunner(stdout=stdout))
    with pytest.raises(runner.TerraformError, match=message) as raised:
        facade.show_json(WORKSPACE, PLAN)
    assert raised.value.log == facade.last_log


def test_show_json_failure_carries_the_output(tmp_path):
    recording = RecordingRunner(stderr="Error: plan file stale", returncode=1)
    facade = _facade(tmp_path, recording)
    with pytest.raises(runner.TerraformError, match="exit status 1") as raised:
        facade.show_json(WORKSPACE, PLAN)
    assert "plan file stale" in raised.value.output
    with pytest.raises(runner.TerraformError):
        facade.show_text(WORKSPACE, PLAN)


def test_state_pull_without_state(tmp_path):
    assert (
        _facade(tmp_path, RecordingRunner(stdout="\n")).state_pull(WORKSPACE)
        == {}
    )


def test_returned_failures_are_not_raised(tmp_path):
    facade = _facade(tmp_path, RecordingRunner(returncode=1))
    assert facade.apply(WORKSPACE, PLAN).returncode == 1


def test_manual_commands_follow_the_runner_order(tmp_path):
    workspace = tmp_path / "work space"
    assert runner.manual(
        workspace, ("import",), ("-input=false",), ("a[0]", "id")
    ) == (f"terraform '-chdir={workspace}' import -input=false 'a[0]' id")
    saved = tmp_path / "plans" / "s0.tfplan"
    init, plan, apply = runner.manual_apply(workspace, saved)
    assert plan.endswith(f"plan -input=false -out={saved}")
    assert apply.endswith(f"apply -input=false {saved}")
    assert init.endswith("init -input=false")
    _, targeted, _ = runner.manual_apply(workspace, saved, ["a[0]"])
    assert targeted.endswith(f"plan -input=false '-target=a[0]' -out={saved}")


@pytest.mark.parametrize(
    ("args", "timeout"),
    [
        (["init"], 600),
        (["plan"], 900),
        (["apply"], 7200),
        (["state", "pull"], 300),
        (["version"], runner.DEFAULT_TIMEOUT),
        ([], runner.DEFAULT_TIMEOUT),
    ],
)
def test_timeout_for(args, timeout):
    assert runner.timeout_for(args) == timeout


@pytest.fixture
def popen(monkeypatch):
    """Replaces `subprocess.Popen` with a scripted fake."""
    script = types.SimpleNamespace(
        stdout="", stderr="", returncode=0, calls=[], error=None
    )

    class FakePopen:
        def __init__(self, argv, **kwargs):
            if script.error:
                raise script.error
            script.calls.append((argv, kwargs))
            merged = kwargs["stderr"] is subprocess.STDOUT
            text = script.stdout + (script.stderr if merged else "")
            self.stdout = io.StringIO(text)
            self.returncode = None

        def wait(self, timeout=None):
            self.returncode = script.returncode
            return self.returncode

        def communicate(self, timeout=None):
            self.returncode = script.returncode
            return script.stdout, script.stderr

        def send_signal(self, signal):
            raise AssertionError("unexpected signal")

        def kill(self):
            raise AssertionError("unexpected kill")

    monkeypatch.setattr(runner.subprocess, "Popen", FakePopen)
    return script


def test_run_streams_merged_output_to_console_and_log(tmp_path, popen):
    popen.stdout = "Plan: 1 to add\nmodule.x[0] created\n"
    popen.stderr = "Warning: targeting\n"
    popen.returncode = 2
    console = _console()
    log = tmp_path / "logs/run.log"
    completed = runner.SystemRunner(console).run(
        WORKSPACE, ["plan", "-no-color"], env={"A": "1"}, log=log, timeout=5
    )
    (argv, kwargs) = popen.calls[0]
    assert argv == ["terraform", f"-chdir={WORKSPACE}", "plan", "-no-color"]
    assert kwargs["env"] == {"A": "1"}
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.STDOUT
    assert "shell" not in kwargs
    assert completed.returncode == 2
    assert completed.stdout == popen.stdout + popen.stderr
    assert completed.args == argv
    assert _output(console) == popen.stdout + popen.stderr
    assert log.read_text(encoding="utf-8") == (
        popen.stdout + popen.stderr + "# exit status 2\n"
    )
    assert conftest.mode(log) == 0o600
    assert conftest.mode(log.parent) == 0o700


def test_run_appends_to_an_existing_log(tmp_path, popen):
    popen.stdout = "done\n"
    log = tmp_path / "run.log"
    log.write_text("# header\n", encoding="utf-8")
    runner.SystemRunner(_console()).run(
        WORKSPACE, ["init"], env={}, log=log, timeout=5
    )
    assert log.read_text(encoding="utf-8") == (
        "# header\ndone\n# exit status 0\n"
    )


def test_capture_separates_stderr(tmp_path, popen):
    popen.stdout = '{"format_version": "1.2"}'
    popen.stderr = "Warning: deprecated\n"
    console = _console()
    log = tmp_path / "show.log"
    completed = runner.SystemRunner(console).capture(
        WORKSPACE,
        ["show", "-no-color", "-json", "p"],
        env={},
        log=log,
        timeout=5,
    )
    assert completed.stdout == popen.stdout
    assert completed.stderr == popen.stderr
    assert popen.calls[0][1]["stderr"] is subprocess.PIPE
    # Stdout can hold the whole plan or state, so only stderr is logged.
    assert log.read_text(encoding="utf-8") == (
        "Warning: deprecated\n# exit status 0\n"
    )
    assert _output(console) == ""


@pytest.mark.parametrize("method", ["run", "capture"])
def test_missing_binary_is_reported_not_raised(tmp_path, popen, method):
    popen.error = FileNotFoundError(2, "No such file", "terraform")
    log = tmp_path / "x.log"
    completed = getattr(runner.SystemRunner(_console()), method)(
        WORKSPACE, ["init"], env={}, log=log, timeout=5
    )
    assert completed.returncode == runner.NOT_STARTED
    assert "cannot run terraform" in completed.stdout + completed.stderr
    assert "# exit status 127" in log.read_text(encoding="utf-8")


def _script(tmp_path, body):
    """Writes an executable shell script that stands in for Terraform."""
    path = tmp_path / "fake-terraform"
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o700)
    return str(path)


def test_real_process_merges_output_and_gets_only_its_env(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PARENT_ONLY", "leaked")
    binary = _script(
        tmp_path,
        'echo "args $*"\necho "parent=$PARENT_ONLY child=$CHILD"\n'
        'echo "to stderr" >&2\nexit 3',
    )
    console = _console()
    log = tmp_path / "run.log"
    completed = runner.SystemRunner(console, binary=binary).run(
        tmp_path,
        ["plan", "-no-color"],
        env={"CHILD": "yes"},
        log=log,
        timeout=30,
    )
    assert completed.returncode == 3
    assert completed.stdout == (
        f"args -chdir={tmp_path} plan -no-color\nparent= child=yes\nto stderr\n"
    )
    assert log.read_text(encoding="utf-8") == (
        completed.stdout + "# exit status 3\n"
    )
    assert _output(console) == completed.stdout


def test_real_process_capture(tmp_path):
    binary = _script(tmp_path, 'echo "{}"\necho "a warning" >&2')
    log = tmp_path / "capture.log"
    completed = runner.SystemRunner(_console(), binary=binary).capture(
        tmp_path, ["state", "pull", "-no-color"], env={}, log=log, timeout=30
    )
    assert (completed.returncode, completed.stdout) == (0, "{}\n")
    assert completed.stderr == "a warning\n"
    assert log.read_text(encoding="utf-8") == "a warning\n# exit status 0\n"


@pytest.mark.parametrize("method", ["run", "capture"])
def test_real_process_timeout_interrupts(tmp_path, method):
    binary = _script(tmp_path, "echo started\nexec sleep 30")
    log = tmp_path / "slow.log"
    started = time.monotonic()
    completed = getattr(
        runner.SystemRunner(_console(), binary=binary, grace=2), method
    )(tmp_path, ["apply"], env={}, log=log, timeout=1)
    assert time.monotonic() - started < 15
    assert completed.returncode != 0
    output = completed.stdout + completed.stderr
    assert "ran longer than 1 seconds and was interrupted" in output
    assert "interrupted" in log.read_text(encoding="utf-8")


def _system(tmp_path, environ=None):
    """Returns a facade over the real binary with logs under tmp_path."""
    return runner.Terraform(
        runner.SystemRunner(_console()),
        os.environ if environ is None else environ,
        tmp_path / "logs",
        lambda: NOW,
    )


def _write(directory, name, text):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(text, encoding="utf-8")


def _state(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["lineage"], data["serial"]


def _ok(completed):
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed


_IMPORT_OUTSIDE_TARGET = """
resource "terraform_data" "a" {
  input = "a"
}

resource "terraform_data" "b" {
  count = 0
  input = "b"
}

import {
  to = terraform_data.b[0]
  id = "x"
}
"""


@pytest.mark.terraform
def test_target_skips_an_import_outside_the_target(tmp_path, repo):
    workspace = tmp_path / "ws"
    _write(workspace, "main.tf", _IMPORT_OUTSIDE_TARGET)
    helpers.terraform_init(workspace)
    full = helpers.terraform(workspace, "plan", "-input=false")
    assert full.returncode != 0
    assert "Configuration for import target does not exist" in full.stderr
    facade = _system(tmp_path)
    out = tmp_path / "a.tfplan"
    _ok(facade.plan(workspace, out, targets=("terraform_data.a",)))
    plan = plan_lib.parse(facade.show_json(workspace, out))
    assert [(c.address, c.actions) for c in plan.changes] == [
        ("terraform_data.a", ("create",))
    ]
    assert not any(change.importing for change in plan.changes)
    # Every targeted plan is incomplete; the guards accept that only with
    # the target.
    assert not plan.complete
    assert (
        guards.evaluate(
            plan,
            stage="1",
            run_state=None,
            repo=repo,
            targeted_to="terraform_data.a",
        )
        == []
    )


_SHAPES = """
variable "v" {
  type    = string
  default = "one"
}

resource "terraform_data" "keep" {
  input = var.v
}

resource "terraform_data" "replace" {
  triggers_replace = var.v
}

resource "terraform_data" "each" {
  for_each = var.v == "one" ? toset(["x", "y"]) : toset(["x"])
  input    = each.key
}

resource "terraform_data" "added" {
  count = var.v == "one" ? 0 : 1
  input = "new"
}

output "v" {
  value = var.v
}
"""


@pytest.mark.terraform
def test_saved_plan_flow_and_show_json_shape(tmp_path):
    workspace = tmp_path / "ws"
    _write(workspace, "main.tf", _SHAPES)
    facade = _system(tmp_path)
    _ok(facade.init(workspace))
    first = tmp_path / "first.tfplan"
    _ok(facade.plan(workspace, first))
    applied = _ok(facade.apply(workspace, first))
    assert "Apply complete! Resources: 4 added" in applied.stdout
    assert facade.last_log is not None
    assert "Apply complete!" in facade.last_log.read_text(encoding="utf-8")
    _write(workspace, "terraform.tfvars", 'v = "two"\n')
    second = tmp_path / "second.tfplan"
    _ok(facade.plan(workspace, second))
    plan = plan_lib.parse(facade.show_json(workspace, second))
    assert plan.format_major == "1"
    assert plan.terraform_version
    assert (plan.applyable, plan.complete, plan.errored) == (True, True, False)
    assert plan.variable("v") == "two"
    assert plan.drift == ()
    found = {change.address: change for change in plan.changes}
    assert found['terraform_data.each["x"]'].actions == ("no-op",)
    deleted = found['terraform_data.each["y"]']
    assert (deleted.actions, deleted.action_reason, deleted.index) == (
        ("delete",),
        "delete_because_each_key",
        "y",
    )
    assert found["terraform_data.keep"].actions == ("update",)
    assert found["terraform_data.keep"].unknown_attributes == ("output",)
    replaced = found["terraform_data.replace"]
    assert replaced.action == "replace"
    assert replaced.action_reason == "replace_because_cannot_update"
    assert replaced.replace_paths == (("triggers_replace",),)
    assert "id" in replaced.unknown_attributes
    added = found["terraform_data.added[0]"]
    assert (added.actions, added.index, added.before) == (("create",), 0, None)
    assert plan_lib.summary(plan) == {
        "create": 1,
        "update": 1,
        "replace": 1,
        "delete": 1,
        "forget": 0,
        "import": 0,
        "read": 0,
        "no-op": 1,
    }
    assert "terraform_data.replace" in facade.show_text(workspace, second)
    _ok(facade.apply(workspace, second))


_ONE = """
resource "terraform_data" "a" {
  input = "{value}"
}
"""


def _local_backend(workspace, destination):
    _write(
        workspace,
        "backend.tf",
        f'terraform {{\n  backend "local" {{\n    path = "{destination}"\n'
        "  }\n}\n",
    )


def _apply(facade, workspace, value, out):
    _write(workspace, "main.tf", _ONE.replace("{value}", value))
    _ok(facade.init(workspace))
    _ok(facade.plan(workspace, out))
    _ok(facade.apply(workspace, out))


@pytest.mark.terraform
def test_migrate_state_copies_once_then_does_nothing(tmp_path):
    workspace = tmp_path / "ws"
    facade = _system(tmp_path)
    _apply(facade, workspace, "a", tmp_path / "a.tfplan")
    local = workspace / "terraform.tfstate"
    lineage, serial = _state(local)
    destination = tmp_path / "remote/default.tfstate"
    destination.parent.mkdir()
    _local_backend(workspace, destination)
    refused = facade.init(workspace, migrate=True)
    assert refused.returncode != 0
    assert "Can't ask approval for state migration" in refused.stdout
    _ok(facade.init(workspace, migrate=True, force_copy=True))
    remote_lineage, remote_serial = _state(destination)
    assert remote_lineage == lineage
    assert remote_serial >= serial
    assert local.stat().st_size == 0
    assert _state(workspace / "terraform.tfstate.backup") == (lineage, serial)
    cached = json.loads(
        (workspace / ".terraform/terraform.tfstate").read_text(encoding="utf-8")
    )
    assert cached["backend"]["type"] == "local"
    copied = destination.read_bytes()
    _ok(facade.init(workspace, migrate=True, force_copy=True))
    assert destination.read_bytes() == copied
    # With the backend recorded, init ignores even a stale local state.
    local.write_bytes((workspace / "terraform.tfstate.backup").read_bytes())
    _ok(facade.init(workspace, migrate=True, force_copy=True))
    assert destination.read_bytes() == copied


@pytest.mark.terraform
def test_force_copy_overwrites_a_newer_destination(tmp_path):
    # Why stellar compares lineage and serial before it migrates: without
    # a recorded backend, -force-copy copies a stale local state over a
    # newer destination without asking.
    workspace = tmp_path / "ws"
    facade = _system(tmp_path)
    _apply(facade, workspace, "a", tmp_path / "a.tfplan")
    destination = tmp_path / "remote/default.tfstate"
    destination.parent.mkdir()
    _local_backend(workspace, destination)
    _ok(facade.init(workspace, migrate=True, force_copy=True))
    _apply(facade, workspace, "b", tmp_path / "b.tfplan")
    lineage, newer = _state(destination)
    stale = workspace / "terraform.tfstate.backup"
    (workspace / "terraform.tfstate").write_bytes(stale.read_bytes())
    _, stale_serial = _state(stale)
    assert stale_serial < newer
    (workspace / ".terraform/terraform.tfstate").unlink()
    _ok(facade.init(workspace, migrate=True, force_copy=True))
    assert _state(destination) == (lineage, stale_serial)


_VARIABLES = """
variable "x" {
  type    = string
  default = "default"
}

variable "y" {
  type    = string
  default = "default"
}

resource "terraform_data" "a" {
  input = "${var.x}-${var.y}"
}
"""


@pytest.mark.terraform
def test_parent_variables_and_cli_args_do_not_leak(tmp_path, monkeypatch):
    monkeypatch.setenv("TF_VAR_x", "leaked")
    monkeypatch.setenv("TF_CLI_ARGS_plan", "-var=y=injected")
    workspace = tmp_path / "ws"
    _write(workspace, "main.tf", _VARIABLES)
    facade = _system(tmp_path)
    assert "TF_VAR_x" in facade.child_env.scrubbed
    assert "TF_CLI_ARGS_plan" in facade.child_env.scrubbed
    _ok(facade.init(workspace))
    out = tmp_path / "p.tfplan"
    _ok(facade.plan(workspace, out))
    plan = plan_lib.parse(facade.show_json(workspace, out))
    assert plan.variables == {"x": "default", "y": "default"}


@pytest.mark.terraform
def test_state_import_and_unlock_argv(tmp_path):
    workspace = tmp_path / "ws"
    facade = _system(tmp_path)
    _apply(facade, workspace, "a", tmp_path / "a.tfplan")
    _write(
        workspace,
        "imported.tf",
        'resource "terraform_data" "imported" {\n  input = "i"\n}\n',
    )
    _ok(facade.import_resource(workspace, "terraform_data.imported", "id-1"))
    state = facade.state_pull(workspace)
    addresses = {
        f"{resource['type']}.{resource['name']}"
        for resource in state["resources"]
    }
    assert addresses == {"terraform_data.a", "terraform_data.imported"}
    state["serial"] += 1
    pushed = tmp_path / "pushed.tfstate"
    pushed.write_text(json.dumps(state), encoding="utf-8")
    _ok(facade.state_push(workspace, pushed))
    assert facade.state_pull(workspace)["serial"] == state["serial"]
    unlocked = facade.force_unlock(workspace, "1234")
    # The local backend has no lock to release, but parses the arguments.
    assert "not locked" in unlocked.stdout
    assert all(conftest.mode(log) == 0o600 for log in facade.logs)


def test_child_env_problems_reach_the_log(tmp_path):
    facade = _facade(tmp_path, environ={"CLOUDSDK_CONFIG": "/nowhere"})
    facade.init(WORKSPACE)
    assert facade.child_env.problems
    assert facade.last_log is not None
    text = facade.last_log.read_text(encoding="utf-8")
    assert "# problem: CLOUDSDK_CONFIG is set" in text
    assert env_lib.ADC_FILENAME in text
