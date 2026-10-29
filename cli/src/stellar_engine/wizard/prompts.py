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

"""Prompt interface of the wizard and its terminal and scripted versions.

The wizard depends only on the `Prompter` protocol. `QuestionaryPrompter`
asks in the terminal, and `ScriptedPrompter` replays a list of answers so
tests can drive every section without a TTY.
"""

from collections.abc import Callable
from typing import Any, Protocol

import questionary
from rich import console as rich_console

# A validator returns a readable problem, or None when the text is valid.
Validator = Callable[[str], str | None]


class Prompter(Protocol):
    """Asks the operator for one value at a time."""

    def text(
        self,
        message: str,
        default: str | None = None,
        validate: Validator | None = None,
    ) -> str:
        """Asks for free text; Enter accepts the default."""
        ...

    def confirm(self, message: str, default: bool = True) -> bool:
        """Asks a yes or no question."""
        ...

    def select(
        self, message: str, choices: list[str], default: str | None = None
    ) -> str:
        """Asks for one of the choices; the first one without a default."""
        ...

    def note(self, message: str) -> None:
        """Shows information that needs no answer."""
        ...


def _questionary_validator(validate):
    # questionary expects True for valid text and a message otherwise.
    if validate is None:
        return None

    def check(text):
        problem = validate(text)
        return True if problem is None else problem

    return check


class QuestionaryPrompter:
    """Asks in the terminal with questionary and prints notes with Rich.

    `unsafe_ask` raises KeyboardInterrupt on Ctrl-C instead of returning
    None, so an interrupted wizard never saves half an answer.
    """

    def __init__(self, console: rich_console.Console | None = None):
        """Initializes the prompter.

        Args:
            console: Console for notes. Defaults to standard output.
        """
        self._console = console or rich_console.Console()

    def text(self, message, default=None, validate=None):
        """See `Prompter.text`."""
        return questionary.text(
            message,
            default=default or "",
            validate=_questionary_validator(validate),
        ).unsafe_ask()

    def confirm(self, message, default=True):
        """See `Prompter.confirm`."""
        return questionary.confirm(message, default=default).unsafe_ask()

    def select(self, message, choices, default=None):
        """See `Prompter.select`."""
        if default not in choices:
            default = None
        return questionary.select(
            message, choices=choices, default=default
        ).unsafe_ask()

    def note(self, message):
        """See `Prompter.note`."""
        # Values such as `[0]` in resource addresses are not Rich markup.
        self._console.print(message, markup=False, highlight=False)


class ScriptExhaustedError(Exception):
    """Raised when the wizard asks more questions than the script holds."""


class ScriptedPrompter:
    """Replays answers in order, for tests.

    A None entry accepts the default. Text that fails validation consumes
    the next entry, the way the terminal asks again.

    Attributes:
        answers: Remaining scripted answers.
        asked: Every message asked, in order.
        notes: Every note shown, in order.
    """

    def __init__(self, answers: list[Any]):
        """Initializes the prompter.

        Args:
            answers: Strings for text and select, booleans for confirm, and
                None to accept the default.
        """
        self.answers = list(answers)
        self.asked: list[str] = []
        self.notes: list[str] = []

    def _next(self, message: str) -> Any:
        self.asked.append(message)
        if not self.answers:
            raise ScriptExhaustedError(f"No scripted answer for {message!r}")
        return self.answers.pop(0)

    def text(
        self,
        message: str,
        default: str | None = None,
        validate: Validator | None = None,
    ) -> str:
        """See `Prompter.text`."""
        while True:
            answer = self._next(message)
            if answer is None:
                answer = default or ""
            if not isinstance(answer, str):
                raise TypeError(f"{message!r} expects text, got {answer!r}")
            problem = validate(answer) if validate else None
            if problem is None:
                return answer
            self.notes.append(problem)

    def confirm(self, message: str, default: bool = True) -> bool:
        """See `Prompter.confirm`."""
        answer = self._next(message)
        if answer is None:
            return default
        if not isinstance(answer, bool):
            raise TypeError(f"{message!r} expects a bool, got {answer!r}")
        return answer

    def select(
        self, message: str, choices: list[str], default: str | None = None
    ) -> str:
        """See `Prompter.select`."""
        answer = self._next(message)
        if answer is None:
            answer = default if default in choices else choices[0]
        if answer not in choices:
            raise ValueError(f"{answer!r} is not one of {choices}")
        return answer

    def note(self, message: str) -> None:
        """See `Prompter.note`."""
        self.notes.append(message)
