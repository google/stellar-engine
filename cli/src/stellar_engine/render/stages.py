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

"""Builds the `terraform.tfvars` of each stage from the answers.

Each builder starts from the stage's `terraform.tfvars.sample`, so the
rendered file keeps the sample's key order and guidance comments, and
returns the complete set of top-level keys it owns. Answers replace whole
top-level values, so sample entries such as the `ten-1` and `ten-2` tenants
never leak into a deployment. `answers.overrides` merges last, as the
escape hatch for variables the model does not cover.
"""

from collections.abc import Callable, Iterator, Mapping
import copy
import dataclasses
import pathlib
import re
from typing import Any

from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import derive
from stellar_engine.config import models
from stellar_engine.config import validate
from stellar_engine.render import hcl
from stellar_engine.render import sample as sample_lib

SAMPLE_NAME = "terraform.tfvars.sample"
# Sample placeholders look like `<billing_account_id>`.
PLACEHOLDER_RE = re.compile(r"<[a-z_]+>")

_KMS_COMMENT_DERIVED = (
    "# KMS protection level for CMEK keys. stellar derives it from the",
    "# regime: SOFTWARE for FEDRAMP_MODERATE, HSM for every other regime.",
    "# The variable has no default, so stellar always writes it. Set",
    "# kms_protection_level in answers.yaml to choose another level.",
)
_KMS_COMMENT_EXPLICIT = (
    "# KMS protection level for CMEK keys, which answers.yaml sets.",
)
_DELETION_POLICIES_COMMENT = (
    "# Deletion policy of the Stage 0 projects that the imports adopt.",
    "# stellar writes ABANDON while keep_imported_projects is true in",
    "# answers.yaml, so terraform destroy keeps those projects.",
)
_OUTPUTS_COMMENT = (
    "# Per-environment folder for the provider and tfvars files that later",
    "# stages read. stellar derives it from the home on every render.",
)


class RenderError(Exception):
    """Raised when the answers cannot be rendered into a stage's tfvars."""


@dataclasses.dataclass(frozen=True)
class Rendered:
    """A rendered stage tfvars file.

    Attributes:
        stage: Stage directory name, such as `0-bootstrap`.
        values: Top-level values written, in file order.
        text: The HCL text, `terraform fmt` canonical.
    """

    stage: str
    values: dict[str, Any]
    text: str


def sample_path(repo: repo_lib.Repo, stage: str) -> pathlib.Path:
    """Returns the tfvars sample path of a stage in the engine checkout."""
    return paths.stage_dir(repo.root, stage) / SAMPLE_NAME


def _bootstrap(
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
    sample: sample_lib.Sample,
) -> dict[str, Any]:
    """Returns the Stage 0 values, mirroring the DDG Stage 0 tfvars."""
    billing: dict[str, Any] = {"id": answers.billing.account_id}
    # Only non-default flags are written, so the file reads like the DDG.
    if not answers.billing.is_org_level:
        billing["is_org_level"] = False
    if answers.billing.no_iam:
        billing["no_iam"] = True
    values: dict[str, Any] = {"billing_account": billing}
    if answers.budget.amount is not None:
        values["billing_budget_amount"] = {"amount": answers.budget.amount}
    values["regions"] = {"primary": answers.region}
    values["organization"] = {
        "domain": answers.organization.domain,
        # The variable is a number; the model keeps the ID as text.
        "id": int(answers.organization.id),
        "customer_id": answers.organization.customer_id,
    }
    values["outputs_location"] = str(env.fast_config)
    if answers.logging.retention_days is not None:
        values["logging_bucket_retention"] = answers.logging.retention_days
    values["prefix"] = answers.prefix
    values["log_sinks"] = {
        name: {**sink, "type": answers.logging.sink_type}
        for name, sink in sample.values["log_sinks"].items()
    }
    org_policies = copy.deepcopy(sample.values["org_policies_config"])
    org_policies.setdefault("constraints", {})[
        "allowed_policy_member_domains"
    ] = list(answers.org_policies.allowed_policy_member_domains)
    values["org_policies_config"] = org_policies
    values["fast_features"] = copy.deepcopy(sample.values["fast_features"])
    values["assured_workloads"] = {
        "regime": answers.compliance.regime,
        "location": derive.compliance_location(answers),
    }
    values["bootstrap_project"] = answers.bootstrap_project
    values["alert_email"] = answers.alert_email
    values["kms_protection_level"] = derive.kms_protection_level(answers)
    if answers.essential_contacts is not None:
        values["essential_contacts"] = answers.essential_contacts
    defaults = repo.default_groups()
    renamed = {
        key: name
        for key, name in answers.groups.items()
        if name != defaults.get(key)
    }
    if renamed:
        values["groups"] = renamed
    if answers.billing_override is not None:
        values["billing_override"] = answers.billing_override.model_dump()
    policies = derive.project_deletion_policies(answers, repo)
    if policies:
        values[repo_lib.PROJECT_DELETION_POLICIES] = policies
    # bootstrap_user is never written here: `render.phase` writes it to a
    # separate file in the bootstrap phase only, so the final phase drops
    # it without touching this file.
    return values


