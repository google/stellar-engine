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

"""Tests for running checks end to end and rendering the report."""

import json

from rich import console as rich_console

from stellar_engine.preflight import report
from stellar_engine.preflight import result
from stellar_engine.preflight import runner

Status = result.Status


def _item(status):
    return result.CheckResult(
        f"x.{status}", result.Category.TOOLS, "x", status, "detail"
    )


def test_full_run_on_healthy_fake(make_ctx):
    results = runner.run(make_ctx())
    counts = report.summary(results)
    assert counts["fail"] == 0
    assert counts["warn"] == 0
    assert counts["manual"] == 3
    assert runner.exit_code(results) == 0


def test_crashing_check_is_reported(make_ctx):
    def check_boom(ctx):
        raise RuntimeError("kaboom")

    results = runner.run(make_ctx(), (check_boom,))
    assert results[0].status == Status.FAIL
    assert "RuntimeError: kaboom" in results[0].detail


def test_exit_codes():
    assert runner.exit_code([_item(Status.PASS), _item(Status.MANUAL)]) == 0
    assert runner.exit_code([_item(Status.WARN)]) == 0
    assert runner.exit_code([_item(Status.WARN)], strict=True) == 1
    assert runner.exit_code([_item(Status.FAIL)]) == 1


def test_render_json(make_ctx):
    ctx = make_ctx()
    document = json.loads(report.render_json([_item(Status.FAIL)], ctx.inputs))
    assert document["summary"]["fail"] == 1
    assert document["checks"][0]["status"] == "fail"
    assert document["checks"][0]["category"] == "Local tools"
    assert document["inputs"]["regime"] == "IL5"


def test_render_table_shows_remedy_for_failures():
    console = rich_console.Console(record=True, width=120)
    failing = result.CheckResult(
        "a",
        result.Category.TOOLS,
        "Thing",
        Status.FAIL,
        "broken",
        remedy="fix it",
        doc="docs/x.md#y",
    )
    passing = result.CheckResult(
        "b",
        result.Category.TOOLS,
        "Other",
        Status.PASS,
        "fine",
        remedy="never shown",
        doc="docs/hidden.md",
    )
    report.render_table(console, [failing, passing])
    text = console.export_text()
    assert "Fix: fix it" in text
    assert "See: docs/x.md#y" in text
    assert "never shown" not in text
    assert "docs/hidden.md" not in text
    assert "1 pass" in text
