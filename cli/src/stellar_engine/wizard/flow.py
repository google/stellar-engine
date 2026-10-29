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

"""The sections of the `stellar init` wizard.

Each section asks for one group of answers, with the current answer, or a
discovered value, as the default so Enter keeps it. Values that Terraform
derives, such as the KMS protection level, are stored only when the
operator picks something else, so a later regime change recomputes them.
After the sections, the answers are validated and the sections that own a
failing field are asked again.
"""

from collections.abc import Callable, Iterable, Mapping
import copy
import dataclasses
import re
import typing
from typing import Annotated, Any

import pydantic

from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import derive
from stellar_engine.config import models
from stellar_engine.config import validate
from stellar_engine.preflight import regions
from stellar_engine.wizard import discovery
from stellar_engine.wizard import prompts

# Rounds of re-asking after the first pass before the wizard gives up.
MAX_ROUNDS = 3

# `0-bootstrap/main.tf` local.principals passes typed values through.
_PRINCIPAL_RE = re.compile(naming.PRINCIPAL_TYPE_RE.pattern + r"\S+$")
_KMS_LEVELS: tuple[str, ...] = typing.get_args(
    typing.get_args(
        models.Answers.model_fields["kms_protection_level"].annotation
    )[0]
)


class WizardError(Exception):
    """Raised when the answers stay invalid after the re-ask rounds.

    Attributes:
        problems: The remaining problems, one sentence each.
    """

    def __init__(self, problems: list[str]):
        """Initializes the error with the remaining problems."""
        self.problems = problems
        super().__init__(
            "The answers are still invalid:\n"
            + "\n".join(f"- {problem}" for problem in problems)
        )


@dataclasses.dataclass(frozen=True)
class _Context:
    prompter: prompts.Prompter
    repo: repo_lib.Repo
    discovered: discovery.Discovered


def _get(data, path, default=None) -> Any:
    value = data
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def _put(data, path, value):
    """Sets a dotted path, or removes it when the value is None or empty."""
    keys = path.split(".")
    target = data
    for key in keys[:-1]:
        target = target.setdefault(key, {})
    if value is None or value == {}:
        target.pop(keys[-1], None)
    else:
        target[keys[-1]] = value


def _default_envs():
    return {key: {} for key in models.Resman().envs}


def _env_keys(data):
    envs = _get(data, "resman.envs")
    return list(_default_envs() if envs is None else envs)


def _group_principal(data, ctx, key):
    """Returns a Stage 0 group principal, as `derive.group_principal`."""
    name = naming.group_name(
        data.get("groups") or {}, ctx.repo.default_groups(), key
    )
    return naming.group_principal(name, _get(data, "organization.domain", ""))


def _created_stage0_projects(data, ctx):
    """Returns the Stage 0 projects Stage 0 creates, as `derive` does."""
    return ctx.repo.created_stage0_projects(
        no_iam=bool(_get(data, "billing.no_iam", False)),
        is_org_level=bool(_get(data, "billing.is_org_level", True)),
    )


def _field(model, name, problem):
    """Returns a validator that applies the constraints of a model field.

    The prompt then accepts exactly what the model accepts, without a copy
    of its pattern.
    """
    info = model.model_fields[name]
    adapter = pydantic.TypeAdapter(Annotated[(str, *info.metadata)])

    def check(text):
        try:
            adapter.validate_python(text)
        except pydantic.ValidationError:
            return problem
        return None

    return check


def _matches(pattern, problem):
    def check(text):
        return None if pattern.match(text) else problem

    return check


def _email(optional=False):
    def check(text):
        if optional and not text:
            return None
        if re.match(models.EMAIL_PATTERN, text):
            return None
        return "Enter an email address such as admin@example.com."

    return check


def _split(text):
    return [item.strip() for item in text.split(",") if item.strip()]