def _resman(
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
    sample: sample_lib.Sample,
) -> dict[str, Any]:
    """Returns the Stage 1 values that Stage 0 outputs do not provide."""
    del sample  # Stage 1 replaces every sample value it writes.
    values: dict[str, Any] = {
        "tenants": {
            key: {
                "admin_principal": derive.tenant_admin(answers, repo, key),
                "descriptive_name": tenant.descriptive_name,
                "locations": derive.tenant_locations(answers, key),
            }
            for key, tenant in answers.resman.tenants.items()
        },
        "envs_folders": {
            env_key: {"admin": derive.env_admin(answers, repo, env_key)}
            for env_key in answers.resman.envs
        },
        "outputs_location": str(env.fast_config),
    }
    if answers.billing_override is not None:
        values["billing_override"] = answers.billing_override.model_dump()
    return values


_BUILDERS: dict[
    str,
    Callable[
        [models.Answers, repo_lib.Repo, paths.EnvPaths, sample_lib.Sample],
        dict[str, Any],
    ],
] = {
    paths.BOOTSTRAP: _bootstrap,
    paths.RESMAN: _resman,
}


def _merge(base: Any, override: Any) -> Any:
    """Deep-merges override into base: maps merge, anything else replaces."""
    if isinstance(base, Mapping) and isinstance(override, Mapping):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = (
                _merge(merged[key], value)
                if key in merged
                else copy.deepcopy(value)
            )
        return merged
    return copy.deepcopy(override)


