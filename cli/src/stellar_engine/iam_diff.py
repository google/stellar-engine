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

"""Organization IAM policies, the target Stage 0 sets, and their diff.

Stage 0 manages organization roles authoritatively: each apply replaces
the members of such a role with the ones it declares, so it removes every
grant made outside Terraform. This module models a live policy in the
`gcloud organizations get-iam-policy --format=json` shape, builds the
target from a saved plan or, before any plan exists, from the repository,
and lists the grants an apply removes. Snapshots keep the live policy in
that same shape without its etag, which their metadata keeps, so
`gcloud organizations set-iam-policy` restores one by hand even after the
policy changed.
"""

from collections.abc import Callable, Iterable, Mapping
import dataclasses
import datetime
import json
import pathlib
import re
from typing import Any

from stellar_engine import fsutil
from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.render import writer
from stellar_engine.terraform import plan as plan_lib

BINDING_TYPE = "google_organization_iam_binding"
AUDIT_CONFIG_TYPE = "google_organization_iam_audit_config"
MEMBER_TYPE = "google_organization_iam_member"
# A principal that IAM deleted keeps its grants under this prefix until
# the binding changes; nothing can grant it again, so diffs ignore it.
_DELETED = "deleted:"
# Plan actions that leave the live policy as it is.
_UNCHANGED_ACTIONS = ("no-op", "read", "forget")
# Attributes whose unknown value hides what a binding or config sets.
_BINDING_FIELDS = ("members", "role", "condition")
_MEMBER_FIELDS = ("member", "role", "condition")
_AUDIT_FIELDS = ("service", "audit_log_config")
_REASON_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_SNAPSHOT_SUFFIX = ".json"
_META_SUFFIX = ".meta.json"


class UnknownMembersError(Exception):
    """Raised when a plan leaves an IAM binding unknown until apply.

    Attributes:
        address: Resource address of the binding or audit config.
    """

    def __init__(self, address: str):
        """Initializes the error with the resource address."""
        self.address = address
        super().__init__(
            f"The plan leaves {address} unknown until apply, so the IAM "
            "review cannot list the grants the apply removes."
        )


class SnapshotError(Exception):
    """Raised when an IAM snapshot cannot be read or written."""


@dataclasses.dataclass(frozen=True)
class Condition:
    """An IAM condition, which is part of the identity of a binding.

    Attributes:
        title: Condition title.
        expression: CEL expression.
        description: Optional description; None when empty.
    """

    title: str
    expression: str
    description: str | None = None

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> Condition:
        """Reads a condition in the IAM or Terraform JSON shape.

        Args:
            data: Mapping with `title`, `expression` and an optional
                `description`.

        Raises:
            ValueError: If a field has the wrong type.
        """
        if not isinstance(data, Mapping):
            raise ValueError("An IAM condition must be a JSON object.")
        return cls(
            _text(data, "title"),
            _text(data, "expression"),
            _optional_text(data, "description") or None,
        )

    def to_json(self) -> dict[str, str]:
        """Returns the condition in the IAM JSON shape."""
        found = {"expression": self.expression, "title": self.title}
        if self.description:
            found["description"] = self.description
        return found


@dataclasses.dataclass(frozen=True)
class BindingKey:
    """Identifies one binding of a policy: a role and its condition.

    Terraform replaces an unconditional binding only with the unconditional
    binding of the same role, and a conditional one only with the binding
    of the same role and condition, so both make up the key.

    Attributes:
        role: Role name, such as `roles/browser`.
        condition: Condition, or None for an unconditional binding.
    """

    role: str
    condition: Condition | None = None

    def sort_key(self) -> tuple[str, str]:
        """Returns a key that orders bindings by role, then condition."""
        return self.role, self.condition.title if self.condition else ""

    def __str__(self) -> str:
        """Returns the role, with the condition title when it has one."""
        if self.condition is None:
            return self.role
        return f"{self.role} (condition {self.condition.title})"


