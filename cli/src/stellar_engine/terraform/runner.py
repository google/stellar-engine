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

"""Runs the Terraform binary with a scrubbed environment and a log file.

Every command runs as `terraform -chdir=<workspace> <subcommand> -no-color
<flags> <positionals>`. Terraform stops parsing flags at the first
positional argument, so `apply <plan> -input=false` fails; the flags always
come before the plan file, the import address or the lock ID.

`SystemRunner` streams the output of long commands to the console and
appends it to a private log, and captures the output of commands whose
stdout is data, such as `show -json` and `state pull`. It never raises when
Terraform fails; the caller reads the exit status. `Terraform` is the
facade the deploy steps use: it builds the child environment once, names
one log per command, and never passes `-var` or `-target` to `apply`, which
only ever applies a saved plan.

`tools.SystemTools` keeps running the quick read-only probes, such as
`terraform version`, with its short timeout.
"""

from collections.abc import Callable, Mapping, Sequence
import copy
import dataclasses
import datetime
import json
import os
import pathlib
import shlex
import signal
import subprocess
import threading
import types
from typing import IO, Any, Protocol, TextIO

from rich import console as rich_console

from stellar_engine import fsutil
from stellar_engine import paths
from stellar_engine.render import writer
from stellar_engine.terraform import env as env_lib

BINARY = "terraform"
# Seconds each subcommand may run. An apply of Stage 0 creates hundreds of
# resources, and an Assured Workloads workload alone can take minutes.
TIMEOUTS = {
    "init": 600,
    "plan": 900,
    "apply": 7200,
    "import": 900,
    "show": 300,
    "state": 300,
    "force-unlock": 120,
}
DEFAULT_TIMEOUT = 300
# Seconds Terraform gets to stop after an interrupt before it is killed.
# Terraform saves its state and releases the state lock on an interrupt.
INTERRUPT_GRACE_SECONDS = 60
# The exit status reported when the binary could not be started.
NOT_STARTED = 127


