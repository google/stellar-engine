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

"""Loads, edits and saves `answers.yaml`.

The file is the operator's record of one environment, so saving keeps
their comments and key order through a ruamel round trip, and writes
atomically with mode 0600 because it names principals and billing
accounts.
"""

import copy
import io
import json
import pathlib
from typing import Any

import pydantic
from ruamel import yaml
from ruamel.yaml import error as yaml_error
from ruamel.yaml import tokens as yaml_tokens

from stellar_engine import fsutil
from stellar_engine import naming
from stellar_engine import paths
from stellar_engine.config import derive
from stellar_engine.config import models
from stellar_engine.config import validate
from stellar_engine.preflight import inputs

# The path is relative to `<home>/envs/<prefix>/answers.yaml`.
SCHEMA_COMMENT = "# yaml-language-server: $schema=../../answers.schema.json"

# Answers that `scripts/deploy.sh` keeps in config.env beyond the keys
# preflight reads through `inputs.CONFIG_ENV_KEYS`.
_ALERT_EMAIL_KEY = "LOGGING_ALERTS_EMAIL_ADDRESS"
_DEPLOYER_KEY = "DEPLOYER_EMAIL_ADDRESS"
_AW_REGION_KEY = "AW_REGION"
_TENANT_KEY = "TENANT_NAME"

# Import addresses ending in this create projects, which preflight then
# expects to exist instead of reporting a collision.
_PROJECT_ADDRESS_SUFFIX = "google_project.project[0]"


# Slots of a ruamel map entry comment: the comment lines before the key,
# and the token after the value, which holds the EOL comment and the lines
# above the next key.
_BEFORE = 1
_TRAILING = 2


class AnswersError(Exception):
    """Raised when an answers file cannot be read, parsed or saved."""


def _round_trip():
    loader = yaml.YAML(typ="rt")
    loader.preserve_quotes = True
    loader.indent(mapping=2, sequence=4, offset=2)
    loader.width = 4096
    return loader


def load_data(path: pathlib.Path) -> yaml.CommentedMap:
    """Reads an answers file keeping its comments and key order.

    Args:
        path: The `answers.yaml` path.

    Returns:
        The round-trip mapping, empty for an empty file.

    Raises:
        AnswersError: If the file is missing, is not YAML, or is not a
            mapping.
    """
    path = pathlib.Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise AnswersError(f"Cannot read {path}: {error}") from error
    try:
        data = _round_trip().load(text)
    except yaml.YAMLError as error:
        raise AnswersError(f"{path} is not valid YAML: {error}") from error
    if data is None:
        return yaml.CommentedMap()
    if not isinstance(data, yaml.CommentedMap):
        raise AnswersError(f"{path} must contain a mapping")
    return data


def plain(value: Any) -> Any:
    """Converts ruamel round-trip containers and scalars to plain Python.

    Args:
        value: A value from `load_data`, or plain data.

    Returns:
        The same value built from dicts, lists and builtin scalars.
    """
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    if isinstance(value, bool) or value is None:
        return value
    for kind in (int, float, str):
        if isinstance(value, kind):
            return kind(value)
    return value


def parse(data: Any, source: str | None = None) -> models.Answers:
    """Validates answer data against the model.

    Args:
        data: A mapping in the `answers.yaml` shape.
        source: Where the data comes from for error messages, such as a
            path or the `init` options that supplied it. None leaves the
            source out.

    Returns:
        The validated answers.

    Raises:
        AnswersError: Listing every model error with its field.
    """
    try:
        return models.Answers.model_validate(plain(data))
    except pydantic.ValidationError as error:
        title = (
            f"Invalid answers from {source}:"
            if source
            else ("Invalid answers:")
        )
        raise AnswersError(f"{title}\n{format_errors(error)}") from error


def error_fields(error: pydantic.ValidationError) -> list[tuple[str, str]]:
    """Returns the dotted field and the message of each pydantic error.

    Args:
        error: The validation error of the answers model.

    Returns:
        `(field, message)` pairs; an error of the whole model names the
        field `answers`.
    """
    return [
        (".".join(str(part) for part in item["loc"]) or "answers", item["msg"])
        for item in error.errors()
    ]


