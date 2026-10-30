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

"""Records what `stellar deploy` did, so a later run resumes from there.

`run-state.json` in the environment holds the engine that last initialized
the workspaces, the outcome of each step, the state each apply left behind
and every confirmation the operator gave. A missing file means unknown
history: an apply step whose state lineage no record holds answers UNKNOWN
instead of guessing. The `(lineage, serial)` pair of the Stage 0 state is
the resume key, because Terraform keeps the lineage and raises the serial
on every write.

`Lock` keeps two deploys of one environment from running at once. It never
guesses whether a holder still runs: the operator removes a stale lock.
"""

from collections.abc import Iterator, Mapping
import datetime
import json
import os
import pathlib
from typing import Literal

import pydantic

from stellar_engine import fsutil
from stellar_engine import paths

SCHEMA_VERSION = 1
# The `Confirmation.kind` values the deploy records, besides the plan guard
# keys: a person confirmed a manual step, the operator went past a check
# that could not tell, decided the organization IAM review, accepted an
# engine checkout that changed, approved the log bucket state fix, or
# accepted new owners on imported projects outside the IAM review.
MANUAL = "manual"
UNKNOWN = "unknown"
IAM_GATE = "iam_gate"
ENGINE = "engine"
BUCKET_FIX = "bucket_fix"
OWNERS = "owners"
# The `Confirmation.decision` values.
CONFIRMED = "confirmed"
SKIPPED = "skipped"
KEPT = "kept"
CONTINUED = "continued"
RUN = "run"


class RunStateError(Exception):
    """Raised when `run-state.json` cannot be read or has another schema."""


class LockHeldError(Exception):
    """Raised when another deploy holds the environment lock.

    Attributes:
        path: The lock file.
    """

    def __init__(self, message: str, path: pathlib.Path):
        """Initializes the error.

        Args:
            message: Who holds the lock and how to remove a stale one.
            path: The lock file.
        """
        super().__init__(message)
        self.path = path


class _Model(pydantic.BaseModel):
    """Base model that rejects unknown keys, so typos never pass silently."""

    model_config = pydantic.ConfigDict(extra="forbid")


class EngineRecord(_Model):
    """The engine checkout that last initialized the workspaces.

    Attributes:
        path: Absolute path of the checkout; empty before the first init.
        commit: Its git commit, or None outside a git checkout.
        dirty: Whether it had uncommitted changes.
        terraform_version: The Terraform version that ran the init.
    """

    path: str = ""
    commit: str | None = None
    dirty: bool = False
    terraform_version: str = ""


class LastRun(_Model):
    """The latest `stellar deploy` run.

    Attributes:
        command: The command line, such as `deploy --stage 0`.
        principal: The identity of the Application Default Credentials.
        started: When the run started.
        finished: When it ended, or None while it runs.
        exit: Its exit status, or None while it runs.
    """

    command: str
    principal: str = ""
    started: datetime.datetime
    finished: datetime.datetime | None = None
    exit: int | None = None


class Artifacts(_Model):
    """Files of a step's latest plan, relative to the environment.

    Attributes:
        plan: The saved plan that the apply applies.
        plan_json: Its `terraform show -json` document.
        plan_text: Its `terraform show` text.
        log: The log of the latest command.
    """

    plan: str | None = None
    plan_json: str | None = None
    plan_text: str | None = None
    log: str | None = None


class StateRecord(_Model):
    """The Terraform state of a stage after a plan or an apply.

    Attributes:
        lineage: The state lineage, constant over the state's life.
        serial: The state serial, which every write raises.
        remote_generation: The Cloud Storage generation of the remote
            state object, or None while the state is local.
    """

    lineage: str | None = None
    serial: int | None = None
    remote_generation: int | None = None

    def __str__(self) -> str:
        """Returns `serial <serial> lineage <lineage>`, as messages say it."""
        return f"serial {self.serial} lineage {self.lineage}"


class Confirmation(_Model):
    """An answer the operator gave.

    Attributes:
        kind: What was asked: `MANUAL`, `IAM_GATE`, another constant of
            this module, or a plan guard key.
        decision: The answer, such as `CONFIRMED` or `SKIPPED`.
        at: When.
        principal: The identity that ran the deploy.
        detail: What the question covered.
    """

    kind: str
    decision: str
    at: datetime.datetime
    principal: str = ""
    detail: str = ""


