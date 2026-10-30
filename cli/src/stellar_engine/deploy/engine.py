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

"""Runs the deploy steps in catalog order until one stops the run.

`run` walks the selected steps in catalog order. A step that is done is
skipped, so a rerun resumes where the last run stopped. An `auto` step
runs, a `manual` step asks the operator to confirm a person did it, and a
`check` step only reports. A prerequisite that is not done stops the run
instead of being skipped. `--yes` answers only the routine questions:
applying a reviewed plan, granting the missing organization roles in
`pre.iam_roles` and allowing the BigQuery services in `s0.allow_bq`; manual
steps, plan findings and the organization IAM review always need the
operator.

When the `run` of a step fails, the engine applies the matching remedy of
the step and runs it again, a bounded number of times per step. The
`Report` holds the error that stopped the run, and the command maps its
class to the exit status. `render` renders a stage workspace for the steps
that need one, and `apply.apply_pipeline` applies Terraform.
"""

from collections.abc import Sequence
import dataclasses
import functools
import pathlib

from stellar_engine import paths
from stellar_engine.config import derive
from stellar_engine.deploy import model
from stellar_engine.deploy import remedies as remedies_lib
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.render import pipeline
from stellar_engine.terraform import runner as runner_lib

Status = model.StepStatus
# The failure output a step without a matching remedy shows.
_FAILURE_TAIL_LINES = 20
_PERMISSIONS = {
    model.Identity.BILLING_LINKER: checks.BILLING_LINK_PERMISSION,
    model.Identity.BILLING_ADMIN: checks.BILLING_ADMIN_PERMISSION,
}
_CAPABILITIES = {
    model.Identity.DEPLOYER: "the deploying identity",
    model.Identity.BILLING_LINKER: (
        f"an identity with {checks.BILLING_LINK_PERMISSION} on the billing "
        f"account, such as a {checks.BILLING_USER}"
    ),
    model.Identity.BILLING_ADMIN: (
        "an identity that can grant roles on the billing account, such as "
        f"a {checks.BILLING_ADMIN}"
    ),
}


@dataclasses.dataclass(frozen=True)
class StepResult:
    """How one step ended in a run.

    Attributes:
        step_id: The step.
        status: Its status.
        detail: What its check or the stop said.
    """

    step_id: str
    status: model.StepStatus
    detail: str


@dataclasses.dataclass(frozen=True)
class Report:
    """How a run ended.

    The engine prints each step as it goes; the command prints the stop,
    its remedy, which holds the handoff card of an identity mismatch, and
    the next command, and maps the class of the stop to the exit status.

    Attributes:
        results: Each step the run reached, in order.
        stopped_at: The step the run stopped at, or None when every
            selected step is done.
        stop: The error that stopped the run, or None.
    """

    results: tuple[StepResult, ...]
    stopped_at: str | None = None
    stop: model.DeployError | None = None

    @property
    def reason(self) -> str | None:
        """Why the run stopped, or None."""
        return self.stop.reason if self.stop else None

    @property
    def remedy(self) -> str | None:
        """What the operator does next, or None."""
        return self.stop.remedy if self.stop else None


def select(
    catalog: Sequence[model.Step],
    *,
    stages: Sequence[str] = (),
    only: Sequence[str] = (),
    from_step: str | None = None,
) -> list[model.Step]:
    """Returns the steps a command works on, in catalog order.

    Args:
        catalog: Every step.
        stages: `--stage` values; empty selects every stage.
        only: `--only` step IDs; empty selects every step of the stages.
        from_step: The `--from-step` ID, which drops the steps before it.

    Raises:
        ValueError: If a stage or step ID is unknown, or `from_step` is not
            among the selected steps.
    """
    known = {step.id for step in catalog}
    unknown = sorted({*only, *([from_step] if from_step else [])} - known)
    if unknown:
        raise ValueError(f"Unknown step {', '.join(unknown)}.")
    wanted = {model.catalog_stage(name) for name in stages}
    steps = [
        step
        for step in catalog
        if (not wanted or step.stage in wanted)
        and (not only or step.id in only)
    ]
    if from_step is not None:
        ids = [step.id for step in steps]
        if from_step not in ids:
            raise ValueError(f"{from_step} is not among the selected steps.")
        steps = steps[ids.index(from_step) :]
    return steps