def format_errors(error: pydantic.ValidationError) -> str:
    """Formats pydantic errors as one `field: message` line each.

    Args:
        error: The validation error of the answers model.

    Returns:
        The lines, joined with newlines.
    """
    return "\n".join(
        f"- {field}: {message}" for field, message in error_fields(error)
    )


def load(path: pathlib.Path) -> models.Answers:
    """Reads and validates an answers file.

    Args:
        path: The `answers.yaml` path.

    Returns:
        The validated answers.

    Raises:
        AnswersError: If the file cannot be read or fails validation.
    """
    return parse(load_data(path), str(path))


def _trailing_owner(mapping, key):
    """Returns the map and key whose comment token ends the entry of `key`.

    ruamel stores the comment lines above a key as the trailing token of
    the entry before it, and a nested map's entry ends with its last key.
    """
    value = mapping[key]
    while isinstance(value, yaml.CommentedMap) and value:
        mapping, key = value, list(value)[-1]
        value = mapping[key]
    return mapping, key


def _pop_following(mapping, key):
    """Detaches the comment lines after the entry of `key`.

    Returns:
        The lines, without the EOL comment of the entry, which stays.
    """
    owner, owner_key = _trailing_owner(mapping, key)
    entry = owner.ca.items.get(owner_key)
    token = entry[_TRAILING] if entry else None
    if token is None:
        return ""
    # The token holds the EOL comment of the line, then the lines below it.
    eol, _, lines = token.value.partition("\n")
    if eol.strip():
        token.value = eol + "\n"
    else:
        entry[_TRAILING] = None
    return lines


def _comment_token(text):
    return yaml_tokens.CommentToken(text, yaml_error.CommentMark(0), None)


def _put_above(mapping, key, text):
    entry = mapping.ca.items.setdefault(key, [None] * 4)
    entry[_BEFORE] = [*(entry[_BEFORE] or []), _comment_token(text)]


def _put_after(mapping, key, text):
    owner, owner_key = _trailing_owner(mapping, key)
    entry = owner.ca.items.setdefault(owner_key, [None] * 4)
    if entry[_TRAILING] is None:
        entry[_TRAILING] = _comment_token("\n" + text)
    else:
        entry[_TRAILING].value += text


def _merge(previous, data):
    """Merges new values into a round-trip map, keeping unchanged nodes.

    Keys missing from `data` are dropped, keys present in both keep their
    position and comments, and new keys are appended in model order.

    ruamel stores the comment lines above a key with the entry before it,
    so those lines move before that entry goes away: above the next kept
    key, or to the end of the map when they follow its last entry and so
    describe whatever follows the map.
    """
    if not isinstance(previous, yaml.CommentedMap):
        for key in [key for key in previous if key not in data]:
            del previous[key]
        return _update(previous, data)
    keys = list(previous)
    removed = {key for key in keys if key not in data}
    tail = ""
    for index, key in enumerate(keys):
        if key not in removed:
            continue
        lines = _pop_following(previous, key)
        if index + 1 == len(keys):
            tail += lines
        elif keys[index + 1] not in removed and lines.strip():
            _put_above(previous, keys[index + 1], lines)
    for key in removed:
        del previous[key]
        previous.ca.items.pop(key, None)
    if previous and any(key not in previous for key in data):
        # Appended keys go after the comment lines that end the map.
        tail = _pop_following(previous, list(previous)[-1]) + tail
    _update(previous, data)
    if tail.strip() and previous:
        _put_after(previous, list(previous)[-1], tail)
    return previous


def _update(previous, data):
    for key, value in data.items():
        old = previous.get(key)
        if isinstance(value, dict) and isinstance(old, dict):
            _merge(old, value)
        elif key not in previous or plain(old) != value:
            previous[key] = value
    return previous


def _atomic_write(path, text, mode):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fsutil.atomic_write(path, text, mode)