@dataclasses.dataclass(frozen=True, order=True)
class AuditLogConfig:
    """One log type of an audit config, with its exempted members.

    Attributes:
        log_type: Log type, such as `ADMIN_READ`.
        exempted_members: Sorted principals exempted from the log type.
    """

    log_type: str
    exempted_members: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        """Returns the config in the IAM JSON shape."""
        found: dict[str, Any] = {"logType": self.log_type}
        if self.exempted_members:
            found["exemptedMembers"] = list(self.exempted_members)
        return found


AuditConfigs = tuple[AuditLogConfig, ...]


@dataclasses.dataclass(frozen=True)
class Policy:
    """An IAM policy in the shape that `get-iam-policy` returns.

    Attributes:
        version: Policy version; 3 when bindings carry conditions.
        etag: Base64 etag of the read, which a write sends back.
        bindings: Members of each binding.
        audit_configs: Sorted log type configs of each service.
    """

    version: int = 1
    etag: str = ""
    bindings: Mapping[BindingKey, frozenset[str]] = dataclasses.field(
        default_factory=dict
    )
    audit_configs: Mapping[str, AuditConfigs] = dataclasses.field(
        default_factory=dict
    )

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> Policy:
        """Reads a policy in the gcloud and API JSON shape.

        Bindings with the same role and condition merge, and absent fields
        take their API defaults.

        Args:
            data: Mapping with `version`, `etag`, `bindings` and
                `auditConfigs`, any of them optional.

        Raises:
            ValueError: If the data does not have that shape.
        """
        if not isinstance(data, Mapping):
            raise ValueError("An IAM policy must be a JSON object.")
        bindings: dict[BindingKey, frozenset[str]] = {}
        for item in _objects(data, "bindings"):
            condition = item.get("condition")
            key = BindingKey(
                _text(item, "role"),
                None if condition is None else Condition.from_json(condition),
            )
            members = frozenset(_texts(item, "members"))
            bindings[key] = bindings.get(key, frozenset()) | members
        audit_configs = {
            _text(item, "service"): _audit_configs(
                AuditLogConfig(
                    _text(config, "logType"),
                    tuple(_texts(config, "exemptedMembers")),
                )
                for config in _objects(item, "auditLogConfigs")
            )
            for item in _objects(data, "auditConfigs")
        }
        return cls(
            version=int(data.get("version") or 1),
            etag=str(data.get("etag") or ""),
            bindings=bindings,
            audit_configs=audit_configs,
        )

    def to_json(self) -> dict[str, Any]:
        """Returns the policy in the gcloud and API JSON shape."""
        found: dict[str, Any] = {"version": self.version}
        if self.etag:
            found["etag"] = self.etag
        found["bindings"] = [
            _binding_json(key, members)
            for key, members in self.bindings.items()
        ]
        if self.audit_configs:
            found["auditConfigs"] = [
                {
                    "service": service,
                    "auditLogConfigs": [config.to_json() for config in configs],
                }
                for service, configs in self.audit_configs.items()
            ]
        return found


@dataclasses.dataclass(frozen=True)
class Target:
    """What an apply sets on the bindings and audit configs it manages.

    Attributes:
        bindings: Members each managed binding ends with. None when the
            apply deletes the binding, which removes every member.
        audit_configs: Log type configs each managed service ends with.
            None when the apply deletes the config.
        removed_members: Additive grants that the apply deletes. Deleting
            one removes the member from the live binding, even when someone
            granted it outside Terraform too.
        added_members: Additive grants that the apply creates.
    """

    bindings: Mapping[BindingKey, frozenset[str] | None] = dataclasses.field(
        default_factory=dict
    )
    audit_configs: Mapping[str, AuditConfigs | None] = dataclasses.field(
        default_factory=dict
    )
    removed_members: frozenset[Grant] = frozenset()
    added_members: frozenset[Grant] = frozenset()

    @property
    def empty(self) -> bool:
        """Returns whether the apply leaves organization IAM alone."""
        return not (
            self.bindings
            or self.audit_configs
            or self.removed_members
            or self.added_members
        )


