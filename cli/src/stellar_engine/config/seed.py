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

"""Seeds a new environment from existing answers, and suggests prefixes.

`stellar init --answers-from` copies the organization, billing, groups and
tenants of another environment so most prompts become Enter-to-accept.
Derived values are stored as None, so they follow the new regime on their
own; explicit values are kept and listed for review.

`--new-prefix` addresses issue #50: a short base plus a random suffix gives
a fresh prefix while Terraform names stay deterministic.
"""

import copy
import pathlib
import random
import string

from stellar_engine import paths
from stellar_engine.config import models
from stellar_engine.preflight import regions

# Imports name the source environment's own projects, so carrying them
# would make the new environment adopt projects it does not own. The
# existing organization policies describe the source organization as the
# last scan saw it, so the new environment scans its own.
# keep_imported_projects is a preference rather than organization state, so
# it carries and applies once the new environment adds its own imports.
# stage0_phase records how far the source deployment got, and a new
# environment always starts with the bootstrap apply.
NEVER_CARRIED = (
    "prefix",
    "engine",
    "imports",
    "existing_org_policies",
    "stage0_phase",
)

SUFFIX_LENGTH = 4
_SUFFIX_CHARS = string.ascii_lowercase + string.digits


def seed(source: dict) -> dict:
    """Returns answer data to start a new environment from.

    Args:
        source: Answer data of an existing environment.

    Returns:
        A deep copy without the keys in NEVER_CARRIED.
    """
    return {
        key: copy.deepcopy(value)
        for key, value in source.items()
        if key not in NEVER_CARRIED
    }


def _regime(data):
    compliance = data.get("compliance")
    return compliance.get("regime") if isinstance(compliance, dict) else None


def review_notes(source: dict, target_regime: str | None) -> list[str]:
    """Lists carried values the operator should re-check.

    Args:
        source: Answer data of the source environment.
        target_regime: Regime of the new environment, or None when it keeps
            the source regime.

    Returns:
        Readable notes, empty when nothing needs a second look.
    """
    notes = []
    # The prefix is always asked again and the engine recorded again, so
    # only the dropped imports, organization policies and phase need a note.
    if source.get("imports"):
        notes.append(
            "the copy drops the imports, because they name resources of "
            "the source environment; add the imports for this one."
        )
    if source.get("existing_org_policies"):
        notes.append(
            "the copy drops existing_org_policies, because they describe "
            "the organization of the source environment; run stellar "
            "imports scan for this one."
        )
    if source.get("stage0_phase") == models.STAGE0_FINAL:
        notes.append(
            "the copy starts in the bootstrap stage0_phase, because the "
            "source environment already ran its final Stage 0 apply; this "
            "environment runs the first apply with bootstrap_user."
        )
    old_regime = _regime(source)
    if not target_regime or target_regime == old_regime:
        return notes
    change = f"the regime changes from {old_regime} to {target_regime}"
    level = source.get("kms_protection_level")
    if level:
        notes.append(
            f"kms_protection_level {level} is explicit; {change}, so check "
            "it or remove it to use the regime default."
        )
    compliance = source.get("compliance") or {}
    if compliance.get("location"):
        notes.append(
            f"compliance.location {compliance['location']} is explicit; "
            f"{change}, so check that Assured Workloads offers it."
        )
    if compliance.get("allow_unlisted_region"):
        notes.append(
            f"compliance.allow_unlisted_region is set; {change}, so check "
            "the region against the new regime."
        )
    allowed = regions.supported_regions(target_regime)
    region = source.get("region")
    if allowed is not None and region and region not in allowed:
        notes.append(
            f"region {region} is not an Assured Workloads region for "
            f"{target_regime}; choose another."
        )
    if source.get("overrides"):
        notes.append(
            f"the copy keeps the overrides as written; {change}, so check them."
        )
    return notes


def suggest_prefix(base: str, limit: int, rng: random.Random) -> str:
    """Suggests a fresh prefix from a base and a random suffix.

    Args:
        base: Preferred start of the prefix; characters other than
            lowercase letters and digits are dropped.
        limit: Maximum prefix length, from `Repo.prefix_max_length()`.
        rng: Random source, seeded in tests.

    Returns:
        A prefix of at most `limit` characters that starts with a letter
        and ends with up to SUFFIX_LENGTH random characters.

    Raises:
        ValueError: If the limit is below 1.
    """
    if limit < 1:
        raise ValueError(f"Prefix limit {limit} is below 1")
    suffix_length = min(SUFFIX_LENGTH, limit)
    cleaned = "".join(
        char for char in base.lower() if char in _SUFFIX_CHARS
    ).lstrip(string.digits)
    head = cleaned[: limit - suffix_length]
    suffix = [rng.choice(_SUFFIX_CHARS) for _ in range(suffix_length)]
    if not head:
        suffix[0] = rng.choice(string.ascii_lowercase)
    return head + "".join(suffix)


def resolve_source(spec: str, home: paths.Home) -> pathlib.Path:
    """Finds the answers file that `--answers-from` names.

    Args:
        spec: An environment prefix in the home, a path to an answers file,
            or a directory holding `answers.yaml`.
        home: The home whose environments a prefix refers to.

    Returns:
        Path of the source answers file.

    Raises:
        FileNotFoundError: If no environment or file matches.
    """
    try:
        env_answers = home.env(spec).answers
    except ValueError:
        env_answers = None
    if env_answers is not None and env_answers.is_file():
        return env_answers
    path = pathlib.Path(spec).expanduser()
    if path.is_dir():
        path /= "answers.yaml"
    if path.is_file():
        return path
    raise FileNotFoundError(
        f"No environment {spec!r} in {home.root} and no answers file at {path}"
    )
