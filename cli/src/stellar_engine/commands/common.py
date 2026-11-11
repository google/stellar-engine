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

"""Options, messages and environment loading shared by the commands.

Every error that the operator can fix ends the command through `fail`,
which prints `Error: <message>` to stderr and exits with one of the exit
codes that the `stellar_engine.cli` docstring lists.
"""

import dataclasses
import datetime
import os
import pathlib
import sys
import types
from typing import Annotated, NoReturn

from rich import console as rich_console
import typer

from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.config import validate as validate_lib
from stellar_engine.wizard import prompts

EXIT_CLOUD = 1
EXIT_USAGE = 2
EXIT_OVERWRITE_REFUSED = 3
# A deploy or an IAM command stopped for the operator: a manual step, a
# handoff to another identity, a declined question, a pending check, an
# engine or environment check that refused the run, a held lock, or a
# prompt that `--non-interactive` forbids. A rerun resumes there.
EXIT_STOPPED = 4
# A deploy step failed: Terraform failed after the bounded remedies, a
# plan guard refused the apply, or run-state is unreadable.
EXIT_FAILED = 5

HOME_SOURCES = {
    paths.HomeSource.FLAG: "from the --home flag",
    paths.HomeSource.ENV: f"from {paths.HOME_ENV_VAR}",
    paths.HomeSource.DEFAULT: "default inside the engine checkout",
}

# The shared options. `--home` deliberately has no envvar: Typer would copy
# STELLAR_HOME into the flag, and `env show` could no longer tell where the
# home came from. `paths.resolve_home` reads the variable itself.
HomeOption = Annotated[
    pathlib.Path | None,
    typer.Option(
        "--home",
        help=(
            "Home folder that holds the environments. Defaults to "
            f"${paths.HOME_ENV_VAR}, then <engine checkout>/"
            f"{paths.HOME_DIRNAME}."
        ),
        file_okay=False,
    ),
]
PrefixOption = Annotated[
    str | None,
    typer.Option(
        "--prefix",
        envvar="STELLAR_PREFIX",
        help="Environment prefix. Defaults to the current environment.",
    ),
]
RepoOption = Annotated[
    pathlib.Path | None,
    typer.Option(
        "--repo", help="Stellar Engine checkout to read. Auto-detected."
    ),
]


def non_interactive_option(help_text: str) -> typer.models.OptionInfo:
    """Returns the `--non-interactive` option with a command's own help.

    Pyright accepts no call in a type expression, so a command declares
    `Annotated[bool, non_interactive_option(...)]` itself.

    Args:
        help_text: What the flag means for the command.
    """
    return typer.Option("--non-interactive", help=help_text)


def error(message: object) -> None:
    """Prints an error to stderr without exiting."""
    typer.secho(f"Error: {message}", fg="red", err=True)


def fail(message: object, code: int = EXIT_USAGE) -> NoReturn:
    """Prints an error to stderr and exits with `code`."""
    error(message)
    raise typer.Exit(code)


def warn(message: object) -> None:
    """Prints a warning to stderr."""
    typer.secho(f"Warning: {message}", fg="yellow", err=True)


class ExitOn:
    """Ends the command with `fail` when the block raises given errors.

    Use it around calls whose errors the operator can fix and whose
    message is the error text itself:

        with common.ExitOn(answers_lib.AnswersError):
            answers = answers_lib.load(path)

    `__exit__` returns None, so type checkers know that the block never
    swallows an error and the names it binds stay bound after it.
    """

    def __init__(
        self, *errors: type[BaseException], code: int = EXIT_USAGE
    ) -> None:
        """Initializes the context manager.

        Args:
            *errors: Exception types that end the command.
            code: Exit code for those errors.
        """
        self._errors = errors
        self._code = code

    def __enter__(self) -> None:
        """Enters the block."""

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        raised: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        """Exits with the error text when `raised` is one of the errors."""
        if isinstance(raised, self._errors):
            fail(str(raised), self._code)


def stdin_is_tty() -> bool:
    """Returns whether standard input is a terminal.

    A function so tests can make a CliRunner invocation interactive.
    """
    return sys.stdin.isatty()


