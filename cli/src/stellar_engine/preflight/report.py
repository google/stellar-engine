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

"""Renders preflight results as a terminal table or as JSON."""

import collections
import json

from rich import table as rich_table
from rich import text as rich_text

from stellar_engine.preflight import result

_STYLES = {
    result.Status.PASS: "bold green",
    result.Status.WARN: "bold yellow",
    result.Status.FAIL: "bold red",
    result.Status.MANUAL: "bold cyan",
    result.Status.SKIP: "dim",
}


def summary(results):
    """Returns the number of results per status, in a fixed order."""
    counts = collections.Counter(item.status for item in results)
    return {status.value: counts.get(status, 0) for status in result.Status}


def render_table(console, results):
    """Prints results grouped by category, followed by a summary line.

    Args:
        console: A `rich.console.Console`.
        results: Results from `runner.run`.
    """
    for category in result.Category:
        rows = [item for item in results if item.category == category]
        if not rows:
            continue
        table = rich_table.Table(
            title=category.value, title_justify="left", expand=True
        )
        table.add_column("Status", no_wrap=True, width=8)
        table.add_column("Check", ratio=2, overflow="fold")
        table.add_column("Detail", ratio=5, overflow="fold")
        for item in rows:
            detail = rich_text.Text(item.detail)
            if item.remedy and item.status in (
                result.Status.FAIL,
                result.Status.WARN,
            ):
                detail.append(f"\nFix: {item.remedy}", style="italic")
            if item.doc and item.status != result.Status.PASS:
                detail.append(f"\nSee: {item.doc}", style="dim")
            table.add_row(
                rich_text.Text(item.status.value.upper(), _STYLES[item.status]),
                item.title,
                detail,
            )
        console.print(table)
    counts = summary(results)
    console.print(
        "Summary: "
        + ", ".join(f"{count} {status}" for status, count in counts.items())
    )


def render_json(results, inputs):
    """Returns the results and the inputs used as a JSON document."""
    document = {
        "inputs": inputs.model_dump(mode="json"),
        "summary": summary(results),
        "checks": [item.to_dict() for item in results],
    }
    return json.dumps(document, indent=2)