def _choose(ctx, message, current, options, labels, check):
    """Asks for a value, as a choice when discovery found several.

    Args:
        ctx: Wizard context.
        message: Prompt message.
        current: Current answer, which is the default when set.
        options: Discovered values.
        labels: Note line for each discovered value.
        check: Validator for typed text.
    """
    if current is None and len(options) > 1:
        for label in labels:
            ctx.prompter.note(label)
        return ctx.prompter.select(message, list(options))
    default = current or (options[0] if options else None)
    return ctx.prompter.text(message, default=default, validate=check)


def ask_prefix(data: dict, ctx: _Context) -> None:
    """Asks for the resource prefix.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    limit = ctx.repo.prefix_max_length()

    def check(text):
        if not re.match(models.PREFIX_PATTERN, text) or len(text) > limit:
            return (
                f"Use 1 to {limit} lowercase letters and digits, starting "
                "with a letter."
            )
        return None

    data["prefix"] = ctx.prompter.text(
        f"Resource prefix, at most {limit} characters",
        default=data.get("prefix"),
        validate=check,
    )


def ask_organization(data: dict, ctx: _Context) -> None:
    """Asks for the organization ID, domain and customer ID.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    orgs = {org.org_id: org for org in ctx.discovered.organizations}
    current = _get(data, "organization.id")
    current = None if current is None else str(current)
    org_id = _choose(
        ctx,
        "Organization ID",
        current,
        list(orgs),
        [f"{org.org_id}  {org.domain}" for org in orgs.values()],
        _field(models.Organization, "id", "Enter the numeric organization ID."),
    )
    found = orgs.get(org_id)
    # Keep the current domain and customer ID unless the org changed.
    keep = org_id == current or found is None
    domain = _get(data, "organization.domain") if keep else None
    customer = _get(data, "organization.customer_id") if keep else None
    organization = {"id": org_id}
    organization["domain"] = ctx.prompter.text(
        "Organization domain",
        default=domain or (found.domain if found else None),
        validate=lambda text: None if text else "Enter the domain.",
    )
    organization["customer_id"] = ctx.prompter.text(
        "Cloud Identity customer ID",
        default=customer or (found.customer_id if found else None),
        validate=_field(
            models.Organization,
            "customer_id",
            "Enter an ID such as C01234567.",
        ),
    )
    data["organization"] = organization