def interactive(non_interactive: bool) -> bool:
    """Returns whether the command may prompt the operator.

    Args:
        non_interactive: The value of the command's `--non-interactive`.
    """
    return not non_interactive and stdin_is_tty()


def prompter(
    console: rich_console.Console | None = None,
) -> prompts.QuestionaryPrompter:
    """Returns the prompter that asks the operator in the terminal.

    Args:
        console: Console for the prompter's notes, so a command keeps its
            notes on the console it prints everything else to.
    """
    return prompts.QuestionaryPrompter(console)


def console(stderr: bool = False) -> rich_console.Console:
    """Returns a Rich console for tables and status lines.

    Args:
        stderr: Prints to stderr instead of stdout.
    """
    return rich_console.Console(stderr=stderr)


def now() -> datetime.datetime:
    """Returns the current time in UTC, which names backups."""
    return datetime.datetime.now(datetime.UTC)


@dataclasses.dataclass(frozen=True)
class Session:
    """The engine checkout and home that one command works with."""

    repo: repo_lib.Repo
    resolved: paths.ResolvedHome

    @property
    def home(self) -> paths.Home:
        """The resolved home."""
        return paths.Home(self.resolved.path)


def session(
    home_flag: pathlib.Path | None, repo_flag: pathlib.Path | None
) -> Session:
    """Resolves the engine checkout, then the home inside or beside it.

    Args:
        home_flag: The `--home` value, if any.
        repo_flag: The `--repo` value, if any.

    Returns:
        The session, or exits 2 when no engine checkout is found.
    """
    with ExitOn(repo_lib.RepoError):
        repository = repo_lib.Repo(repo_lib.find_root(repo_flag))
    resolved = paths.resolve_home(home_flag, os.environ, repository.root)
    return Session(repository, resolved)


def env(home: paths.Home, prefix: str | None) -> paths.EnvPaths:
    """Returns the paths of the selected environment, or exits 2.

    Args:
        home: The home that holds the environments.
        prefix: The `--prefix` value; None selects the current environment.
    """
    with ExitOn(paths.NoEnvironmentError, ValueError):
        return home.env(home.resolve_prefix(prefix))


def load_answers(
    env: paths.EnvPaths, repository: repo_lib.Repo, *, check_repo=True
) -> models.Answers:
    """Loads and validates an environment's answers, or exits 2.

    Args:
        env: The environment paths.
        repository: The engine checkout.
        check_repo: Whether to also apply the repository rules of
            `validate.problems`.
    """
    if not env.answers.is_file():
        fail(
            f"No answers for {env.prefix} at {env.answers}. Run `stellar "
            f"init --prefix {env.prefix}` first."
        )
    with ExitOn(answers_lib.AnswersError):
        answers = answers_lib.load(env.answers)
    if answers.prefix != env.prefix:
        fail(
            f"{env.answers} sets prefix {answers.prefix}, but it belongs to "
            f"environment {env.prefix}. Set prefix back to {env.prefix}, or "
            f"run `stellar init --answers-from {env.prefix} --prefix "
            f"{answers.prefix}` to copy it into a new environment."
        )
    if check_repo:
        found = validate_lib.problems(answers, repository)
        if found:
            fail(bullets(f"{env.answers} has problems:", found))
    return answers


def load_env(
    session: Session, prefix: str | None, *, check_repo=True
) -> tuple[paths.EnvPaths, models.Answers]:
    """Selects an environment and loads its answers, or exits 2.

    Args:
        session: The engine checkout and home.
        prefix: The `--prefix` value; None selects the current environment.
        check_repo: Whether to also apply the repository rules of
            `validate.problems`.

    Returns:
        The environment paths and its answers.
    """
    selected = env(session.home, prefix)
    answers = load_answers(selected, session.repo, check_repo=check_repo)
    return selected, answers


def bullets(title: str, lines: list[str]) -> str:
    """Returns a title followed by one `- ` line per item."""
    return "\n".join([title, *(f"- {line}" for line in lines)])