@dataclasses.dataclass(frozen=True)
class Grant:
    """One member of one binding.

    Attributes:
        key: The binding.
        member: Principal, such as `user:admin@example.com`.
        additive: Whether an additive `google_organization_iam_member`
            grants it, rather than an authoritative binding.
    """

    key: BindingKey
    member: str
    additive: bool = False

    def sort_key(self) -> tuple[str, str, str]:
        """Returns a key that orders grants by binding, then member."""
        return *self.key.sort_key(), self.member

    def __str__(self) -> str:
        """Returns `<role> <member>`, plus the condition title if any."""
        if self.key.condition is None:
            return f"{self.key.role} {self.member}"
        return (
            f"{self.key.role} {self.member} "
            f"(condition {self.key.condition.title})"
        )


@dataclasses.dataclass(frozen=True)
class AuditOverwrite:
    """An existing audit config that the apply replaces or deletes.

    Attributes:
        service: Service, such as `allServices`.
        live: The configs the organization has now.
        target: The configs after the apply; None when it deletes them.
    """

    service: str
    live: AuditConfigs
    target: AuditConfigs | None


@dataclasses.dataclass(frozen=True)
class Diff:
    """How an apply changes the live organization policy.

    Grants of deleted principals never count, because nothing can grant
    them again.

    Attributes:
        removed: Live grants on managed bindings that the apply drops.
        added: Grants the apply makes that the policy lacks.
        kept_foreign: Live grants on managed bindings that the apply keeps,
            such as grants that `overrides.0-bootstrap.iam` lists.
        audit_overwrites: Live audit configs that the apply changes.
        conditional_replacements: Live conditional bindings whose members
            the apply rewrites.
    """

    removed: tuple[Grant, ...] = ()
    added: tuple[Grant, ...] = ()
    kept_foreign: tuple[Grant, ...] = ()
    audit_overwrites: tuple[AuditOverwrite, ...] = ()
    conditional_replacements: tuple[BindingKey, ...] = ()

    @property
    def needs_review(self) -> bool:
        """Returns whether the apply takes away access or audit logging."""
        return bool(
            self.removed
            or self.audit_overwrites
            or self.conditional_replacements
        )


@dataclasses.dataclass(frozen=True)
class SnapshotMeta:
    """Why and when a snapshot was taken, kept beside the policy file.

    Attributes:
        org_id: Organization ID of the policy.
        reason: Short slug such as `gate`, which names the file.
        taken: Time of the read.
        plan: Saved plan the snapshot reviewed, if any.
        engine_commit: Engine commit in use, if known.
        principal: Identity that took the snapshot, if known.
        etag: Etag of the read, which the policy file leaves out.
    """

    org_id: str
    reason: str
    taken: datetime.datetime
    plan: str | None = None
    engine_commit: str | None = None
    principal: str | None = None
    etag: str | None = None

    def to_json(self) -> dict[str, Any]:
        """Returns the metadata as JSON data with an ISO time."""
        data = dataclasses.asdict(self)
        data["taken"] = self.taken.astimezone(datetime.UTC).isoformat()
        return data

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> SnapshotMeta:
        """Reads metadata that `to_json` wrote.

        Raises:
            ValueError: If a field is missing or malformed.
        """
        if not isinstance(data, Mapping):
            raise ValueError("Snapshot metadata must be a JSON object.")
        return cls(
            org_id=_text(data, "org_id"),
            reason=_text(data, "reason"),
            taken=datetime.datetime.fromisoformat(_text(data, "taken")),
            plan=_optional_text(data, "plan"),
            engine_commit=_optional_text(data, "engine_commit"),
            principal=_optional_text(data, "principal"),
            etag=_optional_text(data, "etag"),
        )


@dataclasses.dataclass(frozen=True)
class Snapshot:
    """A policy snapshot read back from disk.

    Attributes:
        path: The policy file.
        policy: The policy it holds.
        meta: Its metadata, or None when the sidecar file is missing.
    """

    path: pathlib.Path
    policy: Policy
    meta: SnapshotMeta | None


def _optional_text(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"Field {key} must be a string, got {value!r}.")
    return value


def _text(data: Mapping[str, Any], key: str) -> str:
    value = _optional_text(data, key)
    if value is None:
        raise ValueError(f"Field {key} is missing.")
    return value


def _texts(data, key):
    values = data.get(key) or []
    if not isinstance(values, list) or not all(
        isinstance(value, str) for value in values
    ):
        raise ValueError(f"Field {key} must be a list of strings.")
    return values