class StepRecord(_Model):
    """What run-state knows about one step.

    Attributes:
        status: The latest status, a `model.StepStatus` value, or None.
        principal: The identity that last ran or confirmed the step.
        finished: When the step last ended.
        attempts: Remedy key to the attempts made since the step was last
            done.
        artifacts: The files of the latest plan.
        summary: The latest plan's counts per action.
        findings: The latest plan's findings as `<level> <key> <address>`.
        tfvars_sha256: The hash of the stage inputs at the latest apply.
        engine_sha256: The hash of the engine commit and the provider lock
            file at the latest apply; None when the checkout was dirty.
        state: The state the latest apply, or no-op plan, left behind.
        failed_state: The state that the latest failed apply left behind,
            which may start a lineage, such as a failed first apply of a
            stage does; None once an apply succeeds.
        confirmations: Every answer given for the step, oldest first.
    """

    status: str | None = None
    principal: str = ""
    finished: datetime.datetime | None = None
    attempts: dict[str, int] = pydantic.Field(default_factory=dict)
    artifacts: Artifacts = pydantic.Field(default_factory=Artifacts)
    summary: dict[str, int] = pydantic.Field(default_factory=dict)
    findings: list[str] = pydantic.Field(default_factory=list)
    tfvars_sha256: str | None = None
    engine_sha256: str | None = None
    state: StateRecord | None = None
    failed_state: StateRecord | None = None
    confirmations: list[Confirmation] = pydantic.Field(default_factory=list)

    def confirmed(self, kind: str, decision: str = CONFIRMED) -> bool:
        """Returns whether an answer of a kind was recorded for the step.

        Args:
            kind: The `Confirmation.kind`, such as `MANUAL`.
            decision: The `Confirmation.decision` to look for.
        """
        return any(
            item.kind == kind and item.decision == decision
            for item in self.confirmations
        )


class Migration(_Model):
    """The Stage 0 state migration to the remote backend.

    Attributes:
        backup: The copy of the local state taken before the migration.
        local: The local state that was migrated.
        remote_before: The remote state object before, or None if absent.
        remote_after: The remote state object after.
    """

    backup: str | None = None
    local: StateRecord | None = None
    remote_before: StateRecord | None = None
    remote_after: StateRecord | None = None


class Stage0Record(_Model):
    """Stage 0 facts that outlive one step.

    Attributes:
        final_applied: Whether a final-phase Stage 0 apply succeeded, which
            forbids returning to the bootstrap phase.
        migration: The state migration, once it ran.
    """

    final_applied: bool = False
    migration: Migration | None = None


class SnapshotRecord(_Model):
    """An organization IAM snapshot that a deploy took.

    Attributes:
        path: The policy file.
        etag: The etag of the read.
        taken: When.
        reason: Why, such as `gate` or `grant`.
    """

    path: str
    etag: str = ""
    taken: datetime.datetime
    reason: str


class IamRecord(_Model):
    """The organization IAM snapshots, oldest first."""

    snapshots: list[SnapshotRecord] = pydantic.Field(default_factory=list)


class RunState(_Model):
    """The content of `run-state.json`.

    Attributes:
        schema_version: The file format version.
        prefix: The environment prefix.
        updated: When the file was last saved; None until the first save.
        engine: The engine checkout that last initialized the workspaces.
        last_run: The latest deploy run, or None.
        steps: Step ID to what is known about it.
        stage0: Stage 0 facts that outlive one step.
        iam: The organization IAM snapshots.
    """

    schema_version: Literal[1] = SCHEMA_VERSION
    prefix: str
    updated: datetime.datetime | None = None
    engine: EngineRecord = pydantic.Field(default_factory=EngineRecord)
    last_run: LastRun | None = None
    steps: dict[str, StepRecord] = pydantic.Field(default_factory=dict)
    stage0: Stage0Record = pydantic.Field(default_factory=Stage0Record)
    iam: IamRecord = pydantic.Field(default_factory=IamRecord)

    def step(self, step_id: str) -> StepRecord:
        """Returns the record of a step, adding an empty one if missing.

        Args:
            step_id: The step ID, such as `s0.apply_final`.
        """
        return self.steps.setdefault(step_id, StepRecord())

    def confirmed(
        self, step_id: str, kind: str, decision: str = CONFIRMED
    ) -> bool:
        """Returns whether an answer was recorded for a step; see `StepRecord`.

        Args:
            step_id: The step ID; a step without a record has no answers.
            kind: The `Confirmation.kind`, such as `MANUAL`.
            decision: The `Confirmation.decision` to look for.
        """
        record = self.steps.get(step_id)
        return record is not None and record.confirmed(kind, decision)

    def confirmations(self, kind: str) -> Iterator[tuple[str, Confirmation]]:
        """Yields the step ID and each recorded answer of a kind.

        Args:
            kind: The `Confirmation.kind`, such as `IAM_GATE`.
        """
        for step_id, record in self.steps.items():
            for item in record.confirmations:
                if item.kind == kind:
                    yield step_id, item