def save(
    path: pathlib.Path,
    answers: models.Answers,
    *,
    home: pathlib.Path | None = None,
    previous: yaml.CommentedMap | None = None,
) -> None:
    """Writes answers, keeping the comments of a previous load.

    Args:
        path: The `answers.yaml` path.
        answers: Validated answers.
        home: The home that holds the environment of the file. The answers
            must not point into it, and the JSON schema of the model goes
            to its `paths.Home.schema_path`. None skips both.
        previous: The map `load_data` returned for this file, whose
            comments and key order survive. None writes a fresh file.

    Raises:
        AnswersError: If a value points into the home.
    """
    path = pathlib.Path(path)
    if home is not None:
        found = validate.home_references(answers, home)
        if found:
            raise AnswersError("\n".join(found))
    data = answers.model_dump(mode="json", exclude_none=True)
    merged = _merge(
        copy.deepcopy(previous) if previous is not None else {}, data
    )
    if not isinstance(merged, yaml.CommentedMap):
        merged = yaml.CommentedMap(merged)
    stream = io.StringIO()
    _round_trip().dump(merged, stream)
    lines = stream.getvalue().splitlines(keepends=True)
    while lines and lines[0].strip() in (SCHEMA_COMMENT, ""):
        lines.pop(0)
    _atomic_write(path, f"{SCHEMA_COMMENT}\n{''.join(lines)}", 0o600)
    if home is not None:
        schema = models.Answers.model_json_schema()
        _atomic_write(
            paths.Home(pathlib.Path(home)).schema_path,
            json.dumps(schema, indent=2) + "\n",
            0o644,
        )


def _split_assignment(assignment):
    """Splits `a.b."c.d"=VALUE` into key segments and the value text.

    A double-quoted segment may contain dots and `=`, which Terraform
    resource addresses under `imports` need.

    Raises:
        ValueError: If the assignment has no `=`, an empty segment, or an
            unterminated quote.
    """
    segments = []
    current = ""
    index = 0
    while index < len(assignment):
        char = assignment[index]
        if char == '"' and not current:
            end = assignment.find('"', index + 1)
            while end != -1 and assignment[end - 1] == "\\":
                end = assignment.find('"', end + 1)
            if end == -1:
                raise ValueError(f"Unterminated quote in {assignment!r}")
            current = json.loads(assignment[index : end + 1])
            index = end + 1
            if index < len(assignment) and assignment[index] not in ".=":
                raise ValueError(f"Malformed key in {assignment!r}")
            if not current:
                raise ValueError(f"Empty key segment in {assignment!r}")
            continue
        if char in ".=":
            if not current:
                raise ValueError(f"Empty key segment in {assignment!r}")
            segments.append(current)
            current = ""
            if char == "=":
                return segments, assignment[index + 1 :]
        else:
            current += char
        index += 1
    raise ValueError(f"Expected KEY=VALUE, got {assignment!r}")


def _parse_value(text):
    # YAML 1.2, so `yes` and `no` stay strings; an empty value is "".
    if not text.strip():
        return ""
    try:
        value = plain(yaml.YAML(typ="safe", pure=True).load(text))
    except yaml.YAMLError as error:
        raise ValueError(f"Cannot parse value {text!r}: {error}") from error
    # Keep numbers whose text a number would not reproduce, such as an ID
    # with a leading zero, as the string the operator typed.
    is_number = isinstance(value, int | float) and not isinstance(value, bool)
    if is_number and str(value) != text.strip():
        return text.strip()
    return value


def apply_sets(data: dict, assignments: list[str]) -> dict:
    """Applies `--set KEY=VALUE` assignments to answer data.

    KEY is a dotted path such as `billing.no_iam`; a double-quoted segment
    may contain dots, as in
    `imports.0-bootstrap."module.x.google_project.project[0]"=my-project`.
    VALUE is a YAML flow scalar or collection, so `true`, `[C01, C02]` and
    `{descriptive_name: tenant-1}` work, and `null` sets None.

    Args:
        data: Answer data, which is not modified.
        assignments: The assignments in order.

    Returns:
        A copy of the data with the assignments applied and intermediate
        maps created.

    Raises:
        ValueError: On a malformed assignment, or a path through a value
            that is not a map.
    """
    result = copy.deepcopy(data)
    for assignment in assignments:
        segments, text = _split_assignment(assignment)
        target = result
        for depth, segment in enumerate(segments[:-1]):
            child = target.setdefault(segment, {})
            if not isinstance(child, dict):
                path = ".".join(segments[: depth + 1])
                raise ValueError(
                    f"Cannot set {'.'.join(segments)}: {path} is not a map"
                )
            target = child
        target[segments[-1]] = _parse_value(text)
    return result