def run(
    ctx: model.Context,
    steps: Sequence[model.Step],
    *,
    catalog: Sequence[model.Step] = (),
    command: str = "deploy",
) -> Report:
    """Runs steps in order until one stops the run.

    Each outcome goes to run-state as soon as it is known, so a crash
    loses at most the step that was running. The caller records the end
    of the run and its exit status with `finish_run`.

    Args:
        ctx: The deploy context.
        steps: The selected steps, from `select`.
        catalog: Every step, which the `requires` of a selected step may
            name; defaults to the selected steps.
        command: The command line that run-state records.

    Returns:
        How the run ended.
    """
    index = {step.id: step for step in (*catalog, *steps)}
    ctx.run_state.last_run = run_state_lib.LastRun(
        command=command, principal=ctx.principal(), started=ctx.now()
    )
    ctx.save()
    results = []
    for step in steps:
        ctx.say(f"== {step.id} ({step.kind}) {step.title} ==")
        try:
            results.append(_run_step(ctx, step, index))
        except model.DeployError as stop:
            results.append(_finish(ctx, step, stop.status, stop.reason))
            return Report(tuple(results), step.id, stop)
    return Report(tuple(results))


def finish_run(ctx: model.Context, code: int) -> None:
    """Records in run-state that the run ended, with its exit status.

    Args:
        ctx: The deploy context.
        code: The exit status that the command maps the report to.
    """
    last = ctx.run_state.last_run
    if last is not None:
        last.finished = ctx.now()
        last.exit = code
    ctx.save()


def _finish(
    ctx: model.Context, step: model.Step, status: Status, detail: str
) -> StepResult:
    """Records how a step ended and returns its result."""
    record = ctx.record(step.id)
    record.status = status
    record.finished = ctx.now()
    record.principal = ctx.principal()
    if status == Status.DONE:
        record.attempts.clear()
    ctx.save()
    return StepResult(step.id, status, detail)


def applies(ctx: model.Context, step: model.Step) -> bool:
    """Returns whether a step applies to the environment.

    Args:
        ctx: The deploy context.
        step: The step.

    Returns:
        The step's `applies_when`, or True when Google Cloud cannot answer
        it, so that the step's check decides.
    """
    try:
        return step.applies_when(ctx)
    except api.CLOUD_ERRORS:
        return True


def check(ctx: model.Context, step: model.Step) -> model.Verdict:
    """Runs a step's check; a Google Cloud error makes it UNKNOWN.

    Args:
        ctx: The deploy context.
        step: The step.
    """
    try:
        return step.check(ctx)
    except api.CLOUD_ERRORS as error:
        return model.Verdict(Status.UNKNOWN, f"Cannot check: {error}")


def _run_step(
    ctx: model.Context, step: model.Step, index: dict[str, model.Step]
) -> StepResult:
    """Checks one step and runs, asks or stops as its verdict says."""
    if not applies(ctx, step):
        return _finish(
            ctx, step, Status.NOT_APPLICABLE, "Not needed by this deployment."
        )
    _require(ctx, step, index)
    ctx.say(step.explain(ctx))
    verdict = check(ctx, step)
    ctx.say(f"{verdict.status}: {verdict.detail}")
    if verdict.status in (Status.DONE, Status.NOT_APPLICABLE):
        return _finish(ctx, step, verdict.status, verdict.detail)
    if verdict.status == Status.BLOCKED:
        raise model.BlockedError(verdict.detail, remedy=verdict.remedy)
    if verdict.status == Status.FAILED:
        raise model.FailedError(verdict.detail, remedy=verdict.remedy)
    if step.kind == model.StepKind.MANUAL:
        return _manual(ctx, step, verdict)
    if step.kind == model.StepKind.CHECK or step.run is None:
        return _report_only(ctx, step, verdict)
    return _auto(ctx, step, verdict)