def ask_billing(data: dict, ctx: _Context) -> None:
    """Asks for the billing account and how Stage 0 manages its IAM.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    accounts = [
        account.account_id
        for account in ctx.discovered.billing_accounts
        if account.is_open
    ]
    billing = dict(data.get("billing") or {})
    billing["account_id"] = _choose(
        ctx,
        "Billing account ID",
        billing.get("account_id"),
        accounts,
        accounts,
        _field(
            models.Billing,
            "account_id",
            "Enter an ID such as 000000-AAAAAA-BBBBBB.",
        ),
    )
    billing["is_org_level"] = ctx.prompter.confirm(
        "Does the billing account belong to this organization?",
        default=billing.get("is_org_level", True),
    )
    billing["no_iam"] = ctx.prompter.confirm(
        "Skip billing IAM in Stage 0, for a shared billing account you "
        "cannot administer?",
        default=billing.get("no_iam", False),
    )
    billing["external_grant"] = ctx.prompter.confirm(
        "Does someone outside Terraform grant billing access before "
        "Stages 1 to 3?",
        default=billing.get("external_grant", False),
    )
    data["billing"] = billing


def _sync_stage0_imports(data, ctx, enabled):
    """Rewrites the Stage 0 project import entries.

    Entries for other addresses are kept. With `enabled`, every Stage 0
    project that Stage 0 creates for these answers gets an import of its
    derived project ID.

    Returns:
        Whether the entries changed.
    """
    imports = copy.deepcopy(data.get("imports") or {})
    stage = dict(imports.get(paths.BOOTSTRAP) or {})
    before = dict(stage)
    for project in ctx.repo.stage0_projects():
        stage.pop(project.address, None)
    if enabled:
        prefix = data.get("prefix", "")
        for project in _created_stage0_projects(data, ctx):
            stage[project.address] = naming.stage0_project_id(
                prefix, project.name
            )
    _put(imports, paths.BOOTSTRAP, stage or None)
    _put(data, "imports", imports or None)
    return stage != before


def _has_stage0_imports(data, ctx):
    stage = _get(data, f"imports.{paths.BOOTSTRAP}", {}) or {}
    return any(
        project.address in stage for project in ctx.repo.stage0_projects()
    )


def _note_imports(data, ctx):
    stage = _get(data, f"imports.{paths.BOOTSTRAP}", {}) or {}
    created = _created_stage0_projects(data, ctx)
    for project in ctx.repo.stage0_projects():
        if project.address in stage:
            ctx.prompter.note(
                f"  import {project.address} = {stage[project.address]}"
            )
        elif project not in created:
            ctx.prompter.note(
                f"  Stage 0 creates {project.address} only when "
                f"{repo_lib.BILLING_EXPORT_CONDITION}, "
                "so Stage 0 imports nothing for it."
            )


def ask_bootstrap(data: dict, ctx: _Context) -> None:
    """Asks for the bootstrap project and whether Stage 0 projects exist.

    Organizations where only a human can link billing pre-create the
    Stage 0 projects, so Stage 0 imports them instead of creating them,
    and the section then asks whether a Stage 0 destroy keeps them.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    data["bootstrap_project"] = ctx.prompter.text(
        "Bootstrap project ID",
        default=data.get("bootstrap_project") or ctx.discovered.gcloud_project,
        validate=_field(
            models.Answers,
            "bootstrap_project",
            "Enter a project ID such as example-bootstrap.",
        ),
    )
    precreated = ctx.prompter.confirm(
        "Do the Stage 0 projects exist already, so Stage 0 imports them?",
        default=_has_stage0_imports(data, ctx),
    )
    _sync_stage0_imports(data, ctx, precreated)
    if precreated:
        ctx.prompter.note("Stage 0 imports these pre-created projects:")
        _note_imports(data, ctx)
        # Someone else created these projects, so a Stage 0 destroy keeps
        # them unless the operator says otherwise.
        data["keep_imported_projects"] = ctx.prompter.confirm(
            "Keep these projects when Stage 0 is destroyed?",
            default=data.get("keep_imported_projects", True),
        )


def ask_compliance(data: dict, ctx: _Context) -> None:
    """Asks for the Assured Workloads regime.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    compliance = dict(data.get("compliance") or {})
    # Regimes with a region table, the ones Stellar Engine targets, come
    # first, so a fresh run defaults to one of them.
    names = ctx.repo.regime_names()
    targeted = [str(regime) for regime in regions.SUPPORTED_REGIONS]
    choices = [name for name in targeted if name in names]
    choices += [name for name in names if name not in choices]
    compliance["regime"] = ctx.prompter.select(
        "Compliance regime", choices, default=compliance.get("regime")
    )
    data["compliance"] = compliance


def ask_region(data: dict, ctx: _Context) -> None:
    """Asks for the region, offering only the regions of the regime.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    compliance = dict(data.get("compliance") or {})
    regime = compliance.get("regime", "")
    allowed = regions.supported_regions(regime)
    current = data.get("region")
    if allowed and not compliance.get("allow_unlisted_region"):
        choices = sorted(allowed)
        if current and current not in allowed:
            ctx.prompter.note(
                f"Region {current} is not listed for {regime}; pick another."
            )
        region = ctx.prompter.select(
            f"Region for {regime}", choices, default=current
        )
    else:
        if not allowed:
            ctx.prompter.note(
                f"No region table for {regime}; check {regions.LOCATIONS_DOC}."
            )
        region = ctx.prompter.text(
            "Region",
            default=current,
            validate=lambda text: None if text else "Enter a region.",
        )
    data["region"] = region
    location = ctx.prompter.text(
        "Assured Workloads location",
        default=compliance.get("location") or region,
        validate=lambda text: None if text else "Enter a location.",
    )
    # The location defaults to the region, so only a different one is kept.
    compliance["location"] = None if location == region else location
    _put(
        data,
        "compliance",
        {k: v for k, v in compliance.items() if v is not None},
    )