class Runner(Protocol):
    """Runs Terraform commands in a workspace."""

    def run(
        self,
        workspace: pathlib.Path,
        args: Sequence[str],
        *,
        env: Mapping[str, str],
        log: pathlib.Path,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        """Runs a command and streams its output to the console.

        Args:
            workspace: The Terraform root module, passed as `-chdir`.
            args: The arguments after `terraform -chdir=<workspace>`.
            env: The complete environment of the process.
            log: File that receives the merged stdout and stderr; created
                with mode 0600 when missing, appended to otherwise.
            timeout: Seconds before the command is interrupted.

        Returns:
            The completed process, whose `stdout` holds the merged output.
            A non-zero exit status is returned, never raised.
        """
        ...

    def capture(
        self,
        workspace: pathlib.Path,
        args: Sequence[str],
        *,
        env: Mapping[str, str],
        log: pathlib.Path,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        """Runs a command whose stdout is data, without printing it.

        Args:
            workspace: The Terraform root module, passed as `-chdir`.
            args: The arguments after `terraform -chdir=<workspace>`.
            env: The complete environment of the process.
            log: File that receives stderr only, because stdout can hold
                the whole state or plan.
            timeout: Seconds before the command is interrupted.

        Returns:
            The completed process with separate `stdout` and `stderr`. A
            non-zero exit status is returned, never raised.
        """
        ...


def command(
    workspace: pathlib.Path, args: Sequence[str], *, binary: str = BINARY
) -> list[str]:
    """Returns the full argv of a Terraform command.

    Args:
        workspace: The Terraform root module.
        args: The arguments after `terraform -chdir=<workspace>`.
        binary: The Terraform executable.
    """
    return [binary, f"-chdir={workspace}", *args]


def arguments(
    subcommand: Sequence[str],
    flags: Sequence[str] = (),
    positionals: Sequence[str] = (),
) -> list[str]:
    """Returns Terraform arguments in the order the binary accepts.

    Args:
        subcommand: The subcommand words, such as `("state", "pull")`.
        flags: Options such as `-input=false`.
        positionals: Plan files, addresses or IDs, which end flag parsing.
    """
    return [*subcommand, "-no-color", *flags, *positionals]


def manual(
    workspace: pathlib.Path,
    subcommand: Sequence[str],
    flags: Sequence[str] = (),
    positionals: Sequence[str] = (),
) -> str:
    """Returns a Terraform command line that the operator runs by hand.

    The words keep the order of `arguments`, without `-no-color`, so every
    printed fallback runs what the deploy itself would run.

    Args:
        workspace: The Terraform root module.
        subcommand: The subcommand words, such as `("init",)`.
        flags: Options such as `-input=false`.
        positionals: Plan files, addresses or IDs.
    """
    return shlex.join(
        [BINARY, f"-chdir={workspace}", *subcommand, *flags, *positionals]
    )


def manual_apply(
    workspace: pathlib.Path, plan: pathlib.Path, targets: Sequence[str] = ()
) -> list[str]:
    """Returns the commands that initialize, plan and apply by hand.

    They are the commands `stellar deploy` runs, ending with the apply of
    the saved plan. The plan goes under the environment's `plans/`, never
    into the workspace, where a stale plan file could be applied later.

    Args:
        workspace: The Terraform root module.
        plan: The plan file, such as `<env>/plans/s0.tfplan`.
        targets: `-target` addresses of a targeted plan.
    """
    flags = ("-input=false",)
    plan_flags = (
        *flags,
        *(f"-target={target}" for target in targets),
        f"-out={plan}",
    )
    return [
        manual(workspace, ("init",), flags),
        manual(workspace, ("plan",), plan_flags),
        manual(workspace, ("apply",), flags, (str(plan),)),
    ]


def timeout_for(args: Sequence[str]) -> int:
    """Returns the timeout in seconds for a command's arguments.

    Args:
        args: The arguments after `terraform -chdir=<workspace>`.
    """
    if not args:
        return DEFAULT_TIMEOUT
    return TIMEOUTS.get(args[0], DEFAULT_TIMEOUT)


def _open_log(log: pathlib.Path) -> TextIO:
    """Opens a log for appending, creating it and its directory privately."""
    paths.make_private_dir(log.parent)
    descriptor = os.open(
        log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, fsutil.PRIVATE_FILE_MODE
    )
    handle = os.fdopen(descriptor, "a", encoding="utf-8")
    os.fchmod(handle.fileno(), fsutil.PRIVATE_FILE_MODE)
    return handle


def _footer(handle: TextIO, returncode: int) -> None:
    handle.write(f"# exit status {returncode}\n")


def _timed_out(args: Sequence[str], timeout: int) -> str:
    name = " ".join(args[:1])
    return (
        f"stellar: terraform {name} ran longer than {timeout} seconds and "
        "was interrupted.\n"
    )


class _Deadline:
    """Interrupts a process at its timeout, then kills it after a grace."""

    def __init__(
        self, process: subprocess.Popen[str], timeout: int, grace: int
    ) -> None:
        self.expired = False
        self._process = process
        self._timers = (
            threading.Timer(timeout, self._interrupt),
            threading.Timer(timeout + grace, process.kill),
        )
        for timer in self._timers:
            timer.daemon = True

    def _interrupt(self) -> None:
        self.expired = True
        self._process.send_signal(signal.SIGINT)

    def __enter__(self) -> _Deadline:
        for timer in self._timers:
            timer.start()
        return self

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        raised: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        for timer in self._timers:
            timer.cancel()


class SystemRunner:
    """Runs the Terraform binary through `subprocess.Popen`.

    The process gets exactly the environment it is given, never the parent
    environment, and no shell.
    """

    def __init__(
        self,
        console: rich_console.Console | None = None,
        *,
        binary: str = BINARY,
        grace: int = INTERRUPT_GRACE_SECONDS,
    ) -> None:
        """Initializes the runner.

        Args:
            console: Console that receives the streamed output.
            binary: The Terraform executable.
            grace: Seconds an interrupted process gets before it is killed.
        """
        self._console = console or rich_console.Console()
        self._binary = binary
        self._grace = grace

    def _echo(self, line: str) -> None:
        # `out` applies no markup, so `[0]` in an address prints as is.
        self._console.out(line.rstrip("\n"), highlight=False)

    def _not_started(
        self,
        argv: list[str],
        error: OSError,
        handle: TextIO,
        *,
        capture: bool,
    ) -> subprocess.CompletedProcess[str]:
        """Reports a binary that did not start where its output would go."""
        message = f"stellar: cannot run {argv[0]}: {error}\n"
        handle.write(message)
        _footer(handle, NOT_STARTED)
        if capture:
            return subprocess.CompletedProcess(argv, NOT_STARTED, "", message)
        self._echo(message)
        return subprocess.CompletedProcess(argv, NOT_STARTED, message, "")

    def _spawn(
        self,
        argv: list[str],
        env: Mapping[str, str],
        *,
        stderr: int,
        bufsize: int = -1,
    ) -> subprocess.Popen[str]:
        """Starts the binary without a shell, on the given environment."""
        return subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=stderr,
            env=dict(env),
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=bufsize,
        )

    def _copy(
        self, stream: IO[str] | None, lines: list[str], handle: TextIO
    ) -> None:
        for line in stream or ():
            lines.append(line)
            handle.write(line)
            handle.flush()
            self._echo(line)

    def _stream(
        self,
        process: subprocess.Popen[str],
        lines: list[str],
        handle: TextIO,
    ) -> None:
        try:
            self._copy(process.stdout, lines, handle)
        except KeyboardInterrupt:
            # Terraform got the same interrupt and stops on its own. Keep
            # reading until it exits, so it can save its state and release
            # the state lock instead of dying on a closed pipe.
            self._copy(process.stdout, lines, handle)
            process.wait()
            raise
        process.wait()

    def run(
        self,
        workspace: pathlib.Path,
        args: Sequence[str],
        *,
        env: Mapping[str, str],
        log: pathlib.Path,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        """See `Runner.run`."""
        argv = command(workspace, args, binary=self._binary)
        with _open_log(log) as handle:
            try:
                process = self._spawn(
                    argv, env, stderr=subprocess.STDOUT, bufsize=1
                )
            except OSError as error:
                return self._not_started(argv, error, handle, capture=False)
            lines: list[str] = []
            with _Deadline(process, timeout, self._grace) as deadline:
                self._stream(process, lines, handle)
            if deadline.expired:
                message = _timed_out(args, timeout)
                lines.append(message)
                handle.write(message)
                self._echo(message)
            _footer(handle, process.returncode)
        return subprocess.CompletedProcess(
            argv, process.returncode, "".join(lines), ""
        )

    def _stop(self, process: subprocess.Popen[str]) -> tuple[str, str]:
        process.send_signal(signal.SIGINT)
        try:
            return process.communicate(timeout=self._grace)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.communicate()

    def capture(
        self,
        workspace: pathlib.Path,
        args: Sequence[str],
        *,
        env: Mapping[str, str],
        log: pathlib.Path,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        """See `Runner.capture`."""
        argv = command(workspace, args, binary=self._binary)
        with _open_log(log) as handle:
            try:
                process = self._spawn(argv, env, stderr=subprocess.PIPE)
            except OSError as error:
                return self._not_started(argv, error, handle, capture=True)
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                stdout, stderr = self._stop(process)
                stderr += _timed_out(args, timeout)
            handle.write(stderr)
            _footer(handle, process.returncode)
        return subprocess.CompletedProcess(
            argv, process.returncode, stdout, stderr
        )


class TerraformError(Exception):
    """Raised when a command whose output stellar parses fails.

    Attributes:
        completed: The completed process.
        log: The log of the command.
    """

    def __init__(
        self,
        message: str,
        completed: subprocess.CompletedProcess[str],
        log: pathlib.Path,
    ) -> None:
        """Initializes the error.

        Args:
            message: What failed.
            completed: The completed process.
            log: The log of the command.
        """
        super().__init__(message)
        self.completed = completed
        self.log = log

    @property
    def output(self) -> str:
        """Returns the stdout and stderr of the command."""
        return output(self.completed)


def output(completed: subprocess.CompletedProcess[str]) -> str:
    """Returns the stdout and then the stderr of a completed command.

    Args:
        completed: The completed command; `run` merges both into stdout.
    """
    return (completed.stdout or "") + (completed.stderr or "")


@dataclasses.dataclass(frozen=True)
class PlanFiles:
    """The files of one saved plan under the environment's `plans/`.

    Attributes:
        tfplan: The binary plan that `apply` applies.
        json: The `terraform show -json` document.
        text: The `terraform show` text.
    """

    tfplan: pathlib.Path
    json: pathlib.Path
    text: pathlib.Path


def plan_files(
    plans_dir: pathlib.Path, *, stage: str, step: str, now: datetime.datetime
) -> PlanFiles:
    """Returns the paths `<stage>-<step>-<ts>.tfplan|.json|.txt`.

    Args:
        plans_dir: The environment's `plans/` directory.
        stage: The catalog stage, such as `0`.
        step: The step ID, such as `s0.apply_final`.
        now: The current time.
    """
    base = f"{stage}-{step}-{writer.stamp(now)}"
    return PlanFiles(
        tfplan=plans_dir / f"{base}.tfplan",
        json=plans_dir / f"{base}.json",
        text=plans_dir / f"{base}.txt",
    )


def state_backup_path(
    plans_dir: pathlib.Path, *, step: str, now: datetime.datetime
) -> pathlib.Path:
    """Returns the path `terraform.tfstate.before-<step>.<ts>`.

    Args:
        plans_dir: The environment's `plans/` directory.
        step: What the backup comes before, such as `migrate`.
        now: The current time.
    """
    return plans_dir / f"terraform.tfstate.before-{step}.{writer.stamp(now)}"


def providers_backup_path(
    plans_dir: pathlib.Path, name: str, *, now: datetime.datetime
) -> pathlib.Path:
    """Returns the path `<name>.local.<ts>` of a replaced providers file.

    Args:
        plans_dir: The environment's `plans/` directory.
        name: The providers file name, such as `0-bootstrap-providers.tf`.
        now: The current time.
    """
    return plans_dir / f"{name}.local.{writer.stamp(now)}"


def fixed_state_path(
    plans_dir: pathlib.Path, *, now: datetime.datetime
) -> pathlib.Path:
    """Returns the path `state-fixed.<ts>.json` of a rewritten state.

    Args:
        plans_dir: The environment's `plans/` directory.
        now: The current time.
    """
    return plans_dir / f"state-fixed.{writer.stamp(now)}.json"


def _absolute(path: pathlib.Path) -> str:
    # `-chdir` resolves relative paths against the workspace instead.
    return str(pathlib.Path(path).absolute())


class Terraform:
    """Runs the Terraform commands of the deploy steps.

    Each command gets its own log, `logs/<ts>-<stage>-<step>-<cmd>.log`,
    whose header names the scrubbed and kept environment variables.

    Attributes:
        child_env: The child environment and how it was built.
        logs: The logs of the commands run so far, oldest first.
    """

    def __init__(
        self,
        runner: Runner,
        environ: Mapping[str, str],
        logs_dir: pathlib.Path,
        now: Callable[[], datetime.datetime],
        *,
        stage: str = "",
        step: str = "",
    ) -> None:
        """Initializes the facade.

        Args:
            runner: Runs the commands.
            environ: The parent environment that `env.build_env` scrubs.
            logs_dir: The environment's `logs/` directory.
            now: Returns the current time, which names logs and plans.
            stage: The catalog stage that names logs, such as `0`.
            step: The step ID that names logs, such as `s0.apply_final`.
        """
        self.child_env = env_lib.build_env(environ)
        self.logs: list[pathlib.Path] = []
        self._runner = runner
        self._logs_dir = pathlib.Path(logs_dir)
        self._now = now
        self._stage = stage
        self._step = step

    def for_step(self, stage: str, step: str) -> Terraform:
        """Returns a facade that names its logs and plans after a step.

        Args:
            stage: The catalog stage, such as `0`.
            step: The step ID, such as `s0.apply_final`.
        """
        bound = copy.copy(self)
        bound.logs = []
        bound._stage = stage
        bound._step = step
        return bound

    @property
    def last_log(self) -> pathlib.Path | None:
        """Returns the log of the latest command, or None."""
        return self.logs[-1] if self.logs else None

    def plan_files(self, plans_dir: pathlib.Path) -> PlanFiles:
        """Returns new plan file paths for the bound stage and step.

        Args:
            plans_dir: The environment's `plans/` directory.
        """
        return plan_files(
            plans_dir, stage=self._stage, step=self._step, now=self._now()
        )

    def _new_log(
        self, label: str, workspace: pathlib.Path, args: Sequence[str]
    ) -> pathlib.Path:
        """Creates a log with its header and returns its path."""
        paths.make_private_dir(self._logs_dir)
        now = self._now()
        parts = [writer.stamp(now), self._stage, self._step, label]
        base = "-".join(part for part in parts if part)
        counter = 0
        while True:
            name = f"{base}.log" if counter == 0 else f"{base}.{counter}.log"
            log = self._logs_dir / name
            try:
                descriptor = os.open(
                    log,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    fsutil.PRIVATE_FILE_MODE,
                )
            except FileExistsError:
                counter += 1
                continue
            break
        header = [
            f"stellar {now.astimezone(datetime.UTC).isoformat()}",
            f"workspace: {workspace}",
            "command: " + shlex.join(command(workspace, args)),
            *self.child_env.header(),
        ]
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), fsutil.PRIVATE_FILE_MODE)
            handle.writelines(f"# {line}\n" for line in header)
        self.logs.append(log)
        return log

    def _call(
        self,
        workspace: pathlib.Path,
        args: list[str],
        *,
        label: str,
        capture: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], pathlib.Path]:
        log = self._new_log(label, workspace, args)
        method = self._runner.capture if capture else self._runner.run
        completed = method(
            workspace,
            args,
            env=self.child_env.env,
            log=log,
            timeout=timeout_for(args),
        )
        return completed, log

    def _checked(
        self,
        workspace: pathlib.Path,
        args: list[str],
        *,
        label: str,
    ) -> tuple[str, pathlib.Path]:
        completed, log = self._call(workspace, args, label=label, capture=True)
        if completed.returncode != 0:
            raise TerraformError(
                f"terraform {label} failed with exit status "
                f"{completed.returncode}; see {log}",
                completed,
                log,
            )
        return completed.stdout, log

    def _json(
        self,
        workspace: pathlib.Path,
        args: list[str],
        *,
        label: str,
        allow_empty: bool = False,
    ) -> dict[str, Any]:
        stdout, log = self._checked(workspace, args, label=label)
        if allow_empty and not stdout.strip():
            return {}
        try:
            data = json.loads(stdout)
        except ValueError as error:
            raise TerraformError(
                f"terraform {label} printed no JSON: {error}; see {log}",
                subprocess.CompletedProcess(args, 0, stdout, ""),
                log,
            ) from error
        if not isinstance(data, dict):
            raise TerraformError(
                f"terraform {label} printed no JSON object; see {log}",
                subprocess.CompletedProcess(args, 0, stdout, ""),
                log,
            )
        return data

    def init(
        self,
        workspace: pathlib.Path,
        *,
        migrate: bool = False,
        force_copy: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Runs `terraform init -input=false`.

        Args:
            workspace: The Terraform root module.
            migrate: Adds `-migrate-state`.
            force_copy: Adds `-force-copy`, which copies the state into a
                new backend without asking and overwrites a non-empty
                destination; the caller decides that it is safe.
        """
        flags = ["-input=false"]
        if migrate:
            flags.append("-migrate-state")
        if force_copy:
            flags.append("-force-copy")
        completed, _ = self._call(
            workspace, arguments(("init",), flags), label="init"
        )
        return completed

    def plan(
        self,
        workspace: pathlib.Path,
        out: pathlib.Path,
        *,
        targets: Sequence[str] = (),
    ) -> subprocess.CompletedProcess[str]:
        """Runs `terraform plan -out` and saves the plan file.

        A plan made with `-target` records its targets, so `apply` of the
        saved plan needs none.

        Args:
            workspace: The Terraform root module.
            out: The plan file to write.
            targets: Resource or module addresses for `-target`.
        """
        flags = [
            "-input=false",
            f"-out={_absolute(out)}",
            *(f"-target={target}" for target in targets),
        ]
        completed, _ = self._call(
            workspace, arguments(("plan",), flags), label="plan"
        )
        return completed

    def show_json(
        self, workspace: pathlib.Path, plan: pathlib.Path
    ) -> dict[str, Any]:
        """Returns `terraform show -json` of a saved plan.

        Args:
            workspace: The Terraform root module.
            plan: The saved plan file.

        Raises:
            TerraformError: If the command fails or prints no JSON object.
        """
        args = arguments(("show",), ["-json"], [_absolute(plan)])
        return self._json(workspace, args, label="show-json")

    def show_text(self, workspace: pathlib.Path, plan: pathlib.Path) -> str:
        """Returns the `terraform show` text of a saved plan.

        Args:
            workspace: The Terraform root module.
            plan: The saved plan file.

        Raises:
            TerraformError: If the command fails.
        """
        args = arguments(("show",), (), [_absolute(plan)])
        stdout, _ = self._checked(workspace, args, label="show")
        return stdout

    def apply(
        self, workspace: pathlib.Path, plan: pathlib.Path
    ) -> subprocess.CompletedProcess[str]:
        """Applies a saved plan, never with `-var` or `-target`.

        Args:
            workspace: The Terraform root module.
            plan: The saved plan file.
        """
        args = arguments(("apply",), ["-input=false"], [_absolute(plan)])
        completed, _ = self._call(workspace, args, label="apply")
        return completed

    def state_pull(self, workspace: pathlib.Path) -> dict[str, Any]:
        """Returns the state of the workspace's backend.

        Args:
            workspace: The Terraform root module.

        Returns:
            The state document, or an empty dict when there is no state.

        Raises:
            TerraformError: If the command fails or prints no JSON object.
        """
        args = arguments(("state", "pull"))
        return self._json(workspace, args, label="state-pull", allow_empty=True)

    def state_push(
        self, workspace: pathlib.Path, path: pathlib.Path
    ) -> subprocess.CompletedProcess[str]:
        """Pushes a state file to the workspace's backend.

        Terraform refuses the push unless the lineage matches and the
        serial is not lower than the backend's, so a push at an equal
        serial is accepted; stellar never adds `-force`.

        Args:
            workspace: The Terraform root module.
            path: The state file to push.
        """
        args = arguments(("state", "push"), (), [_absolute(path)])
        completed, _ = self._call(workspace, args, label="state-push")
        return completed

    def import_resource(
        self, workspace: pathlib.Path, address: str, resource_id: str
    ) -> subprocess.CompletedProcess[str]:
        """Imports an existing object into the state.

        Args:
            workspace: The Terraform root module.
            address: The resource address, such as
                `module.x["k"].google_logging_project_bucket_config.bucket[0]`.
            resource_id: The import ID.
        """
        args = arguments(("import",), ["-input=false"], [address, resource_id])
        completed, _ = self._call(workspace, args, label="import")
        return completed

    def force_unlock(
        self, workspace: pathlib.Path, lock_id: str
    ) -> subprocess.CompletedProcess[str]:
        """Releases a state lock without asking; the caller confirms first.

        Args:
            workspace: The Terraform root module.
            lock_id: The lock ID that the lock error printed.
        """
        args = arguments(("force-unlock",), ["-force"], [lock_id])
        completed, _ = self._call(workspace, args, label="force-unlock")
        return completed