def load(env: paths.EnvPaths) -> RunState:
    """Reads an environment's run-state.

    Args:
        env: The environment.

    Returns:
        The run-state, or an empty one when the file does not exist.

    Raises:
        RunStateError: If the file cannot be parsed, has another schema
            version, or does not match the model.
    """
    text = fsutil.read_text_or_none(env.run_state)
    if text is None:
        return RunState(prefix=env.prefix)
    try:
        data = json.loads(text)
    except ValueError as error:
        raise RunStateError(
            f"Cannot read {env.run_state}: {error}. Move it away to start "
            "without history."
        ) from error
    version = data.get("schema_version") if isinstance(data, dict) else None
    if version != SCHEMA_VERSION:
        raise RunStateError(
            f"{env.run_state} has schema_version {version}, which this "
            "stellar does not read. Use the stellar version that wrote it, "
            "or move the file away to start without history."
        )
    try:
        return RunState.model_validate(data)
    except pydantic.ValidationError as error:
        raise RunStateError(
            f"{env.run_state} is invalid: {error}. Move it away to start "
            "without history."
        ) from error


def save(env: paths.EnvPaths, state: RunState, now: datetime.datetime) -> None:
    """Writes an environment's run-state with mode 0600.

    Args:
        env: The environment.
        state: The run-state; its `updated` becomes `now`.
        now: The current time.
    """
    state.updated = now
    text = state.model_dump_json(indent=2, exclude_none=True)
    fsutil.write_private(env.run_state, f"{text}\n")


def lock_holder(env: paths.EnvPaths) -> dict[str, str] | None:
    """Returns what the lock file says about its holder, or None.

    Args:
        env: The environment.

    Returns:
        The `command` and `started` the holder wrote, or None without a
        lock. A lock that cannot be parsed returns an empty mapping.
    """
    text = fsutil.read_text_or_none(env.deploy_lock)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {key: str(value) for key, value in data.items()}


def describe_holder(holder: Mapping[str, str]) -> str:
    """Returns who holds the deploy lock, as `<command> since <time>`.

    Args:
        holder: What `lock_holder` returned; missing keys read as unknown.
    """
    command = holder.get("command", "an unknown command")
    return f"{command} since {holder.get('started', 'an unknown time')}"


class Lock:
    """Holds the environment's deploy lock for the length of a deploy.

    The lock file is created with `O_CREAT | O_EXCL`, so only one process
    creates it, and mode 0600. It holds the command and start time, which
    a refused deploy and `stellar status` print.
    """

    def __init__(
        self, env: paths.EnvPaths, command: str, now: datetime.datetime
    ):
        """Initializes the lock without taking it.

        Args:
            env: The environment to lock.
            command: The command line that takes the lock.
            now: The current time.
        """
        self.env = env
        self.path = env.deploy_lock
        self._content = json.dumps(
            {"command": command, "started": now.isoformat()}
        )

    def acquire(self) -> None:
        """Takes the lock.

        Raises:
            LockHeldError: If the lock file exists.
        """
        paths.make_private_dir(self.path.parent)
        try:
            descriptor = os.open(
                self.path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                fsutil.PRIVATE_FILE_MODE,
            )
        except FileExistsError:
            holder = describe_holder(lock_holder(self.env) or {})
            raise LockHeldError(
                f"Another deploy holds {self.path}: {holder}. Delete "
                f"{self.path} if no deploy is running.",
                self.path,
            ) from None
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(f"{self._content}\n")

    def release(self) -> None:
        """Removes the lock file, unless another deploy's lock replaced it.

        An operator may delete a stale lock while this deploy runs, and
        another deploy may then take it.
        """
        if fsutil.read_text_or_none(self.path) == f"{self._content}\n":
            self.path.unlink(missing_ok=True)
