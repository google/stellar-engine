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

"""The `stellar guide`, `stellar status` and `stellar deploy` commands.

`guide` explains the deploy steps without reading Google Cloud. `status`
runs the check of every step and writes nothing. `deploy` runs the steps
under the environment lock and records each outcome in run-state, so a
rerun resumes where the last one stopped. The deploy library raises typed
errors; `exit_code` maps their classes to the exit statuses of `common`.
"""

import dataclasses
import json
import os
from typing import Annotated, Any, cast

from rich import console as rich_console
from rich import padding
from rich import text as rich_text
import typer

from stellar_engine import paths
from stellar_engine import tools as tools_lib
from stellar_engine.commands import common
from stellar_engine.config import models
from stellar_engine.deploy import catalog as catalog_lib
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import api
from stellar_engine.gcp import live
from stellar_engine.preflight import report
from stellar_engine.preflight import result
from stellar_engine.terraform import runner as runner_lib

Status = model.StepStatus
StageOption = Annotated[
    list[str] | None,
    typer.Option(
        "--stage",
        help=(
            "Only the steps of this stage: pre, 0 or 1, or a stage name "
            "such as 1-resman. Repeatable."
        ),
    ),
]
OnlyOption = Annotated[
    list[str] | None,
    typer.Option(
        "--only",
        help="Only this step, such as s0.apply_final. Repeatable.",
    ),
]
_INDENT = (0, 0, 0, 4)
_FINISHED = (Status.DONE, Status.NOT_APPLICABLE)
# What follows a finished stage.
_NEXT = {
    model.PRE_STAGE: "Prerequisites complete. Next: stellar deploy --stage 0",
    "0": "Stage 0 complete. Next: stellar deploy --stage 1",
    "1": (
        "Stage 1 complete. Next: the DDG Stage 2 section, which stellar "
        "does not run yet."
    ),
}


class _OfflineCloud:
    """Refuses every Google Cloud call, so `stellar guide` stays offline."""

    def __getattr__(self, name: str) -> Any:
        """Returns a method that raises `api.CloudError` when called."""

        def refuse(*args: Any, **kwargs: Any) -> Any:
            """Refuses the call."""
            del args, kwargs  # The call never reaches Google Cloud.
            raise api.CloudError(f"stellar guide does not call {name}.")

        return refuse


def _context(
    session: common.Session,
    env: paths.EnvPaths,
    answers: models.Answers,
    *,
    console: rich_console.Console,
    cloud: model.Cloud,
    run_state: run_state_lib.RunState,
    yes: bool = False,
    interactive: bool = False,
) -> model.Context:
    """Builds the deploy context from the command's factories."""
    return model.Context(
        env=env,
        home=session.home.root,
        repo=session.repo,
        answers=answers,
        cloud=cloud,
        tools=tools_lib.SystemTools(),
        terraform=runner_lib.Terraform(
            runner_lib.SystemRunner(console),
            os.environ,
            env.logs,
            common.now,
        ),
        prompter=common.prompter(console),
        console=console,
        now=common.now,
        environ=os.environ,
        run_state=run_state,
        yes=yes,
        interactive=interactive,
    )


def _select(
    stage: list[str] | None,
    only: list[str] | None = None,
    from_step: str | None = None,
) -> list[model.Step]:
    """Returns the selected steps in catalog order, or exits 2."""
    with common.ExitOn(ValueError):
        return engine.select(
            catalog_lib.catalog(),
            stages=stage or (),
            only=only or (),
            from_step=from_step,
        )


def _flags(
    stage: list[str] | None,
    only: list[str] | None,
    from_step: str | None = None,
) -> list[str]:
    """Returns the selection flags as a command line repeats them."""
    flags = [arg for name in stage or () for arg in ("--stage", name)]
    flags += [arg for name in only or () for arg in ("--only", name)]
    if from_step:
        flags += ["--from-step", from_step]
    return flags