def _objects(data, key):
    values = data.get(key) or []
    if not isinstance(values, list) or not all(
        isinstance(value, Mapping) for value in values
    ):
        raise ValueError(f"Field {key} must be a list of objects.")
    return values


def _audit_configs(configs: Iterable[AuditLogConfig]) -> AuditConfigs:
    """Sorts configs and their exempted members, so equal ones compare."""
    return tuple(
        sorted(
            AuditLogConfig(
                config.log_type, tuple(sorted(config.exempted_members))
            )
            for config in configs
        )
    )


def _binding_json(key, members):
    found: dict[str, Any] = {"role": key.role, "members": sorted(members)}
    if key.condition is not None:
        found["condition"] = key.condition.to_json()
    return found


def resolve_holder(
    holder: repo_lib.Holder,
    *,
    prefix: str | None,
    groups: Mapping[str, str],
    bootstrap_user: str | None,
    domain: str | None,
) -> str | None:
    """Resolves a Stage 0 role holder to the IAM member it grants.

    Args:
        holder: A holder from `Repo.authoritative_bindings`.
        prefix: The deployment prefix, which names the automation service
            accounts.
        groups: The group members by group key.
        bootstrap_user: The user of the first Stage 0 apply.
        domain: The organization domain.

    Returns:
        The member, or None when the inputs cannot name it.
    """
    match holder.kind:
        case repo_lib.HolderKind.GROUP if holder.key:
            return groups.get(holder.key)
        case repo_lib.HolderKind.SERVICE_ACCOUNT if prefix and holder.key:
            email = naming.automation_sa_email(prefix, holder.key)
            return naming.principal(naming.SERVICE_ACCOUNT, email)
        case repo_lib.HolderKind.BOOTSTRAP_USER if bootstrap_user:
            return naming.principal(naming.USER, bootstrap_user)
        case repo_lib.HolderKind.DOMAIN if domain:
            return naming.principal(naming.DOMAIN, domain)
    return None


def _put(target, key, value):
    """Records what one resource sets on a key.

    A value that a create sets wins over a delete of the same key, as in
    a replace that keeps the key, and two creates merge their members.
    """
    if key not in target or target[key] is None:
        target[key] = value
    elif value is not None:
        target[key] = target[key] | value


def _plan_key(values):
    condition = values.get("condition") or []
    return BindingKey(
        _text(values, "role"),
        Condition.from_json(condition[0]) if condition else None,
    )


def _plan_configs(values):
    return _audit_configs(
        AuditLogConfig(
            _text(config, "log_type"),
            tuple(_texts(config, "exempted_members")),
        )
        for config in values.get("audit_log_config") or []
    )


def _plan_change(change: plan_lib.Change, bindings, audit_configs, members):
    """Adds what one IAM change sets to the target.

    `members` holds the removed and the added additive grants, in that
    order.
    """
    is_binding = change.type == BINDING_TYPE
    unknown = change.after_unknown
    unknown = unknown if isinstance(unknown, Mapping) else {}
    before, after = change.before, change.after
    if change.type == MEMBER_TYPE:
        # The state holds what a delete removes, so only a grant that the
        # apply creates can be unknown, such as one to a new service
        # account. That grant cannot be live, and a replace to it counts
        # as a removal.
        removed, added = members
        if change.deletes and before:
            removed.add(Grant(_plan_key(before), _text(before, "member"), True))
        known = not any(
            plan_lib.has_unknown(unknown.get(field)) for field in _MEMBER_FIELDS
        )
        if after and known:
            added.add(Grant(_plan_key(after), _text(after, "member"), True))
        return
    fields = _BINDING_FIELDS if is_binding else _AUDIT_FIELDS
    if any(plan_lib.has_unknown(unknown.get(field)) for field in fields):
        raise UnknownMembersError(change.address)
    if is_binding:
        if change.deletes and before:
            _put(bindings, _plan_key(before), None)
        if after:
            members = frozenset(after.get("members") or ())
            _put(bindings, _plan_key(after), members)
        return
    if change.deletes and before:
        _put(audit_configs, _text(before, "service"), None)
    if after:
        audit_configs[_text(after, "service")] = _plan_configs(after)