def _done(
    ctx: model.Context, step_id: str, index: dict[str, model.Step]
) -> bool:
    """Returns whether a prerequisite is done.

    The prerequisite's check decides, so a stale record never stands in
    for a render that the answers outdated or a billing link that went
    away. A DONE record in run-state counts only when the check cannot
    tell, as a recorded confirmation does in `_manual`.
    """
    record = ctx.run_state.steps.get(step_id)
    recorded = record is not None and record.status == Status.DONE
    required = index.get(step_id)
    if required is None:
        return recorded
    if not applies(ctx, required):
        return True
    status = check(ctx, required).status
    if status == Status.UNKNOWN:
        return recorded
    return status in (Status.DONE, Status.NOT_APPLICABLE)


def _require(
    ctx: model.Context, step: model.Step, index: dict[str, model.Step]
) -> None:
    """Stops before a step whose prerequisites are not done."""
    for required in step.requires:
        if not _done(ctx, required, index):
            raise model.StoppedError(
                f"{step.id} needs {required} first.",
                remedy=f"Run {ctx.deploy_command(required)} first.",
            )


def _manual(
    ctx: model.Context, step: model.Step, verdict: model.Verdict
) -> StepResult:
    """Lets the operator run a manual step, or confirm a person did it.

    A recorded confirmation counts while the check cannot tell. A manual
    step with a `run` runs only when the identity has the capability; a
    pending one hands off otherwise.
    """
    if verdict.status == Status.UNKNOWN and ctx.run_state.confirmed(
        step.id, run_state_lib.MANUAL
    ):
        return _finish(ctx, step, Status.DONE, "A person confirmed it.")
    if step.run is not None:
        if _has_identity(ctx, step):
            if ctx.confirm(f"Run {step.title} now?"):
                return _run_and_check(ctx, step)
        elif verdict.status == Status.PENDING:
            raise _handoff(ctx, step)
    if verdict.remedy:
        ctx.say(verdict.remedy)
    if not ctx.confirm(f"Mark {step.id} done?"):
        raise model.StoppedError(
            f"{step.id} waits for a person: {verdict.detail}",
            remedy=verdict.remedy or f"See {step.doc_anchor}.",
        )
    ctx.confirmed(step.id, run_state_lib.MANUAL, verdict.detail)
    return _finish(ctx, step, Status.DONE, "Confirmed by the operator.")


def _report_only(
    ctx: model.Context, step: model.Step, verdict: model.Verdict
) -> StepResult:
    """Stops at a pending check; asks to go past one that cannot tell."""
    if verdict.status == Status.UNKNOWN and ctx.confirm(
        f"{step.id} cannot tell. Continue anyway?"
    ):
        ctx.confirmed(
            step.id,
            run_state_lib.UNKNOWN,
            verdict.detail,
            run_state_lib.CONTINUED,
        )
        return _finish(ctx, step, Status.UNKNOWN, verdict.detail)
    raise model.StoppedError(
        f"{step.id}: {verdict.detail}",
        remedy=verdict.remedy or f"See {step.doc_anchor}.",
    )


def _auto(
    ctx: model.Context, step: model.Step, verdict: model.Verdict
) -> StepResult:
    """Runs an auto step, after asking when its check cannot tell."""
    if verdict.status == Status.UNKNOWN:
        if not ctx.confirm(f"{step.id} cannot tell. Run {step.title} anyway?"):
            raise model.StoppedError(
                f"{step.id}: {verdict.detail}", remedy=verdict.remedy
            )
        ctx.confirmed(
            step.id, run_state_lib.UNKNOWN, verdict.detail, run_state_lib.RUN
        )
    if not _has_identity(ctx, step):
        raise _handoff(ctx, step)
    return _run_and_check(ctx, step)


