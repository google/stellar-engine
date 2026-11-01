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

"""Tests for the options, errors and loaders that the commands share."""

import datetime
from typing import Annotated

import pytest
import typer

import conftest
import helpers
from stellar_engine.commands import common
from stellar_engine.wizard import prompts

pytestmark = pytest.mark.usefixtures("isolated_home")


class _SubclassError(ValueError):
    """A subclass of an error that ExitOn lists."""


def _session():
    """Returns the session of the checkout under test and the temp home."""
    return common.session(None, conftest.REPO_ROOT)


def test_exit_on_fails_with_the_error_text_and_code(capsys):
    with (
        pytest.raises(typer.Exit) as raised,
        common.ExitOn(KeyError, ValueError, code=common.EXIT_CLOUD),
    ):
        raise ValueError("the value is wrong")
    assert raised.value.exit_code == common.EXIT_CLOUD
    assert capsys.readouterr().err == "Error: the value is wrong\n"


def test_exit_on_defaults_to_the_usage_code(capsys):
    with pytest.raises(typer.Exit) as raised, common.ExitOn(ValueError):
        raise _SubclassError("a subclass also ends the command")
    assert raised.value.exit_code == common.EXIT_USAGE
    assert capsys.readouterr().err == (
        "Error: a subclass also ends the command\n"
    )


def test_exit_on_lets_other_errors_through(capsys):
    with pytest.raises(KeyError), common.ExitOn(ValueError):
        raise KeyError("not listed")
    assert capsys.readouterr().err == ""


def test_exit_on_keeps_the_names_bound(capsys):
    with common.ExitOn(ValueError):
        value = int("7")
    assert value == 7
    assert capsys.readouterr().err == ""


def test_load_env_selects_the_current_environment(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner, "aaa").exit_code == 0
    assert helpers.init_env(cli_runner, "bbb").exit_code == 0
    env, answers = common.load_env(_session(), None)
    assert env.prefix == "bbb"
    assert env.root == isolated_home / "envs" / "bbb"
    assert answers.prefix == "bbb"
    env, answers = common.load_env(_session(), "aaa")
    assert env.prefix == "aaa"
    assert answers.prefix == "aaa"


def test_load_env_without_answers_exits_2(capsys):
    with pytest.raises(typer.Exit) as raised:
        common.load_env(_session(), "nope")
    assert raised.value.exit_code == common.EXIT_USAGE
    assert "Run `stellar init --prefix nope` first." in capsys.readouterr().err


def test_load_env_with_a_stale_current_environment_exits_2(
    cli_runner, isolated_home, capsys
):
    assert helpers.init_env(cli_runner).exit_code == 0
    (isolated_home / "current").write_text("zzz\n")
    with pytest.raises(typer.Exit) as raised:
        common.load_env(_session(), None)
    assert raised.value.exit_code == common.EXIT_USAGE
    assert "current environment zzz no longer exists" in (
        capsys.readouterr().err
    )


def test_load_env_applies_the_repository_rules_on_request(
    cli_runner, isolated_home, capsys
):
    outcome = helpers.init_env(
        cli_runner,
        sets=("existing_org_policies=[iam.allowedPolicyMemberDomains]",),
    )
    assert outcome.exit_code == 0, outcome.output
    # The model accepts any policy name; only the repository rules know
    # which policies Stage 0 declares.
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text(
        path.read_text().replace(
            "iam.allowedPolicyMemberDomains", "unmanaged.constraint"
        )
    )
    _, answers = common.load_env(_session(), None, check_repo=False)
    assert answers.existing_org_policies == ["unmanaged.constraint"]
    with pytest.raises(typer.Exit) as raised:
        common.load_env(_session(), None)
    assert raised.value.exit_code == common.EXIT_USAGE
    error = capsys.readouterr().err
    assert f"Error: {path} has problems:\n- " in error
    assert "unmanaged.constraint" in error


@pytest.mark.parametrize(
    ("tty", "non_interactive", "expected"),
    [(True, False, True), (True, True, False), (False, False, False)],
)
def test_interactive_needs_a_terminal(
    monkeypatch, tty, non_interactive, expected
):
    monkeypatch.setattr(common, "stdin_is_tty", lambda: tty)
    assert common.interactive(non_interactive) is expected


def test_non_interactive_option_keeps_the_command_help(cli_runner):
    app = typer.Typer()

    @app.command()
    def command(
        non_interactive: Annotated[
            bool, common.non_interactive_option("Never prompt here.")
        ] = False,
    ):
        typer.echo(f"non_interactive={non_interactive}")

    assert cli_runner.invoke(app, ["--non-interactive"]).stdout == (
        "non_interactive=True\n"
    )
    assert "Never prompt here." in cli_runner.invoke(app, ["--help"]).stdout


def test_prompter_asks_in_the_terminal():
    assert isinstance(common.prompter(), prompts.QuestionaryPrompter)


def test_prompter_notes_on_the_given_console():
    console = common.console()
    assert common.prompter(console)._console is console


def test_console_prints_to_stdout_unless_asked():
    assert common.console().stderr is False
    assert common.console(stderr=True).stderr is True


def test_now_is_the_current_utc_time():
    before = datetime.datetime.now(datetime.UTC)
    now = common.now()
    after = datetime.datetime.now(datetime.UTC)
    assert now.tzinfo is datetime.UTC
    assert before <= now <= after
