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

"""Deploy contexts, scripted steps, plans and states for the deploy tests.

`make_ctx` builds a `model.Context` on a temp home with the real checkout,
a `FakeCloud`, a `FakeTerraform` runner, a scripted prompter, a clock that
ticks one second per call and a recorded sleep. `Script` builds steps whose
checks and runs follow a script. `pipeline_ctx` prepares a context whose
runner plans scripted documents, for the apply and IAM review tests.
"""

import dataclasses
import datetime
import io
import json
import re
import subprocess

from rich import console as rich_console

import conftest
import helpers
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.commands import common
from stellar_engine.config import answers as answers_lib
from stellar_engine.deploy import model
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.terraform import runner as runner_lib
from stellar_engine.wizard import prompts

NOW = datetime.datetime(2026, 10, 29, 12, 0, tzinfo=datetime.UTC)
COMMIT = "0123456789abcdef0123456789abcdef01234567"
LINEAGE = "00000000-1111-2222-3333-444444444444"
_BINDINGS = "module.organization.google_organization_iam_binding.authoritative"
# The resource name: the last name before an optional index.
_NAME_RE = re.compile(r"\.([\w-]+)(\[[^\]]*\])?$")
WORKLOAD = f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/w-1"
# The authoritative role and the members of the organization IAM tests.
IAM_ROLE = "roles/logging.admin"
ADMINS = f"group:gcp-organization-admins@{conftest.DOMAIN}"
OLD_MEMBER = f"user:old@{conftest.DOMAIN}"


class Clock:
    """Returns a time one second later on every call."""

    def __init__(self, start=NOW):
        self.current = start

    def __call__(self):
        self.current += datetime.timedelta(seconds=1)
        return self.current


@dataclasses.dataclass(frozen=True)
class FixedRepo(repo_lib.Repo):
    """The checkout under test with a fixed git provenance."""

    commit: str | None = COMMIT
    dirty: bool = False

    def provenance(self):
        if self.commit is None:
            return None
        return repo_lib.Provenance(self.commit, self.dirty)


def make_ctx(
    tmp_path,
    *,
    cloud=None,
    runner=None,
    answers=None,
    prompter=None,
    repo=None,
    yes=False,
    interactive=True,
    environ=None,
    sleep=None,
):
    """Returns a deploy context on a fresh environment under tmp_path.

    The answers are saved, so steps can update them. `sleep` defaults to
    a function that returns at once; pass `list.append` to record waits.
    """
    home = tmp_path / "home"
    answers = answers or helpers.minimal_answers()
    env = paths.EnvPaths(home / "envs" / answers.prefix, answers.prefix)
    env.ensure()
    answers_lib.save(env.answers, answers)
    clock = Clock()
    console = rich_console.Console(
        file=io.StringIO(), width=200, color_system=None
    )
    environ = environ or {}
    return model.Context(
        env=env,
        home=home,
        repo=repo or FixedRepo(conftest.REPO_ROOT),
        answers=answers,
        cloud=cloud or conftest.FakeCloud(),
        tools=conftest.FakeTools(),
        terraform=runner_lib.Terraform(
            runner or conftest.FakeTerraform(), environ, env.logs, clock
        ),
        prompter=prompter or prompts.ScriptedPrompter([]),
        console=console,
        now=clock,
        environ=environ,
        run_state=run_state_lib.load(env),
        yes=yes,
        interactive=interactive,
        sleep=sleep or _no_wait,
    )


def _no_wait(seconds):
    del seconds


def scripted_ctx(tmp_path, replies=(), **kwargs):
    """Returns a `make_ctx` context whose prompter gives these replies."""
    prompter = prompts.ScriptedPrompter(list(replies))
    return make_ctx(tmp_path, prompter=prompter, **kwargs)


def asked(ctx):
    """Returns the questions the scripted prompter was asked."""
    return ctx.prompter.asked


