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

"""The step model that `stellar guide`, `status` and `deploy` share.

A deploy is an ordered catalog of steps. Each step explains itself, checks
whether it is done without changing anything, and, unless a person has to
act, runs. `Context` carries everything a step reads or changes, so the
engine, the catalog and the tests pass one object around.

The contracts: `explain` is pure. `check` reads local files, run-state,
`CloudApi` reads and the Stage 0 probe; it never prompts, writes or runs
Terraform, so `stellar status` never changes anything. `run` changes things
only through `Context.terraform`, the `CloudWriter` calls,
`Context.update_answers`, `pipeline.render_stage` for the workspace, the
Stage 0 workspace providers file and local state, after a backup under
`plans/`, and files under `plans/`, `logs/`, `iam-snapshots/` and
`fast-config/`, and asks only through the `Context` prompt methods, which
stop the deploy when it may not prompt.

The model knows no exit statuses: a step stops the deploy by raising a
`DeployError`, and `commands.deploy` maps each error class to the exit
status that the `stellar_engine.cli` docstring lists.
"""

from collections.abc import Callable, Mapping, Sequence
import dataclasses
import datetime
import enum
import pathlib
import subprocess
import time
from typing import Any, Protocol

from rich import console as rich_console

from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import tools as tools_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.preflight import inputs as inputs_lib
from stellar_engine.preflight import result
from stellar_engine.preflight import runner as preflight_runner
from stellar_engine.terraform import plan as plan_lib
from stellar_engine.terraform import runner as runner_lib
from stellar_engine.wizard import prompts

# The catalog stage of the prerequisites, which have no workspace.
PRE_STAGE = "pre"
# How many entries `named` lists before it counts the rest.
_MAX_NAMED = 5


class StepKind(enum.StrEnum):
    """Who acts on a step."""

    # A person acts; the deploy asks them to confirm it is done.
    MANUAL = "manual"
    # stellar acts through Terraform or Google Cloud.
    AUTO = "auto"
    # Nothing acts; the step only reports.
    CHECK = "check"


class Identity(enum.StrEnum):
    """The capability a step needs from the signed-in identity."""

    # The identity that runs the deploy.
    DEPLOYER = "deployer"
    # An identity that can link projects to the billing account.
    BILLING_LINKER = "billing_linker"
    # An identity that can grant roles on the billing account.
    BILLING_ADMIN = "billing_admin"


class StepStatus(enum.StrEnum):
    """What a check found, or how a step ended."""

    DONE = "done"
    PENDING = "pending"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


# How `stellar status` reports a step status as a preflight status; the
# statuses left out are failures.
_RESULT_STATUS = {
    StepStatus.DONE: result.Status.PASS,
    StepStatus.NOT_APPLICABLE: result.Status.SKIP,
    StepStatus.UNKNOWN: result.Status.MANUAL,
}


class DeployError(Exception):
    """Ends a deploy before every selected step is done.

    Attributes:
        status: The status the engine records for the step.
        reason: Why the deploy stopped.
        remedy: What the operator does next, or None.
    """

    status = StepStatus.PENDING

    def __init__(self, reason: str, *, remedy: str | None = None):
        """Initializes the stop.

        Args:
            reason: Why the deploy stopped.
            remedy: What the operator does next, or None.
        """
        super().__init__(reason)
        self.reason = reason
        self.remedy = remedy


class StoppedError(DeployError):
    """The deploy waits for the operator; a rerun resumes at the step."""


class BlockedError(StoppedError):
    """The step cannot go on until something outside the deploy changes."""

    status = StepStatus.BLOCKED


class InputRequiredError(StoppedError):
    """The step must ask the operator, but the deploy may not prompt."""


class FailedError(DeployError):
    """The step failed, and the operator fixes the cause before a rerun."""

    status = StepStatus.FAILED


class CommandError(Exception):
    """Raised by `run` when a command failed in a way remedies may fix.

    The engine matches the output against the step's remedies.

    Attributes:
        command: What failed, such as `apply` or `plan`.
        output: The output to match, such as the Terraform output.
        plan: The parsed plan of the failed step, or None.
        findings: The keys of the plan guard findings that refused the
            apply, which remedies match by key.
        log: The log of the failed command, or None.
    """

    def __init__(
        self,
        command: str,
        output: str,
        *,
        plan: plan_lib.Plan | None = None,
        findings: Sequence[str] = (),
        log: pathlib.Path | None = None,
    ):
        """Initializes the error.

        Args:
            command: What failed.
            output: The output to match.
            plan: The parsed plan, or None.
            findings: The keys of the guard findings that refused it.
            log: The log of the failed command, or None.
        """
        super().__init__(f"{command} failed")
        self.command = command
        self.output = output
        self.plan = plan
        self.findings = tuple(findings)
        self.log = log