def _iam_changes(plan: plan_lib.Plan) -> list[plan_lib.Change]:
    """Returns the managed organization IAM changes."""
    return [
        change
        for change in plan.changes
        if change.managed
        and change.type in (BINDING_TYPE, MEMBER_TYPE, AUDIT_CONFIG_TYPE)
    ]


def manages_iam(plan: plan_lib.Plan) -> bool:
    """Returns whether a saved plan manages organization IAM at all.

    A plan that only refreshes the bindings still manages them, so the
    deploy saves a snapshot of the live policy before applying it and
    `stellar iam restore` has a recent point to return to.

    Args:
        plan: The parsed saved plan.

    Returns:
        True when the plan holds any managed
        `google_organization_iam_binding`,
        `google_organization_iam_member` or
        `google_organization_iam_audit_config`, changed or not.
    """
    return bool(_iam_changes(plan))


def target_from_plan(plan: plan_lib.Plan) -> Target:
    """Returns what a saved plan sets on organization IAM.

    It reads every managed `google_organization_iam_binding`, whether the
    module names it `authoritative` or `bindings`, every additive
    `google_organization_iam_member`, and every
    `google_organization_iam_audit_config`. Deleting an additive member
    removes the member from the live binding, whoever granted it, so the
    target records those deletes. Changes that leave the live policy alone
    stay out.

    Args:
        plan: The parsed saved plan.

    Returns:
        The target. A binding with null members ends empty, and a delete
        or a replace that moves a binding to another key deletes the old
        key.

    Raises:
        UnknownMembersError: If a binding's members, role or condition, an
            additive member, or an audit config is unknown until apply,
            because then the removed grants cannot be listed.
        ValueError: If a change has a malformed role or condition.
    """
    bindings: dict[BindingKey, frozenset[str] | None] = {}
    audit_configs: dict[str, AuditConfigs | None] = {}
    removed: set[Grant] = set()
    added: set[Grant] = set()
    for change in _iam_changes(plan):
        if change.action not in _UNCHANGED_ACTIONS:
            _plan_change(change, bindings, audit_configs, (removed, added))
    return Target(bindings, audit_configs, frozenset(removed), frozenset(added))


def stage0_audit_configs(repo: repo_lib.Repo) -> dict[str, AuditConfigs]:
    """Returns the audit log configs Stage 0 sets on the organization.

    Args:
        repo: The engine checkout.

    Returns:
        The sorted configs of each service, as `Repo.audit_log_configs`
        reads them from `0-bootstrap/audit-logging.tf`.
    """
    return {
        service: _audit_configs(
            AuditLogConfig(log_type, exempted) for log_type, exempted in configs
        )
        for service, configs in repo.audit_log_configs().items()
    }


def target_from_repo(
    repo: repo_lib.Repo,
    resolve: Callable[[repo_lib.Holder], str | None],
    stage0_overrides: Mapping[str, Any],
    *,
    audit_configs: Mapping[str, AuditConfigs] | None = None,
) -> Target:
    """Returns what Stage 0 sets on organization IAM, before any plan.

    Preflight cannot plan, so it approximates the target from the
    authoritative bindings in `organization-iam.tf`, then merges the
    `iam` and `iam_by_principals` overrides the way `organization.tf`
    merges `var.iam` and `var.iam_by_principals`: both add members, and
    both can add authoritative roles of their own.

    Args:
        repo: The engine checkout.
        resolve: Resolves a holder to its member, None when the inputs
            cannot name it, such as `resolve_holder` with bound inputs.
        stage0_overrides: The Stage 0 overrides, whose `iam` maps a role to
            members and `iam_by_principals` maps a member to roles.
        audit_configs: Audit configs Stage 0 sets, as
            `stage0_audit_configs` returns them; None leaves them out.

    Returns:
        The target, with unconditional bindings only.
    """
    bindings: dict[BindingKey, set[str]] = {}
    for role, holders in repo.authoritative_bindings().items():
        members = bindings.setdefault(BindingKey(role), set())
        members.update(m for m in map(resolve, holders) if m is not None)
    for role, members in (stage0_overrides.get("iam") or {}).items():
        bindings.setdefault(BindingKey(role), set()).update(members)
    by_principals = stage0_overrides.get("iam_by_principals") or {}
    for member, roles in by_principals.items():
        for role in roles:
            bindings.setdefault(BindingKey(role), set()).add(member)
    return Target(
        {key: frozenset(members) for key, members in bindings.items()},
        dict(audit_configs or {}),
    )


