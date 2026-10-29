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

"""Inputs for preflight checks and the loaders that resolve them.

Values come from command-line flags or `STELLAR_*` environment variables,
which Typer resolves, then from the environment's `answers.yaml`, and then
from an optional `scripts/config.env` file that `scripts/deploy.sh` users
already have. Flags always win.
"""

from collections.abc import Mapping
import pathlib
from typing import Any

import dotenv
import pydantic

from stellar_engine import patterns

# Maps scripts/config.env keys to PreflightInputs fields.
CONFIG_ENV_KEYS = {
    "BILLING_ACCOUNT": "billing_account",
    "BOOTSTRAP_PROJECT_ID": "bootstrap_project",
    "COMPLIANCE_REGIME": "regime",
    "DIRECTORY_CUSTOMER_ID": "customer_id",
    "FULLY_QUALIFIED_DOMAIN_NAME": "domain",
    "ORGANIZATION_ID": "org_id",
    "PREFIX": "prefix",
    "REGION": "region",
}


class PreflightInputs(pydantic.BaseModel):
    """Deployment values that preflight checks validate against.

    Every field is optional. A check whose inputs are missing reports SKIP
    and names the flag that enables it.
    """

    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

    org_id: str | None = pydantic.Field(default=None, pattern=patterns.ORG_ID)
    billing_account: str | None = pydantic.Field(
        default=None, pattern=patterns.BILLING_ACCOUNT
    )
    billing_no_iam: bool = False
    # False when the billing account belongs to another organization, which
    # with billing_no_iam decides whether Stage 0 creates the billing export
    # project.
    billing_is_org_level: bool = True
    bootstrap_project: str | None = pydantic.Field(
        default=None, pattern=patterns.PROJECT_ID
    )
    prefix: str | None = None
    regime: str | None = pydantic.Field(default=None, pattern=patterns.REGIME)
    region: str | None = None
    domain: str | None = None
    customer_id: str | None = None
    bootstrap_user: str | None = pydantic.Field(
        default=None, pattern=patterns.EMAIL
    )
    groups: dict[str, str] = pydantic.Field(default_factory=dict)
    redeploy: bool = False
    # Stage 1 tenant project IDs, which only answers.yaml defines.
    tenant_project_ids: tuple[str, ...] = ()
    # Project IDs that import blocks adopt instead of creating, so preflight
    # expects them to exist.
    imported_project_ids: tuple[str, ...] = ()
    # Resource addresses that Stage 0 import blocks adopt, such as the
    # Assured Workloads workload, from `imports.0-bootstrap` in answers.yaml.
    imported_addresses: tuple[str, ...] = ()
    # The Assured Workloads location. None uses the region, as the answers
    # do.
    compliance_location: str | None = None
    # Whether Stage 0 creates a budget on the billing account, from the
    # `budget.amount` answer, which needs billing access whatever exists.
    billing_budget: bool = False
    # Constraints of the existing organization policies that Stage 0
    # imports, from `existing_org_policies` in answers.yaml. None when the
    # inputs come without answers.yaml, which has nowhere to list them.
    existing_org_policies: tuple[str, ...] | None = None


def read_config_env(path):
    """Reads every value of a `scripts/config.env` file.

    Args:
        path: Path of the file, in the `KEY=value` format of
            `scripts/config.env.sample`.

    Returns:
        A dict of every key in the file to its value without surrounding
        whitespace, empty for a key without a value.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = pathlib.Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        key: (value or "").strip()
        for key, value in dotenv.dotenv_values(path).items()
    }


def config_env_fields(values):
    """Maps `scripts/config.env` values to PreflightInputs fields.

    Args:
        values: Values as `read_config_env` returns them.

    Returns:
        A dict of PreflightInputs field names to non-empty string values.
    """
    return {
        field: values[key]
        for key, field in CONFIG_ENV_KEYS.items()
        if values.get(key)
    }


def load_config_env(path):
    """Reads PreflightInputs fields from a `scripts/config.env` file.

    Args:
        path: Path of the file, in the `KEY=value` format of
            `scripts/config.env.sample`.

    Returns:
        A dict of PreflightInputs field names to non-empty string values.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return config_env_fields(read_config_env(path))


def resolve(
    flags: Mapping[str, Any],
    config_env: pathlib.Path | None = None,
    answer_values: Mapping[str, Any] | None = None,
) -> PreflightInputs:
    """Merges flag values with optional answers and a config.env file.

    Precedence is flags, then answers, then config.env.

    Args:
        flags: Field values from the command line or environment. A falsy
            value such as None or False means the operator did not set it.
        config_env: Optional path of a `scripts/config.env` file whose values
            fill fields that flags and answers leave unset.
        answer_values: Optional field values from the environment's
            answers, as `config.answers.to_preflight` returns them, which
            fill fields that flags leave unset.

    Returns:
        A validated PreflightInputs.

    Raises:
        pydantic.ValidationError: If a value has an invalid format.
        FileNotFoundError: If config_env does not exist.
    """
    merged = load_config_env(config_env) if config_env else {}
    if answer_values is not None:
        merged.update(answer_values)
    merged.update({key: value for key, value in flags.items() if value})
    if isinstance(merged.get("regime"), str):
        merged["regime"] = merged["regime"].upper()
    return PreflightInputs.model_validate(merged)


def validate_against_repo(inputs, repo):
    """Rejects values that the Stage 0 variables would also reject.

    Args:
        inputs: Resolved PreflightInputs.
        repo: The `repo.Repo` whose Stage 0 variables define valid values.

    Raises:
        ValueError: If the regime is not in `regime_mapping`, or a group key
            is not a field of the Stage 0 `groups` variable.
    """
    regimes = repo.regime_names()
    if inputs.regime and inputs.regime not in regimes:
        raise ValueError(
            f"Unknown regime {inputs.regime}. Stage 0 accepts: "
            + ", ".join(regimes)
        )
    known = set(repo.default_groups())
    unknown = sorted(set(inputs.groups) - known)
    if unknown:
        raise ValueError(
            f"Unknown group keys {', '.join(unknown)}. Stage 0 accepts: "
            + ", ".join(sorted(known))
        )
