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

"""Reads the `terraform show -json` document of a saved plan.

The parser reads JSON output format 1.x, which Terraform keeps backward
compatible within a major version. It refuses any other major version and
any action list it does not know, so a guard never misreads a plan it
cannot classify. `resource_drift` is absent from plans without drift, such
as a first apply, and reads as empty.
"""

import collections
from collections.abc import Mapping
import dataclasses
from typing import Any

FORMAT_MAJOR = "1"
MANAGED = "managed"
# Every action list of the format, with its summary category. Terraform
# 1.7 and later emit `forget` for `removed` blocks that keep the object.
ACTIONS = {
    ("no-op",): "no-op",
    ("create",): "create",
    ("read",): "read",
    ("update",): "update",
    ("delete",): "delete",
    ("delete", "create"): "replace",
    ("create", "delete"): "replace",
    ("forget",): "forget",
}
# The summary counts, in display order. `import` counts every importing
# change in addition to its action.
SUMMARY_KEYS = (
    "create",
    "update",
    "replace",
    "delete",
    "forget",
    "import",
    "read",
    "no-op",
)
# Attributes whose drift alone means nothing: the API bumps them on reads.
NOISE_ATTRIBUTES = frozenset({"etag", "update_time"})


class PlanError(ValueError):
    """Raised when a document is not a plan that stellar can read."""


@dataclasses.dataclass(frozen=True)
class Change:
    """One entry of `resource_changes` or `resource_drift`.

    Attributes:
        address: The resource instance address.
        module_address: The module instance address, or None at the root.
        type: The resource type, such as `google_project`.
        name: The resource name in the configuration.
        index: The `count` or `for_each` key, or None.
        mode: `managed` or `data`.
        actions: The action list, such as `("delete", "create")`.
        action_reason: Why Terraform chose the action, or None.
        importing_id: The import ID of an importing change, else None.
        replace_paths: Attribute paths that force a replacement.
        before: The prior values, or None.
        after: The planned values, or None on a delete.
        after_unknown: True at each value known only after apply.
        previous_address: The address before a `moved` block, or None.
        deposed: The deposed object key, or None.
    """

    address: str
    module_address: str | None
    type: str
    name: str
    index: int | str | None
    mode: str
    actions: tuple[str, ...]
    action_reason: str | None
    importing_id: str | None
    replace_paths: tuple[tuple[Any, ...], ...]
    before: Any
    after: Any
    after_unknown: Any
    previous_address: str | None = None
    deposed: str | None = None

    @property
    def action(self) -> str:
        """Returns the summary category, such as `replace`."""
        return ACTIONS[self.actions]

    @property
    def managed(self) -> bool:
        """Returns whether the change is to a managed resource."""
        return self.mode == MANAGED

    @property
    def importing(self) -> bool:
        """Returns whether the change imports an existing object."""
        return self.importing_id is not None

    @property
    def deletes(self) -> bool:
        """Returns whether the change destroys the object, as a replace."""
        return "delete" in self.actions

    @property
    def destructive(self) -> bool:
        """Returns whether the object leaves the state."""
        return self.deletes or "forget" in self.actions

    @property
    def changes_something(self) -> bool:
        """Returns whether a managed change does more than nothing."""
        return self.managed and self.actions != ("no-op",)

    @property
    def unknown_attributes(self) -> tuple[str, ...]:
        """Returns the top-level attributes known only after apply."""
        if not isinstance(self.after_unknown, Mapping):
            return ()
        return tuple(
            sorted(
                key
                for key, value in self.after_unknown.items()
                if has_unknown(value)
            )
        )

    @property
    def forced_paths(self) -> tuple[str, ...]:
        """Returns the attribute paths that force a replacement, dotted."""
        return tuple(
            ".".join(str(step) for step in path) for path in self.replace_paths
        )

    def material(self) -> bool:
        """Returns whether `before` and `after` differ beyond the noise.

        Differences only in `NOISE_ATTRIBUTES` at any depth, such as the
        `etag` that every read of an organization policy refreshes, do not
        count.
        """
        return _without_noise(self.before) != _without_noise(self.after)


def has_unknown(value: Any) -> bool:
    """Returns whether an `after_unknown` value marks anything unknown.

    Args:
        value: An `after_unknown` entry: True at an unknown value, or a
            mapping or list of entries.
    """
    if isinstance(value, Mapping):
        return any(has_unknown(item) for item in value.values())
    if isinstance(value, list):
        return any(has_unknown(item) for item in value)
    return value is True


def _without_noise(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _without_noise(item)
            for key, item in value.items()
            if key not in NOISE_ATTRIBUTES
        }
    if isinstance(value, list):
        return [_without_noise(item) for item in value]
    return value