def additive_key(grant: Grant) -> str:
    """Returns the Stage 0 key of an additive grant, `<role>-<member>`.

    Stage 0 keys its own additive grants the same way, so an override with
    this key keeps the resource the apply would otherwise delete.
    """
    return f"{grant.key.role}-{grant.member}"


def _mapping(parent: dict[str, Any], key: str) -> dict[str, Any]:
    """Returns `parent[key]`, replacing a missing or null value with {}."""
    value = parent.get(key)
    if not isinstance(value, dict):
        if value is not None:
            raise ValueError(
                f"overrides.{paths.BOOTSTRAP}.{key} must be a mapping."
            )
        value = parent[key] = {}
    return value


def keep_in_overrides(data: dict[str, Any], grants: Iterable[Grant]) -> None:
    """Adds grants to the Stage 0 overrides of the answers, in place.

    An authoritative grant goes to `overrides.0-bootstrap.iam`, which
    Stage 0 merges into its authoritative bindings. An additive grant goes
    to `overrides.0-bootstrap.iam_bindings_additive` under the key Stage 0
    gives it, so the next apply keeps the resource instead of deleting
    it; adding the member to the authoritative binding instead would drop
    every other member of that role. New entries are appended, which
    keeps the comments of the answers file; a role whose member list
    grows loses the comments inside that list. Members compare without
    case, as the provider compares them.

    Args:
        data: Answer data, as `config.answers.update` passes it to its
            change function.
        grants: Unconditional grants; the overrides hold no conditions.

    Raises:
        ValueError: If an override that must be a mapping or a member list
            is something else.
    """
    stage0 = _mapping(_mapping(data, "overrides"), paths.BOOTSTRAP)
    for grant in grants:
        if grant.additive:
            additive = _mapping(stage0, "iam_bindings_additive")
            additive.setdefault(
                additive_key(grant),
                {"member": grant.member, "role": grant.key.role},
            )
            continue
        iam = _mapping(stage0, "iam")
        members = iam.get(grant.key.role)
        if members is None:
            members = iam[grant.key.role] = []
        if not isinstance(members, list):
            raise ValueError(
                f"overrides.{paths.BOOTSTRAP}.iam.{grant.key.role} must be "
                "a list of members."
            )
        if grant.member.casefold() not in {
            str(member).casefold() for member in members
        }:
            members.append(grant.member)


def _live_members(members) -> dict[str, str]:
    """Maps each member without case to its spelling, without deleted ones.

    The provider compares members without case, so `group:Admins@x` and
    `group:admins@x` are one member to Terraform.
    """
    return {
        member.casefold(): member
        for member in sorted(members, reverse=True)
        if not member.startswith(_DELETED)
    }


def _audit_overwrites(live, target):
    return tuple(
        AuditOverwrite(service, live.audit_configs[service], configs)
        for service, configs in sorted(target.audit_configs.items())
        if service in live.audit_configs
        and live.audit_configs[service] != configs
    )


def diff(live: Policy, target: Target) -> Diff:
    """Compares the live policy with what an apply sets.

    Only the bindings and audit configs the target manages change; the
    apply leaves every other binding of the live policy alone.

    Args:
        live: The live organization policy.
        target: What the apply sets.

    Returns:
        The grants removed, added and kept, sorted by role, condition and
        member, and the audit configs and conditional bindings the apply
        rewrites. Members compare without case and keep their live
        spelling.
    """
    removed, added, kept, conditional = [], [], [], []
    for key, members in target.bindings.items():
        current = _live_members(live.bindings.get(key, ()))
        wanted = _live_members(members or ())
        removed += [Grant(key, current[m]) for m in current.keys() - wanted]
        added += [Grant(key, wanted[m]) for m in wanted.keys() - current]
        kept += [Grant(key, current[m]) for m in current.keys() & wanted]
        if (
            key.condition is not None
            and current
            and current.keys() != wanted.keys()
        ):
            conditional.append(key)
    removed += _removed_members(live, target)
    added += _added_members(live, target)
    return Diff(
        removed=tuple(sorted(removed, key=Grant.sort_key)),
        added=tuple(sorted(added, key=Grant.sort_key)),
        kept_foreign=tuple(sorted(kept, key=Grant.sort_key)),
        audit_overwrites=_audit_overwrites(live, target),
        conditional_replacements=tuple(
            sorted(conditional, key=BindingKey.sort_key)
        ),
    )