def _run_and_check(ctx: model.Context, step: model.Step) -> StepResult:
    """Runs a step with its remedies, then requires its check to pass."""
    _attempt(ctx, step)
    ctx.invalidate()
    verdict = check(ctx, step)
    if verdict.status != Status.DONE:
        raise model.FailedError(
            f"{step.id} ran, but its check says {verdict.status}: "
            f"{verdict.detail}",
            remedy=verdict.remedy,
        )
    ctx.say(f"{verdict.status}: {verdict.detail}")
    return _finish(ctx, step, Status.DONE, verdict.detail)


def _identity(ctx: model.Context, step: model.Step) -> model.Identity:
    """Returns the identity a step needs; the deployer when unknown."""
    try:
        return step.identity(ctx)
    except api.CLOUD_ERRORS:
        return model.Identity.DEPLOYER


def _has_identity(ctx: model.Context, step: model.Step) -> bool:
    """Tests the capability a step needs on the billing account."""
    permission = _PERMISSIONS.get(_identity(ctx, step))
    if permission is None:
        return True
    account = ctx.answers.billing.account_id
    try:
        granted = ctx.cloud.granted_billing_permissions(account, [permission])
    except api.CLOUD_ERRORS:
        return False
    return permission in granted


def _admins_group(ctx: model.Context) -> str | None:
    """Returns the organization admins group principal, if it is known."""
    try:
        return derive.group_principal(
            ctx.answers, ctx.repo, derive.ORGANIZATION_ADMINS
        )
    except KeyError:
        return None


def _handoff(ctx: model.Context, step: model.Step) -> model.BlockedError:
    """Returns the stop that hands a step to another identity."""
    identity = _identity(ctx, step)
    lines = [
        f"{step.id} needs {_CAPABILITIES[identity]}.",
        f"The current identity is {ctx.principal()}.",
    ]
    group = _admins_group(ctx)
    if group:
        lines.append(
            f"Members of {group} may impersonate the stage service accounts."
        )
    lines += [
        "Sign in as an identity that has it, then resume:",
        "  gcloud auth application-default login",
        f"  {ctx.deploy_command(step.id)}",
    ]
    if step.kind == model.StepKind.AUTO and step.stage != model.PRE_STAGE:
        commands = runner_lib.manual_apply(
            ctx.workspace(step.stage), ctx.env.plans / f"{step.id}.tfplan"
        )
        lines.append("Or run Terraform there by hand:")
        lines += [f"  {command}" for command in commands]
    return model.BlockedError(
        f"{step.id} needs another identity.", remedy="\n".join(lines)
    )


def _attempt(ctx: model.Context, step: model.Step) -> None:
    """Runs a step, applying the matching remedy after each failure."""
    run_step = step.run
    if run_step is None:
        return
    while True:
        try:
            run_step(ctx)
            return
        except model.CommandError as error:
            failure = remedies_lib.Failure(
                step.id,
                step.stage,
                error.command,
                error.output,
                error.plan,
                error.findings,
            )
            log = error.log
        except api.CloudError as error:
            failure = remedies_lib.Failure(
                step.id, step.stage, "google-cloud", _cloud_output(error)
            )
            log = None
        except api.CredentialsError as error:
            raise model.FailedError(
                f"{step.id}: {error}",
                remedy="Run gcloud auth application-default login.",
            ) from error
        _remedy(ctx, step, failure, log)


def _cloud_output(error: api.CloudError) -> str:
    """Returns a Google Cloud error as remedies match it."""
    if isinstance(error, api.ApiDisabledError):
        return (
            f'{error}\nSERVICE_DISABLED "consumer": "projects/'
            f'{error.project}" "service": "{error.service}"'
        )
    return str(error)