def output(ctx):
    """Returns what the context printed."""
    return ctx.console.file.getvalue()


def fix_command_output(monkeypatch):
    """Fixes the console width, the clock and the engine commit of commands.

    The deploy, status and iam command tests then print the same lines and
    file names on every run.
    """
    monkeypatch.setattr(
        common,
        "console",
        lambda stderr=False: rich_console.Console(width=200, color_system=None),
    )
    monkeypatch.setattr(common, "now", Clock())
    monkeypatch.setattr(
        repo_lib.Repo,
        "provenance",
        lambda self: repo_lib.Provenance(COMMIT, False),
    )


def scripted_replies(monkeypatch, *answers):
    """Makes a command interactive with scripted answers.

    Returns:
        The prompter, whose `asked` lists the questions.
    """
    prompter = prompts.ScriptedPrompter(list(answers))
    monkeypatch.setattr(common, "stdin_is_tty", lambda: True)
    monkeypatch.setattr(common, "prompter", lambda console=None: prompter)
    return prompter


@dataclasses.dataclass
class Script:
    """A step whose check returns scripted verdicts.

    Attributes:
        verdicts: Statuses or verdicts the check returns in order; the last
            one repeats.
        errors: Exceptions that run raises in order before it succeeds.
        runs: How often run ran.
        checks: How often check ran.
    """

    verdicts: list = dataclasses.field(default_factory=list)
    errors: list = dataclasses.field(default_factory=list)
    runs: int = 0
    checks: int = 0

    def check(self, ctx):
        del ctx
        self.checks += 1
        found = (
            self.verdicts.pop(0) if len(self.verdicts) > 1 else self.verdicts[0]
        )
        if isinstance(found, model.Verdict):
            return found
        return model.Verdict(found, f"check says {found}", remedy="fix it")

    def run(self, ctx):
        del ctx
        self.runs += 1
        if self.errors:
            raise self.errors.pop(0)

    def step(
        self,
        step_id="t.step",
        *,
        kind=model.StepKind.AUTO,
        stage=model.PRE_STAGE,
        runnable=True,
        **fields,
    ):
        """Returns a step that uses this script."""
        return model.Step(
            id=step_id,
            stage=stage,
            kind=kind,
            title=f"Title of {step_id}",
            doc_anchor="docs/ddg.md#prerequisites",
            explain=lambda ctx: f"Explains {step_id}.",
            check=self.check,
            run=self.run if runnable else None,
            **fields,
        )


def completed(stdout="", returncode=0, stderr=""):
    """Returns a CompletedProcess as a runner returns it."""
    return subprocess.CompletedProcess(
        ["terraform"], returncode, stdout, stderr
    )


def _name(address):
    found = _NAME_RE.search(address)
    assert found, address
    return found.group(1)


def change(address, kind, actions, *, before=None, after=None, **fields):
    """Returns one `resource_changes` entry of a plan document.

    Args:
        address: The resource address.
        kind: The resource type.
        actions: The change actions.
        before: The value before.
        after: The value after.
        **fields: `module_address`, or more `change` fields such as
            `importing` and `replace_paths`.
    """
    module_address = fields.pop("module_address", None)
    entry = {
        "address": address,
        "mode": "managed",
        "type": kind,
        "name": _name(address),
        "change": {
            "actions": list(actions),
            "before": before,
            "after": after,
            "after_unknown": fields.pop("after_unknown", {}),
            **fields,
        },
    }
    if module_address:
        entry["module_address"] = module_address
    return entry


def binding(role, members, actions=("create",), before=None):
    """Returns an authoritative organization IAM binding change."""
    return change(
        f"{_BINDINGS}[{json.dumps(role)}]",
        "google_organization_iam_binding",
        actions,
        module_address="module.organization",
        before=before,
        after={
            "role": role,
            "members": list(members),
            "condition": [],
            "org_id": conftest.ORG_ID,
        },
    )