def _kept_by_target(target: Target, grant: Grant) -> bool:
    """Returns whether the apply still grants the member of a grant."""
    member = grant.member.casefold()
    recreated = {
        (other.key, other.member.casefold()) for other in target.added_members
    }
    wanted = target.bindings.get(grant.key) or ()
    return (grant.key, member) in recreated or member in {
        other.casefold() for other in wanted
    }


def _removed_members(live: Policy, target: Target) -> list[Grant]:
    """Returns the live additive grants that the apply deletes.

    A delete that the same apply creates again, as in a replace that
    keeps the member, removes nothing, and neither does a delete of a
    member that an authoritative binding of the target keeps or that a
    binding of the target already reports.
    """
    found = []
    for grant in target.removed_members:
        if grant.key in target.bindings or _kept_by_target(target, grant):
            continue
        current = _live_members(live.bindings.get(grant.key, ()))
        spelling = current.get(grant.member.casefold())
        if spelling is not None:
            found.append(Grant(grant.key, spelling, additive=True))
    return found


def _added_members(live: Policy, target: Target) -> list[Grant]:
    """Returns the additive grants that the live policy lacks."""
    found = []
    for grant in target.added_members:
        if grant.key in target.bindings:
            continue
        current = _live_members(live.bindings.get(grant.key, ()))
        if grant.member.casefold() not in current:
            found.append(grant)
    return found


def target_from_policy(after: Policy, *, keys_of: Policy) -> Target:
    """Returns the target that turns one policy into another.

    Every binding and audit config of either policy is managed and ends as
    `after` has it, so `diff(keys_of, ...)` lists what changed between two
    snapshots and `diff(live, ...)` what a restore of `after` changes.

    Args:
        after: The policy to end with.
        keys_of: The other policy, whose bindings and audit configs the
            target also manages, so the ones `after` lacks end empty.
    """
    keys = {*keys_of.bindings, *after.bindings}
    services = {*keys_of.audit_configs, *after.audit_configs}
    return Target(
        {key: after.bindings.get(key, frozenset()) for key in keys},
        {service: after.audit_configs.get(service) for service in services},
    )


def _audit_detail(item: AuditOverwrite) -> str:
    """Says how an apply changes the live configs of one service."""
    verb = "deleted" if item.target is None else "replaced"
    return f"{len(item.live)} live log type configs are {verb}"


def rows(found: Diff, *, added: bool = False) -> list[tuple[str, str, str]]:
    """Returns the table rows of a diff: the change, binding and detail.

    The deploy's IAM review and `stellar iam diff` print the same rows, so
    one change reads the same in both.

    Args:
        found: The diff.
        added: Whether to list the added grants, which the review counts
            only.

    Returns:
        The removed grants, the added ones when asked, the audit config
        overwrites and the conditional bindings the apply rewrites.
    """
    listed = [
        ("removed", str(grant.key), grant.member) for grant in found.removed
    ]
    if added:
        listed += [
            ("added", str(grant.key), grant.member) for grant in found.added
        ]
    listed += [
        ("audit", item.service, _audit_detail(item))
        for item in found.audit_overwrites
    ]
    listed += [
        ("rewrite", str(key), "conditional members change")
        for key in found.conditional_replacements
    ]
    return listed


def _meta_path(path):
    return path.with_name(
        path.name.removesuffix(_SNAPSHOT_SUFFIX) + _META_SUFFIX
    )