def _strings(value: Any, path: str) -> Iterator[tuple[str, str]]:
    """Yields every string value and map key with its dotted path."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}"
            yield child, str(key)
            yield from _strings(item, child)
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            yield from _strings(item, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def _placeholders(values: Mapping[str, Any]) -> list[str]:
    return [
        f"{path} = {text!r}"
        for name, value in values.items()
        for path, text in _strings(value, name)
        if PLACEHOLDER_RE.search(text)
    ]


def _comments(
    stage: str, answers: models.Answers, sample: sample_lib.Sample, keys
) -> dict[str, list[str]]:
    comments = {key: list(sample.comments.get(key, [])) for key in keys}
    overridden = answers.overrides.get(stage, {})
    if "kms_protection_level" in comments:
        # The sample says to leave it unset, which only works when the
        # variable has a default; Stage 0 declares none.
        comments["kms_protection_level"] = list(
            _KMS_COMMENT_EXPLICIT
            if answers.kms_protection_level
            else _KMS_COMMENT_DERIVED
        )
    if repo_lib.PROJECT_DELETION_POLICIES in comments:
        comments[repo_lib.PROJECT_DELETION_POLICIES] = list(
            _DELETION_POLICIES_COMMENT
        )
    if "outputs_location" in comments and not comments["outputs_location"]:
        comments["outputs_location"] = list(_OUTPUTS_COMMENT)
    for key in overridden:
        if key in comments and not comments[key]:
            comments[key] = [
                f"# overrides.{stage} in answers.yaml sets this value."
            ]
    return comments


def warnings(
    answers: models.Answers, stage: str, repo: repo_lib.Repo
) -> list[str]:
    """Returns non-fatal findings about the rendered tfvars of a stage.

    The arguments follow `imports.warnings`, which `render` calls next to
    this function.

    Args:
        answers: The environment answers.
        stage: Stage name or alias, such as `0`.
        repo: The engine checkout.

    Returns:
        Readable sentences, one when `keep_imported_projects` asks to keep
        imported Stage 0 projects that this Stage 0 version cannot keep.

    Raises:
        ValueError: If the stage name is unknown.
    """
    if paths.resolve_stage(stage) != paths.BOOTSTRAP:
        return []
    keys = repo.project_deletion_policy_keys()
    unkept = [
        derive.stage0_project_id(answers, project)
        for project in derive.kept_stage0_projects(answers, repo)
        if project.module not in keys
    ]
    if not unkept:
        return []
    return [
        f"keep_imported_projects is true, but this engine version of "
        f"{paths.BOOTSTRAP} cannot keep imported projects on destroy yet, "
        f"so terraform destroy deletes {', '.join(unkept)}."
    ]


def header(repo: repo_lib.Repo, stage: str, prefix: str) -> list[str]:
    """Returns the generated header of a stage's tfvars file.

    Args:
        repo: The engine checkout.
        stage: Stage directory name.
        prefix: Environment prefix.

    Returns:
        Comment lines naming the sources of the file.
    """
    sample = sample_path(repo, stage).relative_to(repo.root).as_posix()
    return [
        f"# stellar render writes this file from {sample} and "
        f"envs/{prefix}/answers.yaml.",
        "# Edit answers.yaml and rerun stellar render; manual edits trigger "
        "an overwrite prompt.",
    ]


def build(
    stage: str,
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
) -> Rendered:
    """Renders the `terraform.tfvars` of one stage.

    Args:
        stage: Stage name or alias, such as `0` or `1-resman`.
        answers: Validated answers of the environment.
        repo: The engine checkout whose sample and variables are used.
        env: Paths of the environment, for `outputs_location`.

    Returns:
        The rendered values and text.

    Raises:
        RenderError: If an override fails
            `validate.stage_override_problems`, a key is
            not a stage variable, or a sample placeholder survives.
        ValueError: If the stage name is unknown.
    """
    stage = paths.resolve_stage(stage)
    found = validate.stage_override_problems(answers, repo, stage)
    if found:
        raise RenderError(" ".join(found))
    sample = sample_lib.load(sample_path(repo, stage))
    auto = repo.auto_tfvars_keys(stage)
    built = _BUILDERS[stage](answers, repo, env, sample)
    built = {key: value for key, value in built.items() if key not in auto}
    merged = _merge(built, answers.overrides.get(stage, {}))
    declared = repo.stage_variable_names(stage)
    unknown = sorted(set(merged) - declared)
    if unknown:
        raise RenderError(
            f"{stage} declares no variable {', '.join(unknown)}; check "
            f"overrides.{stage} in answers.yaml."
        )
    found = _placeholders(merged)
    if found:
        raise RenderError(
            f"Sample placeholders survive in {stage}: {'; '.join(found)}."
        )
    order = [key for key in sample.order if key in merged]
    order += [key for key in merged if key not in order]
    values = {key: merged[key] for key in order}
    text = hcl.dumps(
        values,
        comments=_comments(stage, answers, sample, order),
        header=header(repo, stage, answers.prefix),
    )
    return Rendered(stage=stage, values=values, text=text)
