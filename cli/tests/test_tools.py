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

"""Tests for the local tool queries."""

import subprocess

import pytest

from stellar_engine import tools


def test_terraform_fmt_without_terraform(monkeypatch):
    monkeypatch.setattr(tools.shutil, "which", lambda name: None)
    assert tools.SystemTools().terraform_fmt("a = 1\n") is None


def test_terraform_fmt_passes_text_on_stdin(monkeypatch):
    seen = {}

    def fake_run(args, **kwargs):
        seen["args"] = args
        seen["input"] = kwargs["input"]
        return subprocess.CompletedProcess(args, 0, stdout="formatted\n")

    monkeypatch.setattr(tools.shutil, "which", lambda name: "/bin/" + name)
    monkeypatch.setattr(tools.subprocess, "run", fake_run)
    assert tools.SystemTools().terraform_fmt("a=1\n") == "formatted\n"
    assert seen == {"args": ["terraform", "fmt", "-"], "input": "a=1\n"}


def test_terraform_fmt_rejected_text(monkeypatch):
    def fake_run(args, **kwargs):
        raise subprocess.CalledProcessError(2, args)

    monkeypatch.setattr(tools.shutil, "which", lambda name: "/bin/" + name)
    monkeypatch.setattr(tools.subprocess, "run", fake_run)
    assert tools.SystemTools().terraform_fmt("a = {\n") is None


@pytest.mark.terraform
def test_terraform_fmt_real_binary():
    system = tools.SystemTools()
    assert system.terraform_fmt("a = 1\nbbb = 2\n") == "a   = 1\nbbb = 2\n"
    assert system.terraform_fmt("a = {\n") is None