def _snapshot_files(directory):
    return sorted(
        (
            path
            for path in directory.glob(f"*{_SNAPSHOT_SUFFIX}")
            if not path.name.endswith(_META_SUFFIX)
        ),
        key=lambda path: path.name.removesuffix(_SNAPSHOT_SUFFIX),
    )


def snapshot_meta(
    repository: repo_lib.Repo,
    *,
    org_id: str,
    reason: str,
    taken: datetime.datetime,
    principal: str | None,
    plan: pathlib.Path | None = None,
) -> SnapshotMeta:
    """Returns the metadata of a snapshot that this engine takes.

    `stellar iam snapshot` and the deploy steps share it, so every
    snapshot records the engine commit the same way.

    Args:
        repository: The engine checkout, whose commit the metadata keeps.
        org_id: Organization ID of the policy.
        reason: Short slug such as `gate`, which names the file.
        taken: Time of the read.
        principal: Identity that took the snapshot, if known.
        plan: Saved plan the snapshot reviews, if any.
    """
    provenance = repository.provenance()
    return SnapshotMeta(
        org_id=org_id,
        reason=reason,
        taken=taken,
        plan=None if plan is None else str(plan),
        engine_commit=None if provenance is None else provenance.commit,
        principal=principal,
    )


def write_snapshot(
    env: paths.EnvPaths, policy: Policy, meta: SnapshotMeta
) -> pathlib.Path:
    """Saves a policy and its metadata under `env.iam_snapshots`.

    The policy file `<time>-<reason>.json` holds the policy in the gcloud
    JSON shape without its etag, so `gcloud organizations set-iam-policy
    <org> <file>` restores it by hand: gcloud sends the etag of a file,
    and setIamPolicy rejects a stale one, which a restore always has.
    `<time>-<reason>.meta.json` beside it holds the metadata and the etag.
    A second snapshot in the same second gets a counter.

    Args:
        env: The environment.
        policy: The live policy.
        meta: Its metadata; `meta.taken` and `meta.reason` name the file,
            and the etag of the policy replaces `meta.etag`.

    Returns:
        The policy file, mode 0600, in a 0700 directory.

    Raises:
        ValueError: If the reason is not a lowercase slug.
    """
    if not _REASON_RE.match(meta.reason):
        raise ValueError(f"Snapshot reason {meta.reason!r} is not a slug.")
    paths.make_private_dir(env.iam_snapshots)
    base = f"{writer.stamp(meta.taken)}-{meta.reason}"
    counter = 0
    while True:
        name = base if counter == 0 else f"{base}-{counter}"
        path = env.iam_snapshots / f"{name}{_SNAPSHOT_SUFFIX}"
        if not path.exists() and not _meta_path(path).exists():
            break
        counter += 1
    fsutil.write_private_json(
        path, dataclasses.replace(policy, etag="").to_json()
    )
    meta = dataclasses.replace(meta, etag=policy.etag or None)
    fsutil.write_private_json(_meta_path(path), meta.to_json())
    return path


def read_snapshot(path: pathlib.Path) -> Snapshot:
    """Reads a policy file and the metadata beside it.

    Args:
        path: A policy file that `write_snapshot` wrote, or any file in
            the gcloud `get-iam-policy --format=json` shape.

    Returns:
        The snapshot; its metadata is None without a sidecar file.

    Raises:
        SnapshotError: If a file cannot be read or is malformed.
    """
    path = pathlib.Path(path)
    try:
        policy = Policy.from_json(json.loads(path.read_text(encoding="utf-8")))
        meta_text = fsutil.read_text_or_none(_meta_path(path))
        meta = (
            None
            if meta_text is None
            else SnapshotMeta.from_json(json.loads(meta_text))
        )
    except (OSError, TypeError, ValueError) as error:
        raise SnapshotError(
            f"Cannot read the snapshot {path}: {error}"
        ) from error
    return Snapshot(path, policy, meta)


def latest_snapshot(env: paths.EnvPaths) -> Snapshot | None:
    """Returns the newest snapshot of an environment, or None.

    Raises:
        SnapshotError: If the newest snapshot cannot be read.
    """
    if not env.iam_snapshots.is_dir():
        return None
    files = _snapshot_files(env.iam_snapshots)
    return read_snapshot(files[-1]) if files else None