def _remedy(
    ctx: model.Context,
    step: model.Step,
    failure: remedies_lib.Failure,
    log: pathlib.Path | None,
) -> None:
    """Applies the remedy of a failure, or ends the step.

    Attempts count per step and remedy key in run-state, until the step
    is done again. An attempt counts once its action ran: a declined or
    impossible prompt leaves the count alone, so the rerun offers the
    remedy again.

    Raises:
        model.FailedError: If no remedy fits, the remedy has no action,
            its attempts are used up, or it could not fix the cause.
        model.StoppedError: If the action needs an answer the operator
            declines, or that the deploy may not ask for.
    """
    where = f" See {log}." if log else ""
    remedy = remedies_lib.match(failure, step.remedies)
    if remedy is None:
        raise model.FailedError(
            f"{step.id}: {failure.command} failed.{where}",
            remedy=remedies_lib.tail(failure.output, _FAILURE_TAIL_LINES),
        )
    record = ctx.record(step.id)
    used = record.attempts.get(remedy.key, 0)
    ctx.say(f"Known problem: {remedy.title}.")
    fix = f"{remedy.text} See {remedy.doc}."
    if remedy.action is None or used >= remedy.max_attempts:
        raise model.FailedError(
            f"{step.id}: {remedy.title}.{where}", remedy=fix
        )
    ctx.say(
        f"Remedy {remedy.key}, attempt {used + 1} of {remedy.max_attempts}."
    )
    try:
        fixed = remedy.action(ctx, failure)
    except (model.CommandError, api.CloudError) as error:
        raise model.FailedError(
            f"{step.id}: the remedy {remedy.key} failed: {error}", remedy=fix
        ) from error
    record.attempts[remedy.key] = used + 1
    ctx.save()
    if not fixed:
        raise model.FailedError(
            f"{step.id}: {remedy.title}.{where}", remedy=fix
        )
    seconds = remedy.wait(used)
    if seconds:
        ctx.say(f"Waiting {seconds} seconds before the next attempt.")
        ctx.sleep(seconds)
    ctx.invalidate()


def render(ctx: model.Context, stage: str) -> pipeline.StageRender:
    """Renders a stage workspace from the context's answers.

    It asks before replacing a tfvars file with manual edits, and refuses
    to replace one when the deploy may not prompt.

    Args:
        ctx: The deploy context.
        stage: Catalog stage `0` or `1`.

    Raises:
        model.BlockedError: If the render fails or refuses the tfvars.
    """
    options = pipeline.WriteOptions(
        force=False,
        interactive=ctx.interactive,
        confirm=functools.partial(_confirm_replace, ctx),
        now=ctx.now(),
        warn=functools.partial(_say_prefixed, ctx, "Warning"),
        error=functools.partial(_say_prefixed, ctx, "Error"),
    )
    try:
        rendered = pipeline.render_stage(
            paths.resolve_stage(stage),
            ctx.answers,
            ctx.repo,
            ctx.env,
            ctx.tools,
            options,
        )
    except pipeline.ERRORS as error:
        raise model.BlockedError(
            str(error), remedy="Fix it, then rerun stellar deploy."
        ) from error
    ctx.invalidate()
    if rendered.refused:
        raise model.BlockedError(
            f"The stage {stage} tfvars file has manual edits.",
            remedy=(
                "Move the edits into answers.yaml, or run stellar render "
                "--force to back the file up and replace it."
            ),
        )
    return rendered


def _say_prefixed(ctx: model.Context, label: str, message: str) -> None:
    """Prints a render warning or error with its label."""
    ctx.say(f"{label}: {message}")


def _confirm_replace(
    ctx: model.Context, target: pathlib.Path, changes: str
) -> bool:
    """Shows the changes to an edited tfvars file and asks to replace it."""
    ctx.say(changes)
    return ctx.confirm(pipeline.replace_question(target))