def ask_kms(data: dict, ctx: _Context) -> None:
    """Asks for the KMS protection level, storing only a changed value.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    regime = _get(data, "compliance.regime", "")
    derived = naming.kms_protection_level(regime)
    ctx.prompter.note(
        f"Stage 0 derives KMS protection level {derived} for {regime}."
    )
    level = ctx.prompter.select(
        "KMS protection level",
        list(_KMS_LEVELS),
        default=data.get("kms_protection_level") or derived,
    )
    _put(data, "kms_protection_level", None if level == derived else level)


def _user_account(ctx):
    account = ctx.discovered.gcloud_account
    if account and not account.endswith(naming.SERVICE_ACCOUNT_SUFFIX):
        return account
    return None


def ask_contacts(data: dict, ctx: _Context) -> None:
    """Asks for the alert email, essential contacts and bootstrap user.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    user = _user_account(ctx)
    data["alert_email"] = ctx.prompter.text(
        "Alert email",
        default=data.get("alert_email") or user,
        validate=_email(),
    )
    contacts = data.get("essential_contacts")
    if isinstance(contacts, dict):
        ctx.prompter.note(
            "Keeping the essential_contacts map; edit answers.yaml to "
            "change it."
        )
    else:
        contacts = ctx.prompter.text(
            "Essential contacts email, blank for none",
            default=contacts,
            validate=_email(optional=True),
        )
        _put(data, "essential_contacts", contacts or None)
    # The bootstrap phase writes the user into the phase file, so only the
    # final phase may leave it blank.
    final = data.get("stage0_phase") == models.STAGE0_FINAL
    bootstrap_user = ctx.prompter.text(
        "Bootstrap user, the human user of the first Stage 0 apply"
        + (", blank for none" if final else ""),
        default=data.get("bootstrap_user") or user,
        validate=_email(optional=final),
    )
    _put(data, "bootstrap_user", bootstrap_user or None)


def ask_groups(data: dict, ctx: _Context) -> None:
    """Asks whether to rename the Stage 0 groups, storing only renames.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    defaults = ctx.repo.default_groups()
    current = dict(data.get("groups") or {})
    for key, name in defaults.items():
        ctx.prompter.note(f"  {key}: {current.get(key, name)}")
    renamed = {}
    if ctx.prompter.confirm(
        "Rename any Stage 0 groups?", default=bool(current)
    ):
        for key, name in defaults.items():
            value = ctx.prompter.text(
                f"Group {key}",
                default=current.get(key, name),
                validate=lambda text: None if text else "Enter a group.",
            )
            if value != name:
                renamed[key] = value
    _put(data, "groups", renamed or None)


def _check_env_keys(text):
    keys = _split(text)
    if not keys:
        return "Enter at least one environment key."
    lowered = set()
    for key in keys:
        if not re.match(models.ENV_KEY_PATTERN, key):
            return (
                f"Env key {key} must start with a letter and use only "
                "letters, digits and hyphens."
            )
        if key.lower() in lowered:
            return f"Env keys differ only in case: {key}."
        lowered.add(key.lower())
    return None


def ask_envs(data: dict, ctx: _Context) -> None:
    """Asks for the Stage 1 environment folders and their admins.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    current = _get(data, "resman.envs")
    if current is None:
        current = _default_envs()
    keys = _split(
        ctx.prompter.text(
            "Stage 1 environment keys, comma-separated",
            default=", ".join(current),
            validate=_check_env_keys,
        )
    )
    envs = {key: dict(current.get(key) or {}) for key in keys}
    default_admin = naming.principal_email(
        _group_principal(data, ctx, derive.ORGANIZATION_ADMINS)
    )
    custom = ctx.prompter.confirm(
        f"Use folder admins other than {default_admin}?",
        default=any(env.get("admin") for env in envs.values()),
    )
    for key, env in envs.items():
        admin = None
        if custom:
            admin = ctx.prompter.text(
                f"Admin email of the {key} folder",
                default=env.get("admin") or default_admin,
                validate=_email(),
            )
        _put(env, "admin", None if admin == default_admin else admin)
    resman = dict(data.get("resman") or {})
    resman["envs"] = envs
    data["resman"] = resman


