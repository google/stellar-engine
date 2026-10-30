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

"""Tests for the wizard prompters."""

import io

import pytest
from rich import console as rich_console

from stellar_engine.wizard import prompts


def _not_x(text):
    return "no x" if "x" in text else None


def test_scripted_text_uses_default_for_none():
    prompter = prompts.ScriptedPrompter([None, "typed"])
    assert prompter.text("first", default="kept") == "kept"
    assert prompter.text("second", default="kept") == "typed"
    assert prompter.asked == ["first", "second"]


def test_scripted_text_without_default_is_empty():
    assert prompts.ScriptedPrompter([None]).text("q") == ""


def test_scripted_text_reasks_on_invalid_answer():
    prompter = prompts.ScriptedPrompter(["xx", "ok"])
    assert prompter.text("q", validate=_not_x) == "ok"
    assert prompter.asked == ["q", "q"]
    assert prompter.notes == ["no x"]


def test_scripted_confirm_and_select():
    prompter = prompts.ScriptedPrompter([None, False, None, None, "b"])
    assert prompter.confirm("c1", default=True) is True
    assert prompter.confirm("c2") is False
    assert prompter.select("s1", ["a", "b"], default="b") == "b"
    assert prompter.select("s2", ["a", "b"]) == "a"
    assert prompter.select("s3", ["a", "b"], default="a") == "b"


def test_scripted_select_default_not_in_choices_falls_back():
    prompter = prompts.ScriptedPrompter([None])
    assert prompter.select("s", ["a", "b"], default="z") == "a"


@pytest.mark.parametrize(
    ("answers", "call", "error"),
    [
        ([], lambda p: p.text("q"), prompts.ScriptExhaustedError),
        ([True], lambda p: p.text("q"), TypeError),
        (["yes"], lambda p: p.confirm("q"), TypeError),
        (["c"], lambda p: p.select("q", ["a", "b"]), ValueError),
    ],
)
def test_scripted_errors(answers, call, error):
    with pytest.raises(error):
        call(prompts.ScriptedPrompter(answers))


def test_scripted_notes():
    prompter = prompts.ScriptedPrompter([])
    prompter.note("hello")
    assert prompter.notes == ["hello"]


class _Question:
    def __init__(self, answer):
        self.answer = answer

    def unsafe_ask(self):
        return self.answer


def test_questionary_prompter(monkeypatch):
    calls = {}

    def text(message, default, validate):
        calls["text"] = (message, default, validate)
        return _Question("typed")

    def confirm(message, default):
        calls["confirm"] = (message, default)
        return _Question(False)

    def select(message, choices, default):
        calls["select"] = (message, choices, default)
        return _Question(choices[0])

    monkeypatch.setattr(prompts.questionary, "text", text)
    monkeypatch.setattr(prompts.questionary, "confirm", confirm)
    monkeypatch.setattr(prompts.questionary, "select", select)
    prompter = prompts.QuestionaryPrompter()
    assert prompter.text("t", validate=_not_x) == "typed"
    message, default, check = calls["text"]
    assert (message, default) == ("t", "")
    # questionary wants True for valid text and the message otherwise.
    assert check("abc") is True
    assert check("x") == "no x"
    assert prompter.text("t2", default="d") == "typed"
    assert calls["text"][1:] == ("d", None)
    assert prompter.confirm("c", default=True) is False
    assert calls["confirm"] == ("c", True)
    assert prompter.select("s", ["a", "b"], default="z") == "a"
    # A default outside the choices would make questionary raise.
    assert calls["select"] == ("s", ["a", "b"], None)
    prompter.select("s", ["a", "b"], default="b")
    assert calls["select"][2] == "b"


def test_questionary_note_is_not_markup():
    output = io.StringIO()
    console = rich_console.Console(file=output, width=200)
    prompts.QuestionaryPrompter(console).note("module.x[0].y [bold]")
    assert output.getvalue() == "module.x[0].y [bold]\n"


@pytest.mark.parametrize(
    ("typed", "confirmed"),
    [("123456789012", True), ("  123456789012 ", True), ("12345", False)],
)
def test_typed_confirm(typed, confirmed):
    prompter = prompts.ScriptedPrompter([typed])
    found = prompts.typed_confirm(prompter, "Change the org.", "123456789012")
    assert found is confirmed
    assert prompter.asked == ["Change the org. Type 123456789012 to confirm:"]


def test_typed_confirm_has_no_default():
    # Enter accepts the default, which is empty, so it never confirms.
    prompter = prompts.ScriptedPrompter([None])
    assert not prompts.typed_confirm(prompter, "Change it.", "abc")