def succeeded(
    completed: subprocess.CompletedProcess[str],
    command: str,
    *,
    log: pathlib.Path | None = None,
    plan: plan_lib.Plan | None = None,
) -> subprocess.CompletedProcess[str]:
    """Returns a completed Terraform command, or raises when it failed.

    Args:
        completed: The completed command.
        command: What it was, such as `apply`.
        log: Its log.
        plan: The parsed plan it applied, if any.

    Raises:
        CommandError: If the exit status is not 0.
    """
    if completed.returncode != 0:
        output = runner_lib.output(completed)
        raise CommandError(command, output, plan=plan, log=log)
    return completed


def named(names: Sequence[str]) -> str:
    """Names the first entries of a list and counts the rest.

    Args:
        names: Such as the workspace links a render would change.
    """
    shown = ", ".join(names[:_MAX_NAMED])
    if len(names) > _MAX_NAMED:
        shown += f", and {len(names) - _MAX_NAMED} more"
    return shown


def command_error(
    error: runner_lib.TerraformError, command: str
) -> CommandError:
    """Converts a failed Terraform read into a `CommandError`.

    Args:
        error: The error of `show`, `show -json` or `state pull`.
        command: What it was.
    """
    return CommandError(command, error.output or str(error), log=error.log)


@dataclasses.dataclass(frozen=True)
class Verdict:
    """What a step's check found.

    Attributes:
        status: The status.
        detail: What the check saw.
        remedy: What the operator does about it, or None.
        doc: Repository-relative link to the matching documentation.
        results: Preflight results behind the verdict, if any.
    """

    status: StepStatus
    detail: str
    remedy: str | None = None
    doc: str | None = None
    results: tuple[result.CheckResult, ...] = ()

    def to_result(self, step: Step, stage_title: str) -> result.CheckResult:
        """Returns the verdict as a preflight result, for `stellar status`.

        DONE is PASS, NOT_APPLICABLE is SKIP, UNKNOWN is MANUAL, and
        PENDING, BLOCKED and FAILED are FAIL with the status name leading
        the detail, so the report keeps the difference. Every step goes
        under `result.Category.DEPLOY`, and its title names its stage.

        Args:
            step: The step the verdict is about.
            stage_title: The title of the step's stage, such as
                `Stage 0 - Bootstrap`.
        """
        status = _RESULT_STATUS.get(self.status, result.Status.FAIL)
        detail = self.detail
        if status == result.Status.FAIL:
            detail = f"{self.status}: {self.detail}"
        return result.CheckResult(
            check_id=step.id,
            category=result.Category.DEPLOY,
            title=f"{step.id}\n{stage_title}: {step.title}",
            status=status,
            detail=detail,
            remedy=self.remedy,
            doc=self.doc or step.doc_anchor,
        )


def always(ctx: Context) -> bool:
    """The default `applies_when`: every step applies."""
    del ctx  # Every deployment needs the step.
    return True


def fixed(identity: Identity) -> Callable[[Context], Identity]:
    """Returns an `identity` callable that always needs one identity.

    Args:
        identity: The identity the step needs.
    """

    def resolve(ctx: Context) -> Identity:
        del ctx  # The identity does not depend on the deployment.
        return identity

    return resolve


def static(text: str) -> Callable[[Context], str]:
    """Returns an `explain` callable for text that no answer changes.

    Args:
        text: What the step does and why.
    """

    def explain(ctx: Context) -> str:
        del ctx  # The text does not depend on the deployment.
        return text

    return explain


# The default `Step.identity`.
_DEPLOYER = fixed(Identity.DEPLOYER)


@dataclasses.dataclass(frozen=True)
class Step:
    """One step of the deploy catalog.

    Attributes:
        id: Stable ID such as `s0.apply_final`, which run-state, `--only`
            and `--from-step` use.
        stage: Catalog stage: `pre`, `0` or `1`.
        kind: Who acts on the step.
        title: Short title.
        doc_anchor: Repository-relative link to the DDG section.
        explain: Returns what the step does and why; pure.
        check: Returns whether the step is done; never changes anything.
        run: Does the step, and its return value is ignored; None when
            only a person can.
        requires: Step IDs that must be done first.
        applies_when: Returns whether the deployment needs the step.
        when: Says when `applies_when` holds, as `guide` and `status` print
            it; None for a step that always applies.
        identity: Returns the identity the step needs.
        remedies: Remedy keys that may fix a failure of `run`.
    """

    id: str
    stage: str
    kind: StepKind
    title: str
    doc_anchor: str
    explain: Callable[[Context], str]
    check: Callable[[Context], Verdict]
    run: Callable[[Context], object] | None = None
    requires: tuple[str, ...] = ()
    applies_when: Callable[[Context], bool] = always
    when: str | None = None
    identity: Callable[[Context], Identity] = _DEPLOYER
    remedies: tuple[str, ...] = ()