def _tenant_ids(data, key):
    prefix, envs = data.get("prefix", ""), _env_keys(data)
    projects = naming.tenant_project_ids(prefix, envs, key)
    return projects + naming.tenant_service_account_ids(prefix, envs, key)


def ask_tenants(data: dict, ctx: _Context) -> None:
    """Asks for the Stage 1 tenants and shows their derived project IDs.

    Args:
        data: Answer data, which the section updates in place.
        ctx: The prompter, the engine checkout and the discovered defaults.
    """
    limit = ctx.repo.tenant_key_max_length()
    current = dict(_get(data, "resman.tenants", {}) or {})

    def check(text):
        for key in _split(text):
            if not re.match(models.TENANT_KEY_PATTERN, key) or len(key) > limit:
                return (
                    f"Tenant key {key} must be 1 to {limit} lowercase "
                    "letters, digits or hyphens, starting with a letter."
                )
            too_long = [
                name
                for name in _tenant_ids(data, key)
                if len(name) > validate.ID_MAX_LENGTH
            ]
            if too_long:
                return (
                    f"Tenant {key} makes {too_long[0]} longer than "
                    f"{validate.ID_MAX_LENGTH} characters."
                )
        return None

    keys = _split(
        ctx.prompter.text(
            "Tenant keys, comma-separated, blank for none",
            default=", ".join(current),
            validate=check,
        )
    )
    default_admin = _group_principal(data, ctx, derive.DEVOPS)
    tenants = {}
    for key in keys:
        tenant = dict(current.get(key) or {})
        tenant["descriptive_name"] = ctx.prompter.text(
            f"Descriptive name of tenant {key}",
            default=tenant.get("descriptive_name") or key,
            validate=lambda text: None if text else "Enter a name.",
        )
        admin = ctx.prompter.text(
            f"Admin principal of tenant {key}",
            default=tenant.get("admin_principal") or default_admin,
            validate=_matches(
                _PRINCIPAL_RE, "Enter a principal such as group:x@example.com."
            ),
        )
        _put(
            tenant,
            "admin_principal",
            None if admin == default_admin else admin,
        )
        tenants[key] = tenant
    resman = dict(data.get("resman") or {})
    resman["tenants"] = tenants
    data["resman"] = resman
    for key in tenants:
        ctx.prompter.note(f"Tenant {key} projects:")
        for project_id in naming.tenant_project_ids(
            data.get("prefix", ""), _env_keys(data), key
        ):
            left = validate.ID_MAX_LENGTH - len(project_id)
            ctx.prompter.note(f"  {project_id}  {left} characters left")


@dataclasses.dataclass(frozen=True)
class Section:
    """A wizard section and the answer fields it writes.

    Attributes:
        ask: Asks for the fields and updates the answer data in place.
        fields: Dotted field paths the section owns, so a problem in one of
            them, or below it, re-asks this section.
    """

    ask: Callable[[dict, _Context], None]
    fields: tuple[str, ...]


SECTIONS: Mapping[str, Section] = {
    "prefix": Section(ask_prefix, ("prefix",)),
    "organization": Section(ask_organization, ("organization",)),
    "billing": Section(ask_billing, ("billing",)),
    "bootstrap": Section(
        ask_bootstrap,
        ("bootstrap_project", "imports", "keep_imported_projects"),
    ),
    # The regime comes before the region, because it limits the regions.
    "compliance": Section(ask_compliance, ("compliance",)),
    "region": Section(
        ask_region,
        ("region", "compliance.location", "compliance.allow_unlisted_region"),
    ),
    "kms": Section(ask_kms, ("kms_protection_level",)),
    "contacts": Section(
        ask_contacts, ("alert_email", "essential_contacts", "bootstrap_user")
    ),
    "groups": Section(ask_groups, ("groups",)),
    "envs": Section(ask_envs, ("resman.envs",)),
    "tenants": Section(ask_tenants, ("resman.tenants",)),
}

