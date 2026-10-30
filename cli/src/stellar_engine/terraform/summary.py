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

"""Prints a parsed plan for the operator to review before an apply.

The summary counts every change per action and lists the changes that
deserve a look: deletes, replacements, updates and imports, most
destructive first. Plain creates are only counted. The findings of the
plan guards follow in a second table.
"""

from collections.abc import Sequence

from rich import console as rich_console
from rich import table as rich_table
from rich import text as rich_text

from stellar_engine.terraform import guards
from stellar_engine.terraform import plan as plan_lib

# Rows the summary lists, most destructive first; the rest are counted.
_ROW_ORDER = ("delete", "forget", "replace", "update", "create", "no-op")
_STYLES = {
    "delete": "bold red",
    "forget": "bold red",
    "replace": "bold red",
    "update": "bold yellow",
    "create": "green",
    "no-op": "dim",
}
_LEVEL_STYLES = {
    guards.Level.BLOCK: "bold red",
    guards.Level.CONFIRM: "bold yellow",
    guards.Level.INFO: "dim",
}


def _detail(change: plan_lib.Change) -> str:
    parts = []
    if change.importing:
        parts.append(f"import {change.importing_id}")
    if change.action_reason:
        parts.append(change.action_reason)
    if change.forced_paths:
        parts.append(f"forces replacement: {', '.join(change.forced_paths)}")
    if change.deposed:
        parts.append(f"deposed object {change.deposed}")
    if change.previous_address:
        parts.append(f"moved from {change.previous_address}")
    return "; ".join(parts)


def _rows(plan: plan_lib.Plan) -> list[plan_lib.Change]:
    """Returns the changes the summary lists, most destructive first.

    Imports are listed even when they change nothing else; plain creates
    are only counted.
    """
    listed = [
        change
        for change in plan.changes
        if change.managed
        and (change.importing or change.action not in ("create", "no-op"))
    ]
    return sorted(listed, key=lambda change: _ROW_ORDER.index(change.action))


def render(
    console: rich_console.Console,
    plan: plan_lib.Plan,
    findings: Sequence[guards.Finding],
    *,
    limit: int = 50,
) -> None:
    """Prints the counts, the changes to review and the guard findings.

    Plain creates are only counted, because a first Stage 0 apply creates
    hundreds of resources that Terraform already printed.

    Args:
        console: A `rich.console.Console`.
        plan: The plan.
        findings: The findings of `guards.evaluate`.
        limit: The most change rows to print.
    """
    counts = rich_table.Table(title="Plan summary", title_justify="left")
    for key in plan_lib.SUMMARY_KEYS:
        counts.add_column(key, justify="right")
    counts.add_row(*(str(count) for count in plan_lib.summary(plan).values()))
    console.print(counts)
    if not plan.applyable:
        console.print("The plan changes nothing, so stellar skips the apply.")
    drifted = sum(change.material() for change in plan.drift)
    if drifted:
        console.print(
            f"{drifted} resources changed outside Terraform since the last "
            "apply, not counting etag-only changes."
        )
    rows = _rows(plan)
    if rows:
        console.print(_changes_table(rows, limit))
    if findings:
        console.print(_findings_table(findings))


def _changes_table(rows: list[plan_lib.Change], limit: int) -> rich_table.Table:
    table = rich_table.Table(
        title="Changes to review", title_justify="left", expand=True
    )
    table.add_column("Action", no_wrap=True, width=8)
    table.add_column("Address", ratio=3, overflow="fold")
    table.add_column("Detail", ratio=2, overflow="fold")
    for change in rows[:limit]:
        table.add_row(
            rich_text.Text(change.action, _STYLES[change.action]),
            rich_text.Text(change.address),
            rich_text.Text(_detail(change)),
        )
    if len(rows) > limit:
        table.add_row("", f"and {len(rows) - limit} more", "")
    return table


def _findings_table(findings: Sequence[guards.Finding]) -> rich_table.Table:
    table = rich_table.Table(
        title="Plan checks", title_justify="left", expand=True
    )
    table.add_column("Level", no_wrap=True, width=8)
    table.add_column("Check", ratio=1, overflow="fold")
    table.add_column("Detail", ratio=4, overflow="fold")
    for finding in findings:
        detail = rich_text.Text(finding.detail)
        if finding.address:
            detail = rich_text.Text(f"{finding.address}\n").append(detail)
        table.add_row(
            rich_text.Text(
                finding.level.value.upper(), _LEVEL_STYLES[finding.level]
            ),
            finding.key,
            detail,
        )
    return table