def plan_doc(changes=(), *, applyable=True, bootstrap_user=None, drift=()):
    """Returns a plan document with placeholder variables."""
    doc = {
        "format_version": "1.2",
        "terraform_version": "1.13.3",
        "variables": {
            "bootstrap_user": {"value": bootstrap_user},
            "prefix": {"value": "tst"},
        },
        "resource_changes": list(changes),
        "applyable": applyable,
        "complete": True,
        "errored": False,
    }
    if drift:
        doc["resource_drift"] = list(drift)
    return doc


def script_plan(runner, *docs):
    """Scripts a successful plan and show for each document, in order."""
    for doc in docs:
        runner.results.setdefault("plan", []).append(completed("Plan: ok\n"))
        runner.results.setdefault("show", []).extend(
            [completed(json.dumps(doc)), completed("plan text\n")]
        )


def subcommands(runner):
    """Returns the subcommand of each call a FakeTerraform received."""
    return [runner.subcommand(args) for args, _ in runner.calls]


def calls(runner, subcommand):
    """Returns the arguments of each call of one subcommand."""
    return [args for args, _ in runner.calls if args[0] == subcommand]


def link_workspace(ctx, stage="0"):
    """Links a stage workspace to the engine, as a render does.

    Every init checks the links first. A Stage 1 workspace also gets
    placeholder Stage 0 outputs to link.

    Returns:
        The workspace.
    """
    name = paths.resolve_stage(stage)
    for relative in workspace_lib.OUTPUT_LINKS[name]:
        output = ctx.env.fast_config / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("{}\n")
    workspace_lib.sync(ctx.env, ctx.repo.root, name)
    ctx.invalidate()
    return ctx.env.workspace(name)


def pipeline_ctx(tmp_path, docs, replies=(), **kwargs):
    """Returns a context whose runner plans each document, and the runner.

    The Stage 0 workspace is linked, so `apply.apply_pipeline` can run in
    it.
    """
    runner = kwargs.pop("runner", None) or conftest.FakeTerraform()
    script_plan(runner, *docs)
    ctx = scripted_ctx(tmp_path, replies, runner=runner, **kwargs)
    link_workspace(ctx)
    return ctx, runner


def org_policy(*members, etag=conftest.ETAG):
    """Returns a live organization policy that grants `IAM_ROLE`."""
    return {
        "version": 1,
        "etag": etag,
        "bindings": [{"role": IAM_ROLE, "members": list(members)}],
    }


def folder_change(actions=("create",)):
    """Returns a plan change of a folder outside every guard."""
    return change(
        "google_folder.extra", "google_folder", actions, after={"name": "x"}
    )


def resource(module, kind, name, instances, mode="managed"):
    """Returns one `resources` entry of a state document."""
    entry = {
        "mode": mode,
        "type": kind,
        "name": name,
        "provider": 'provider["registry.terraform.io/hashicorp/google"]',
        "instances": instances,
    }
    if module:
        entry["module"] = module
    return entry


def instance(attributes, index_key=None):
    """Returns one instance of a state resource."""
    found = {"schema_version": 0, "attributes": attributes}
    if index_key is not None:
        found["index_key"] = index_key
    return found


def state_doc(resources=(), *, serial=1, lineage=LINEAGE):
    """Returns a Terraform state document."""
    return {
        "version": 4,
        "terraform_version": "1.13.3",
        "serial": serial,
        "lineage": lineage,
        "outputs": {},
        "resources": list(resources),
    }


def project_state(serial=1, lineage=LINEAGE):
    """Returns a state with one project, so it is not empty."""
    project = resource(
        "module.automation-project",
        "google_project",
        "project",
        [instance({"project_id": "tst-prod-iac-core-0"}, 0)],
    )
    return state_doc([project], serial=serial, lineage=lineage)


def state_bytes(doc):
    """Returns a state document as file bytes."""
    return json.dumps(doc).encode("utf-8")