# A problem under one tenant key, such as a derived ID that gets too long,
# comes from the prefix, the env keys or the tenant key.
_TENANT_FIELD_PREFIX = "resman.tenants."
_TENANT_FIELD_OWNERS = ("prefix", "envs", "tenants")


def _covers(owned, field):
    return field == owned or field.startswith((f"{owned}.", f"{owned}["))


def owners(field: str) -> tuple[str, ...]:
    """Returns the sections that ask for a field.

    The section that owns the most specific field path wins, so
    `compliance.location` belongs to the region section.

    Args:
        field: Dotted field path, such as `compliance.regime`.

    Returns:
        Section names, empty when no section asks for the field, such as
        `overrides`.
    """
    if field.startswith(_TENANT_FIELD_PREFIX):
        return _TENANT_FIELD_OWNERS
    matches = [
        (len(owned), name)
        for name, section in SECTIONS.items()
        for owned in section.fields
        if _covers(owned, field)
    ]
    if not matches:
        return ()
    return (max(matches)[1],)


def problems(data: dict, repo: repo_lib.Repo) -> list[tuple[str, str]]:
    """Validates answer data with the model and the repository rules.

    Args:
        data: Answer data in the `answers.yaml` shape.
        repo: The engine checkout.

    Returns:
        `(field, message)` pairs, empty when the answers are valid.
    """
    try:
        parsed = models.Answers.model_validate(answers_lib.plain(data))
    except pydantic.ValidationError as error:
        return [
            (field, f"{field}: {message}")
            for field, message in answers_lib.error_fields(error)
        ]
    return [
        (problem.split(maxsplit=1)[0].rstrip(":"), problem)
        for problem in validate.problems(parsed, repo)
    ]


def _ordered(sections):
    unknown = sorted(set(sections) - set(SECTIONS))
    if unknown:
        raise ValueError(
            f"Unknown section {', '.join(unknown)}; use one of "
            f"{', '.join(SECTIONS)}"
        )
    return [name for name in SECTIONS if name in set(sections)]


def _ask(names, data, ctx):
    for name in names:
        SECTIONS[name].ask(data, ctx)
    # A new prefix or billing mode changes which Stage 0 projects exist and
    # their IDs, so imports that the bootstrap section added follow along.
    if _has_stage0_imports(data, ctx) and _sync_stage0_imports(
        data, ctx, enabled=True
    ):
        ctx.prompter.note("Updated the Stage 0 imports:")
        _note_imports(data, ctx)


def run(
    data: Mapping[str, Any],
    *,
    prompter: prompts.Prompter,
    repo: repo_lib.Repo,
    discovered: discovery.Discovered,
    sections: Iterable[str] | None = None,
) -> dict:
    """Runs the wizard over answer data.

    Args:
        data: Current answer data, which is not modified. Its values are
            the defaults, so a rerun only needs Enter to keep them.
        prompter: Asks the operator.
        repo: The engine checkout.
        discovered: Defaults found by `discovery.discover`.
        sections: Section names to ask, in any order; None asks all of
            them in `SECTIONS` order.

    Returns:
        The updated answer data, valid for `models.Answers` and
        `validate.problems`.

    Raises:
        ValueError: If a section name is unknown.
        WizardError: If the answers are still invalid after `MAX_ROUNDS`
            rounds of re-asking, or a problem has no section to fix it.
    """
    names = list(SECTIONS) if sections is None else _ordered(sections)
    result = copy.deepcopy(answers_lib.plain(dict(data)))
    ctx = _Context(prompter=prompter, repo=repo, discovered=discovered)
    _ask(names, result, ctx)
    for _ in range(MAX_ROUNDS):
        found = problems(result, repo)
        if not found:
            return result
        sections_to_ask = set()
        for field, _message in found:
            field_owners = owners(field)
            if not field_owners:
                raise WizardError([message for _, message in found])
            sections_to_ask.update(field_owners)
        prompter.note("These answers need another look:")
        for _field, message in found:
            prompter.note(f"  {message}")
        _ask(_ordered(sections_to_ask), result, ctx)
    found = problems(result, repo)
    if found:
        raise WizardError([message for _, message in found])
    return result