def catalog_stage(name: str) -> str:
    """Returns the catalog stage of a `--stage` value.

    Args:
        name: `pre`, a stage alias such as `0`, or a stage name such as
            `1-resman`.

    Raises:
        ValueError: If the name is no stage.
    """
    if name == PRE_STAGE:
        return PRE_STAGE
    return paths.stage_alias(name)


class Cloud(api.CloudApi, api.CloudWriter, Protocol):
    """The Google Cloud reads and writes of a deploy."""


@dataclasses.dataclass(frozen=True)
class Preflight:
    """The preflight results that the step checks share.

    Attributes:
        results: Every result, in report order.
        billing_access: Whether the deployer holds the billing permissions
            Stage 0 needs, as preflight found; None when untested.
    """

    results: tuple[result.CheckResult, ...]
    billing_access: bool | None

    def rows(self, prefix: str) -> list[result.CheckResult]:
        """Returns the results whose check ID starts with a prefix.

        Args:
            prefix: Such as `iam.` or `billing.`.
        """
        return [row for row in self.results if row.check_id.startswith(prefix)]


@dataclasses.dataclass
class Context:
    """Everything a step reads or changes.

    Attributes:
        env: The environment.
        home: The home folder, which answers must not point into.
        repo: The engine checkout.
        answers: The environment answers; a step that changes them
            assigns the updated answers here.
        cloud: Google Cloud reads and writes.
        tools: Local tool probes.
        terraform: Runs Terraform.
        prompter: Asks the operator; use the prompt methods instead.
        console: Prints the deploy output.
        now: Returns the current time.
        environ: The process environment.
        run_state: The run-state, saved through `save`.
        yes: Answers the routine confirmations: applying a reviewed plan,
            granting the missing organization roles in `pre.iam_roles`
            and allowing the BigQuery services in `s0.allow_bq`; never a
            manual step, a plan finding or the IAM review.
        interactive: Whether the deploy may prompt.
        sleep: Waits; tests replace it.
    """

    env: paths.EnvPaths
    home: pathlib.Path
    repo: repo_lib.Repo
    answers: models.Answers
    cloud: Cloud
    tools: tools_lib.LocalTools
    terraform: runner_lib.Terraform
    prompter: prompts.Prompter
    console: rich_console.Console
    now: Callable[[], datetime.datetime]
    environ: Mapping[str, str]
    run_state: run_state_lib.RunState
    yes: bool = False
    interactive: bool = True
    sleep: Callable[[float], Any] = time.sleep
    _preflight: Preflight | None = dataclasses.field(
        default=None, init=False, repr=False
    )
    _probe: probe_lib.Probe | None = dataclasses.field(
        default=None, init=False, repr=False
    )
    _principal: str | None = dataclasses.field(
        default=None, init=False, repr=False
    )
    # Questions answered in this run that later steps do not ask again.
    answered: set[str] = dataclasses.field(
        default_factory=set, init=False, repr=False
    )

    def preflight(self) -> Preflight:
        """Runs every preflight check once, from the answers.

        The checks run in report order, because later checks read what
        earlier ones resolved. `invalidate` clears the cached results.
        """
        if self._preflight is None:
            values = answers_lib.to_preflight(self.answers)
            context = checks.Context(
                inputs=inputs_lib.resolve({}, None, values),
                cloud=self.cloud,
                tools=self.tools,
                repo=self.repo,
                environ=self.environ,
            )
            found = preflight_runner.run(context, checks.ALL_CHECKS)
            self._preflight = Preflight(tuple(found), context.billing_access)
        return self._preflight

    def stage0(self) -> probe_lib.Probe:
        """Returns the Stage 0 probe, read once until `invalidate`."""
        if self._probe is None:
            self._probe = probe_lib.probe(self)
        return self._probe

    def invalidate(self) -> None:
        """Forgets the cached preflight results and probe.

        The engine calls it after every step that may have changed them.
        """
        self._preflight = None
        self._probe = None

    def principal(self) -> str:
        """Returns the identity of the credentials, read once."""
        if self._principal is None:
            try:
                email = self.cloud.adc_principal().email
            except api.CLOUD_ERRORS:
                email = None
            self._principal = email or "unknown"
        return self._principal

    def workspace(self, stage: str) -> pathlib.Path:
        """Returns the workspace of a catalog stage.

        Args:
            stage: Catalog stage `0` or `1`.

        Raises:
            ValueError: If the stage has no workspace.
        """
        return self.env.workspace(paths.resolve_stage(stage))

    def relative(self, path: pathlib.Path | None) -> str | None:
        """Returns a path as run-state records it: relative to the env.

        Args:
            path: A file, usually under `plans/`, `logs/` or
                `iam-snapshots/`; a path outside the environment stays
                absolute.
        """
        if path is None:
            return None
        path = pathlib.Path(path)
        if path.is_relative_to(self.env.root):
            return str(path.relative_to(self.env.root))
        return str(path)

    def deploy_command(self, step_id: str) -> str:
        """Returns the command line that runs one step of this deployment.

        Args:
            step_id: The step, such as `s0.apply_bootstrap`.
        """
        return f"stellar deploy --only {step_id} --prefix {self.answers.prefix}"

    def say(self, text: str) -> None:
        """Prints text as is; resource addresses are not Rich markup."""
        self.console.print(text, markup=False, highlight=False)

    def _ask(self, question: str) -> None:
        """Stops the deploy when it may not ask a question."""
        if not self.interactive:
            raise InputRequiredError(
                f"The deploy needs an answer: {question}",
                remedy="Run stellar deploy in a terminal to answer it.",
            )

    def confirm(self, question: str, *, routine: bool = False) -> bool:
        """Asks a yes or no question whose default is no.

        Args:
            question: The question.
            routine: Whether `--yes` answers it, as for applying a plan
                whose findings all passed.

        Returns:
            The answer.

        Raises:
            InputRequiredError: If the deploy may not prompt and `--yes` does
                not answer the question.
        """
        if routine and self.yes:
            return True
        self._ask(question)
        return self.prompter.confirm(question, default=False)

    def select(self, question: str, choices: list[str]) -> str:
        """Asks for one of the choices, which `--yes` never answers.

        Raises:
            InputRequiredError: If the deploy may not prompt.
        """
        self._ask(question)
        return self.prompter.select(question, choices)

    def text(
        self, question: str, validate: prompts.Validator | None = None
    ) -> str:
        """Asks for text, which `--yes` never answers.

        Raises:
            InputRequiredError: If the deploy may not prompt.
        """
        self._ask(question)
        return self.prompter.text(question, validate=validate)

    def typed_confirm(self, question: str, expected: str) -> bool:
        """Asks the operator to type a phrase; see `prompts.typed_confirm`.

        Raises:
            InputRequiredError: If the deploy may not prompt.
        """
        self._ask(question)
        return prompts.typed_confirm(self.prompter, question, expected)

    def record(self, step_id: str) -> run_state_lib.StepRecord:
        """Returns the run-state record of a step, adding it if missing."""
        return self.run_state.step(step_id)

    def confirmed(
        self,
        step_id: str,
        kind: str,
        detail: str,
        decision: str = run_state_lib.CONFIRMED,
    ) -> None:
        """Records an answer the operator gave for a step.

        Args:
            step_id: The step.
            kind: What was asked, such as `run_state.MANUAL` or a guard key.
            detail: What the question covered.
            decision: The answer, such as `run_state.CONFIRMED` or
                `run_state.SKIPPED`.
        """
        self.record(step_id).confirmations.append(
            run_state_lib.Confirmation(
                kind=kind,
                decision=decision,
                at=self.now(),
                principal=self.principal(),
                detail=detail,
            )
        )

    def save(self) -> None:
        """Saves the run-state."""
        run_state_lib.save(self.env, self.run_state, self.now())

    def require_terraform_env(self) -> None:
        """Stops before Terraform runs in an environment with a problem.

        `terraform.env.build_env` reports a problem when Terraform would
        use other credentials than gcloud and preflight, so every step
        that runs Terraform checks it, not only `s0.ready`, which `--only`
        and `--from-step` can skip.

        Raises:
            BlockedError: If the Terraform environment has a problem.
        """
        problems = self.terraform.child_env.problems
        if problems:
            raise BlockedError(
                " ".join(problems),
                remedy="Fix the environment, then rerun stellar deploy.",
            )

    def update_answers(
        self, change: Callable[[dict[str, Any]], object], *, source: str
    ) -> answers_lib.Update:
        """Changes the answers file through `answers.update` and adopts it.

        The update refuses a return to the bootstrap phase once run-state
        records a final Stage 0 apply. The cached preflight results and
        probe read the answers, so they are forgotten.

        Args:
            change: Mutates the answer data in place, as `answers.update`
                passes it.
            source: What makes the change, for the error messages, such as
                `stellar deploy s0.phase_final`.

        Returns:
            The answers before and after, and whether the file changed.

        Raises:
            BlockedError: If the changed answers are invalid or the change
                is forbidden.
        """
        try:
            outcome = answers_lib.update(
                self.env.answers,
                change,
                repo=self.repo,
                home=self.home,
                source=source,
                final_applied=self.run_state.stage0.final_applied,
            )
        except answers_lib.AnswersError as error:
            raise BlockedError(
                str(error),
                remedy="Fix answers.yaml, then rerun stellar deploy.",
            ) from error
        self.answers = outcome.updated
        self.invalidate()
        return outcome