@dataclasses.dataclass(frozen=True)
class Plan:
    """A parsed `terraform show -json` plan.

    Attributes:
        format_version: The JSON output format, such as `1.2`.
        terraform_version: The Terraform version that made the plan.
        applyable: Whether applying the plan changes anything.
        complete: Whether applying the plan converges, without deferred
            changes that need another plan.
        errored: Whether planning failed part way.
        variables: The value of each root module variable.
        changes: The `resource_changes` entries.
        drift: The `resource_drift` entries; empty when absent.
    """

    format_version: str
    terraform_version: str
    applyable: bool
    complete: bool
    errored: bool
    variables: Mapping[str, Any]
    changes: tuple[Change, ...]
    drift: tuple[Change, ...] = ()

    @property
    def format_major(self) -> str:
        """Returns the major version of the format, such as `1`."""
        return self.format_version.split(".", 1)[0]

    def variable(self, name: str) -> Any:
        """Returns the planned value of a root variable, or None.

        Args:
            name: The variable name, such as `bootstrap_user`.
        """
        return self.variables.get(name)


def _string(entry: Mapping[str, Any], key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str):
        raise PlanError(f"{where} has no string {key!r}")
    return value


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _actions(change: Mapping[str, Any], address: str) -> tuple[str, ...]:
    actions = change.get("actions")
    if not isinstance(actions, list) or not all(
        isinstance(action, str) for action in actions
    ):
        raise PlanError(f"{address} has no action list")
    found = tuple(actions)
    if found not in ACTIONS:
        raise PlanError(
            f"{address} has the unknown actions {list(found)}; stellar "
            "refuses plans it cannot classify"
        )
    return found


def _importing_id(change: Mapping[str, Any]) -> str | None:
    importing = change.get("importing")
    if not isinstance(importing, Mapping):
        return None
    # An import by resource identity carries no `id`.
    return str(importing.get("id") or "")


def _replace_paths(change: Mapping[str, Any]) -> tuple[tuple[Any, ...], ...]:
    found = change.get("replace_paths") or ()
    return tuple(
        tuple(path) if isinstance(path, list) else (path,) for path in found
    )


def _change(entry: Any, where: str) -> Change:
    if not isinstance(entry, Mapping):
        raise PlanError(f"{where} is not an object")
    address = _string(entry, "address", where)
    change = entry.get("change")
    if not isinstance(change, Mapping):
        raise PlanError(f"{address} has no change object")
    index = entry.get("index")
    return Change(
        address=address,
        module_address=_optional_string(entry.get("module_address")),
        type=_string(entry, "type", address),
        name=_string(entry, "name", address),
        index=index if isinstance(index, int | str) else None,
        mode=_string(entry, "mode", address),
        actions=_actions(change, address),
        action_reason=_optional_string(entry.get("action_reason")),
        importing_id=_importing_id(change),
        replace_paths=_replace_paths(change),
        before=change.get("before"),
        after=change.get("after"),
        after_unknown=change.get("after_unknown"),
        previous_address=_optional_string(entry.get("previous_address")),
        deposed=_optional_string(entry.get("deposed")),
    )


def _changes(doc: Mapping[str, Any], key: str) -> tuple[Change, ...]:
    entries = doc.get(key)
    if entries is None:
        return ()
    if not isinstance(entries, list):
        raise PlanError(f"{key} is not a list")
    return tuple(
        _change(entry, f"{key}[{number}]")
        for number, entry in enumerate(entries)
    )


def _flag(doc: Mapping[str, Any], key: str, default: bool) -> bool:
    value = doc.get(key, default)
    if not isinstance(value, bool):
        raise PlanError(f"{key} is not a boolean")
    return value


def parse(doc: Any) -> Plan:
    """Parses a `terraform show -json` plan document.

    Args:
        doc: The decoded JSON document.

    Returns:
        The plan.

    Raises:
        PlanError: If the document is no plan, uses another major format
            version, or holds an action list stellar does not know.
    """
    if not isinstance(doc, Mapping):
        raise PlanError("The plan document is not a JSON object")
    format_version = _string(doc, "format_version", "The plan document")
    major = format_version.split(".", 1)[0]
    if major != FORMAT_MAJOR:
        raise PlanError(
            f"The plan uses JSON format {format_version}; stellar reads "
            f"format {FORMAT_MAJOR}.x only"
        )
    variables = doc.get("variables")
    variables = {} if variables is None else variables
    if not isinstance(variables, Mapping):
        raise PlanError("variables is not an object")
    return Plan(
        format_version=format_version,
        terraform_version=str(doc.get("terraform_version") or ""),
        applyable=_flag(doc, "applyable", True),
        complete=_flag(doc, "complete", True),
        errored=_flag(doc, "errored", False),
        variables={
            name: entry.get("value") if isinstance(entry, Mapping) else None
            for name, entry in variables.items()
        },
        changes=_changes(doc, "resource_changes"),
        drift=_changes(doc, "resource_drift"),
    )


def summary(plan: Plan) -> dict[str, int]:
    """Returns the number of changes per category in `SUMMARY_KEYS` order.

    Every change counts once under its action; an importing change also
    counts under `import`.

    Args:
        plan: The plan.
    """
    counts = collections.Counter(change.action for change in plan.changes)
    counts["import"] = sum(change.importing for change in plan.changes)
    return {key: counts.get(key, 0) for key in SUMMARY_KEYS}