def guide(
    stage: StageOption = None,
    only: OnlyOption = None,
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Explain the deploy steps, offline, with the manual commands.

    The guide lists each step with what it does and the DDG commands that
    do the same by hand. It reads no Google Cloud data and writes nothing.
    """
    session = common.session(home, repo)
    env, answers = common.load_env(session, prefix, check_repo=False)
    steps = _select(stage, only)
    console = common.console()
    ctx = _context(
        session,
        env,
        answers,
        console=console,
        cloud=cast(model.Cloud, _OfflineCloud()),
        run_state=run_state_lib.RunState(prefix=env.prefix),
    )
    for name, title in catalog_lib.STAGE_TITLES.items():
        group = [step for step in steps if step.stage == name]
        if group:
            _print_guide_stage(ctx, title, group)
    next_command = " ".join(["stellar deploy", *_flags(stage, only)])
    console.print(rich_text.Text(f"Next: {next_command}"))


def _print_guide_stage(
    ctx: model.Context, title: str, steps: list[model.Step]
) -> None:
    """Prints the numbered steps of one stage with their explanations."""
    ctx.console.print(rich_text.Text(title, style="bold"))
    for number, step in enumerate(steps, start=1):
        ctx.say(f"{number:>2}. {step.id}  {step.kind}  {step.title}")
        # One paragraph per line, so a console card keeps its own lines.
        lines = step.explain(ctx).splitlines()
        note = _applicability(ctx, step)
        if note:
            lines.append(note)
        for line in lines:
            ctx.console.print(
                padding.Padding(rich_text.Text(line), _INDENT, expand=False)
            )
    ctx.console.print()


def _applicability(ctx: model.Context, step: model.Step) -> str | None:
    """Says whether a conditional step applies, as far as files show."""
    when = step.when
    if when is None:
        return None
    try:
        applies = step.applies_when(ctx)
    except api.CLOUD_ERRORS:
        return f"Applies when {when}."
    if applies:
        return f"Applies here: {when}."
    return f"Not applicable here: it applies only when {when}."


@dataclasses.dataclass(frozen=True)
class _Row:
    """The status of one step."""

    step: model.Step
    verdict: model.Verdict

    def to_result(self) -> result.CheckResult:
        """Returns the row as a preflight result whose title names its stage."""
        title = catalog_lib.STAGE_TITLES[self.step.stage]
        return self.verdict.to_result(self.step, title)


def _status_row(ctx: model.Context, step: model.Step) -> _Row:
    """Checks one step; a step that does not apply says when it would."""
    if not engine.applies(ctx, step):
        when = step.when
        detail = f"Applies only when {when}." if when else "Not needed."
        return _Row(step, model.Verdict(Status.NOT_APPLICABLE, detail))
    return _Row(step, engine.check(ctx, step))


def status(
    stage: StageOption = None,
    output_json: Annotated[
        bool, typer.Option("--json", help="Print the status as JSON.")
    ] = False,
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Show how far the deployment got, without changing anything.

    The command runs the check of every step against the files, run-state
    and Google Cloud, takes no lock and writes nothing. The steps print as
    the preflight report does, with a done step as PASS, a step that cannot
    tell as MANUAL and a step that is not applicable as SKIP. It exits with
    status 4 while a step is not done.
    """
    session = common.session(home, repo)
    env, answers = common.load_env(session, prefix)
    with common.ExitOn(run_state_lib.RunStateError, code=common.EXIT_FAILED):
        state = run_state_lib.load(env)
    steps = _select(stage)
    console = common.console()
    ctx = _context(
        session,
        env,
        answers,
        console=console,
        cloud=live.LiveCloudApi(),
        run_state=state,
    )
    rows = [_status_row(ctx, step) for step in steps]
    header = _header(ctx, rows)
    results = [row.to_result() for row in rows]
    if output_json:
        typer.echo(_status_json(env.prefix, header, results))
    else:
        for _, label, value in header:
            console.print(rich_text.Text(f"{label}: {value}"))
        report.render_table(console, results)
    finished = all(row.verdict.status in _FINISHED for row in rows)
    raise typer.Exit(0 if finished else common.EXIT_STOPPED)


def _status_json(
    prefix: str,
    header: list[tuple[str, str, str]],
    results: list[result.CheckResult],
) -> str:
    """Returns the status as JSON: the header and the preflight rows."""
    document = {
        "prefix": prefix,
        "header": {key: value for key, _, value in header},
        "summary": report.summary(results),
        "steps": [item.to_dict() for item in results],
    }
    return json.dumps(document, indent=2)


def _state_text(summary: probe_lib.StateSummary | None) -> str:
    """Describes a state file for the status header."""
    if summary is None:
        return "absent"
    if summary.empty:
        return "empty"
    if not summary.parsed:
        return f"{summary.size} bytes that are no state"
    return f"{summary.record()}, {len(summary.addresses)} resources"


def _remote_text(remote: probe_lib.RemoteState) -> str:
    """Describes the remote Stage 0 state for the status header."""
    if not remote.readable:
        return f"unreadable: {remote.error}"
    if not remote.exists:
        return "absent"
    return f"{_state_text(remote.summary)}, generation {remote.generation}"


def _backend_text(probe: probe_lib.Probe) -> str:
    """Describes the backend that the last Stage 0 init configured."""
    cached = probe.cached
    if cached is None:
        return "not initialized"
    if not cached.type:
        return "local"
    return f"{cached.type} gs://{cached.bucket}"


def _engine_text(ctx: model.Context) -> str:
    """Describes the current engine checkout and the recorded one."""
    recorded = ctx.run_state.engine
    current = ctx.repo.provenance()
    now = f"{ctx.repo.root} at {current.commit if current else 'no commit'}"
    if current and current.dirty:
        now += " with uncommitted changes"
    if not recorded.path:
        return f"current {now}; none recorded"
    return (
        f"current {now}; recorded {recorded.path} at "
        f"{recorded.commit or 'no commit'}"
    )


def _last_run_text(ctx: model.Context) -> str:
    """Describes the latest deploy run that run-state records."""
    last = ctx.run_state.last_run
    if last is None:
        return "none"
    ended = "still running" if last.exit is None else f"exit {last.exit}"
    return (
        f"{last.command} by {last.principal}, started "
        f"{last.started.isoformat()}, {ended}"
    )


def _last_plan_text(ctx: model.Context) -> str:
    """Describes the newest saved plan, its counts and its findings."""
    planned = [
        (record.finished, step_id, record)
        for step_id, record in ctx.run_state.steps.items()
        if record.artifacts.plan and record.finished is not None
    ]
    if not planned:
        return "none"
    _, step_id, record = max(planned, key=lambda item: item[0])
    counts = ", ".join(
        f"{count} {action}"
        for action, count in record.summary.items()
        if count and action != "no-op"
    )
    findings = "; ".join(record.findings) or "no findings"
    return (
        f"{step_id} {record.artifacts.plan}: {counts or 'no changes'}; "
        f"{findings}"
    )


def _iam_review_text(ctx: model.Context) -> str:
    """Describes the newest organization IAM review decision."""
    reviews = [
        (item.at, step_id, item)
        for step_id, item in ctx.run_state.confirmations(run_state_lib.IAM_GATE)
    ]
    if not reviews:
        return "none"
    at, step_id, item = max(reviews, key=lambda review: review[0])
    return f"{item.decision} for {step_id} at {at.isoformat()}: {item.detail}"


def _lock_text(ctx: model.Context) -> str:
    """Describes who holds the deploy lock, if anyone."""
    holder = run_state_lib.lock_holder(ctx.env)
    if holder is None:
        return "free"
    return f"held by {run_state_lib.describe_holder(holder)}"


def _accounts_text(ctx: model.Context) -> str:
    """Describes whether the stage service accounts are enabled."""
    found = cloud_ops.service_accounts_enabled(ctx)
    if found.enabled is None:
        return f"unknown: {found.error}"
    if found.enabled:
        return "enabled"
    return f"disabled: {', '.join(found.disabled)}"


def _header(ctx: model.Context, rows: list[_Row]) -> list[tuple[str, str, str]]:
    """Returns the key, label and value of each status header line."""
    probe = ctx.stage0()
    manual = [
        row.step.id
        for row in rows
        if row.step.kind == model.StepKind.MANUAL
        and row.verdict.status not in _FINISHED
    ]
    return [
        ("environment", "Environment", f"{ctx.env.prefix} in {ctx.env.root}"),
        ("phase", "Stage 0 phase", ctx.answers.stage0_phase),
        ("backend", "Stage 0 backend", _backend_text(probe)),
        ("local_state", "Local state", _state_text(probe.local)),
        ("local_backup", "Local backup", _state_text(probe.backup)),
        ("remote_state", "Remote state", _remote_text(probe.remote)),
        ("engine", "Engine", _engine_text(ctx)),
        ("last_run", "Last run", _last_run_text(ctx)),
        ("last_plan", "Last plan", _last_plan_text(ctx)),
        ("iam_review", "IAM review", _iam_review_text(ctx)),
        ("manual", "Pending manual steps", ", ".join(manual) or "none"),
        ("lock", "Lock", _lock_text(ctx)),
        ("service_accounts", "Stage service accounts", _accounts_text(ctx)),
    ]


def deploy(
    stage: StageOption = None,
    only: OnlyOption = None,
    from_step: Annotated[
        str | None,
        typer.Option(
            "--from-step",
            help="Skip the selected steps before this one.",
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            help=(
                "Answer the routine questions without asking: apply a "
                "reviewed plan, grant the missing organization roles and "
                "allow the BigQuery services. Manual steps, plan findings "
                "and the organization IAM review still ask."
            ),
        ),
    ] = False,
    non_interactive: Annotated[
        bool,
        common.non_interactive_option(
            "Never prompt; stop with exit status 4 where a question waits."
        ),
    ] = False,
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Run the deploy steps, resuming where the last run stopped.

    Each step checks whether it is done first, so a rerun skips finished
    work. Every apply plans to a file, shows the summary and the findings,
    reviews organization IAM changes and applies the saved plan.
    """
    session = common.session(home, repo)
    env, _ = common.load_env(session, prefix)
    steps = _select(stage, only, from_step)
    command = " ".join(["deploy", *_flags(stage, only, from_step)])
    lock = run_state_lib.Lock(env, command, common.now())
    with common.ExitOn(run_state_lib.LockHeldError, code=common.EXIT_STOPPED):
        lock.acquire()
    try:
        # The answers and run-state are read under the lock, so a deploy
        # that just finished cannot be overwritten with stale copies.
        answers = common.load_answers(env, session.repo)
        with common.ExitOn(
            run_state_lib.RunStateError, code=common.EXIT_FAILED
        ):
            state = run_state_lib.load(env)
        console = common.console()
        ctx = _context(
            session,
            env,
            answers,
            console=console,
            cloud=live.LiveCloudApi(),
            run_state=state,
            yes=yes,
            interactive=common.interactive(non_interactive),
        )
        _print_engine(ctx)
        outcome = engine.run(
            ctx, steps, catalog=catalog_lib.catalog(), command=command
        )
        code = exit_code(outcome)
        engine.finish_run(ctx, code)
    finally:
        lock.release()
    _print_outcome(ctx, steps, outcome, partial=bool(only))
    raise typer.Exit(code)


def exit_code(outcome: engine.Report) -> int:
    """Returns the exit status of a deploy run.

    A failed step exits with `common.EXIT_FAILED`. Every other stop, from a
    manual step to a declined question, waits for the operator and exits
    with `common.EXIT_STOPPED`.

    Args:
        outcome: How the run ended.
    """
    if outcome.stop is None:
        return 0
    if isinstance(outcome.stop, model.FailedError):
        return common.EXIT_FAILED
    return common.EXIT_STOPPED


def _print_engine(ctx: model.Context) -> None:
    """Prints the commit of the engine checkout that the deploy uses."""
    provenance = ctx.repo.provenance()
    if provenance is None:
        ctx.say(f"engine {ctx.repo.root}")
        return
    ctx.say(f"engine {provenance.commit}{' dirty' if provenance.dirty else ''}")


def _print_outcome(
    ctx: model.Context,
    steps: list[model.Step],
    outcome: engine.Report,
    *,
    partial: bool,
) -> None:
    """Prints where the deploy ended and what comes next.

    Args:
        ctx: The deploy context.
        steps: The selected steps.
        outcome: How the run ended.
        partial: Whether `--only` picked single steps, which finish no
            stage.
    """
    if outcome.stopped_at is None:
        if partial or not steps:
            ctx.say("The selected steps are done. Next: stellar deploy")
        else:
            ctx.say(_NEXT[steps[-1].stage])
        return
    reason = (outcome.reason or "it stopped").rstrip(".")
    # A reason that quotes a question keeps its question mark.
    end = "" if reason.endswith("?") else "."
    ctx.say(
        f"Stopped at {outcome.stopped_at}: {reason}{end} Resume with stellar "
        "deploy."
    )
    if outcome.remedy:
        ctx.say(outcome.remedy)