def from_config_env(path: pathlib.Path) -> dict:
    """Maps a `scripts/config.env` file onto the answers shape.

    Args:
        path: Path of the file, in the format of `scripts/config.env.sample`.

    Returns:
        Answer data with the values the file sets.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    extra = inputs.read_config_env(path)
    found = inputs.config_env_fields(extra)
    data = {}
    if "prefix" in found:
        data["prefix"] = found["prefix"]
    organization = {
        field: found[source]
        for field, source in (
            ("id", "org_id"),
            ("domain", "domain"),
            ("customer_id", "customer_id"),
        )
        if source in found
    }
    if organization:
        data["organization"] = organization
    if "billing_account" in found:
        data["billing"] = {"account_id": found["billing_account"]}
    if "bootstrap_project" in found:
        data["bootstrap_project"] = found["bootstrap_project"]
    if "region" in found:
        data["region"] = found["region"]
    compliance = {}
    if "regime" in found:
        compliance["regime"] = found["regime"].upper()
    aw_region = extra.get(_AW_REGION_KEY)
    if aw_region and aw_region != found.get("region"):
        compliance["location"] = aw_region
    if compliance:
        data["compliance"] = compliance
    if extra.get(_ALERT_EMAIL_KEY):
        data["alert_email"] = extra[_ALERT_EMAIL_KEY]
    deployer = extra.get(_DEPLOYER_KEY)
    # deploy.sh runs setIAM for the deployer, which may be a service
    # account; bootstrap_user must be a human user.
    if deployer and not deployer.endswith(naming.SERVICE_ACCOUNT_SUFFIX):
        data["bootstrap_user"] = deployer
    tenant = extra.get(_TENANT_KEY)
    if tenant:
        data["resman"] = {"tenants": {tenant: {"descriptive_name": tenant}}}
    return data


def to_preflight(answers: models.Answers) -> dict:
    """Returns the PreflightInputs field values the answers define.

    Args:
        answers: Validated answers.

    Returns:
        Field values without unset ones, including the tenant project IDs,
        the project IDs and Stage 0 addresses that import blocks adopt, and
        the organization policies that Stage 0 imports.
    """
    tenant_ids = [
        project_id
        for project_ids in derive.tenant_project_ids(answers).values()
        for project_id in project_ids
    ]
    imported = sorted(
        {
            import_id
            for imports in answers.imports.values()
            for address, import_id in imports.items()
            if address.endswith(_PROJECT_ADDRESS_SUFFIX)
        }
    )
    values = {
        "org_id": answers.organization.id,
        "billing_account": answers.billing.account_id,
        "billing_no_iam": answers.billing.no_iam,
        "billing_is_org_level": answers.billing.is_org_level,
        "bootstrap_project": answers.bootstrap_project,
        "prefix": answers.prefix,
        "regime": answers.compliance.regime,
        "region": answers.region,
        "domain": answers.organization.domain,
        "customer_id": answers.organization.customer_id,
        "bootstrap_user": answers.bootstrap_user,
        "groups": dict(answers.groups),
        "tenant_project_ids": tuple(tenant_ids),
        "imported_project_ids": tuple(imported),
        "imported_addresses": tuple(
            sorted(answers.imports.get(paths.BOOTSTRAP, {}))
        ),
        # Preflight falls back to the region itself, so a --region flag
        # also moves a location that the answers leave to the region.
        "compliance_location": answers.compliance.location,
        "billing_budget": answers.budget.amount is not None,
        "existing_org_policies": tuple(answers.existing_org_policies),
    }
    return {key: value for key, value in values.items() if value is not None}
