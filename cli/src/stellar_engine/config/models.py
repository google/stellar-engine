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

"""Pydantic model of `answers.yaml`, the per-environment deployment answers.

Rules that need no repository live here. Rules that read limits or lists
from the repository, such as the prefix length, live in `validate`. Fields
that Terraform derives on its own default to None and `derive` computes
them, so they are recomputed when a seeded environment changes regime.
"""

import re
from typing import Annotated, Any, Literal

import pydantic

from stellar_engine import paths
from stellar_engine import patterns

EMAIL_PATTERN = patterns.EMAIL
# The length limit comes from the repository, so `validate` checks it.
PREFIX_PATTERN = patterns.PREFIX
# The Stage 0 prefix limit, only for the JSON schema that editors read; a
# test keeps it equal to the repository limit that `validate` enforces.
PREFIX_SCHEMA_MAX_LENGTH = 7
TENANT_KEY_PATTERN = r"^[a-z][a-z0-9-]*$"
# Stage 1 lowercases `<env>-<tenant>` into project and service account IDs,
# so env keys may use capitals but only characters valid in those IDs.
ENV_KEY_PATTERN = r"^[A-Za-z][A-Za-z0-9-]*$"
# An organization policy constraint such as `iam.allowedPolicyMemberDomains`.
CONSTRAINT_PATTERN = r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$"
# The Stage 0 phases: the first apply, then every apply after the state
# migration. See `render.phase`.
STAGE0_BOOTSTRAP = "bootstrap"
STAGE0_FINAL = "final"
Stage0Phase = Literal["bootstrap", "final"]

_NonEmpty = Annotated[str, pydantic.Field(min_length=1)]
_Constraint = Annotated[str, pydantic.Field(pattern=CONSTRAINT_PATTERN)]


class _Model(pydantic.BaseModel):
    """Base model that rejects unknown keys.

    YAML and `--set` parse an unquoted organization ID as a number, so
    numbers are accepted where the model expects a string.
    """

    model_config = pydantic.ConfigDict(
        extra="forbid", coerce_numbers_to_str=True
    )


class Organization(_Model):
    """The Google Cloud organization that Stage 0 deploys into."""

    id: str = pydantic.Field(pattern=patterns.ORG_ID)
    domain: str = pydantic.Field(min_length=1)
    customer_id: str = pydantic.Field(pattern=r"^C[0-9a-zA-Z]+$")


class Billing(_Model):
    """The billing account and how Stage 0 manages its IAM.

    Attributes:
        account_id: Billing account ID.
        is_org_level: False when the account belongs to another
            organization.
        no_iam: True when Stage 0 must not manage billing IAM, for example
            on a shared billing account the deployer cannot administer.
        external_grant: True when someone outside Terraform grants billing
            access before Stages 1 to 3.
    """

    account_id: str = pydantic.Field(pattern=patterns.BILLING_ACCOUNT)
    is_org_level: bool = True
    no_iam: bool = False
    external_grant: bool = False


class BillingOverride(_Model):
    """Quota projects for project billing linkage under a user account."""

    project: str = pydantic.Field(min_length=1)
    billing_project: str = pydantic.Field(min_length=1)


class Compliance(_Model):
    """The Assured Workloads regime and location.

    Attributes:
        regime: Regime name in capitals, such as `IL5`.
        location: Assured Workloads location. None uses the region.
        allow_unlisted_region: Accepts a region that the regions table does
            not list for the regime, for when Google adds a region first.
    """

    regime: str = pydantic.Field(pattern=patterns.REGIME)
    location: str | None = None
    allow_unlisted_region: bool = False


class Logging(_Model):
    """Organization log sink destination and log bucket retention."""

    sink_type: Literal["logging", "storage", "bigquery", "pubsub"] = "logging"
    retention_days: int | None = pydantic.Field(default=None, ge=1)


class Budget(_Model):
    """Optional budget on the Assured Workloads folder."""

    amount: int | None = pydantic.Field(default=None, ge=1)


class OrgPolicies(_Model):
    """Organization policy inputs that Stage 0 exposes."""

    allowed_policy_member_domains: list[str] = pydantic.Field(
        default_factory=list
    )


class EnvFolder(_Model):
    """A Stage 1 environment folder.

    Attributes:
        admin: Admin email. None uses the organization admins group.
    """

    admin: str | None = None


class TenantLocations(_Model):
    """Storage and KMS locations of a tenant."""

    gcs: str = pydantic.Field(min_length=1)
    kms: str = pydantic.Field(min_length=1)


class Tenant(_Model):
    """A Stage 1 lightweight tenant.

    Attributes:
        descriptive_name: Human readable tenant name.
        admin_principal: IAM principal of the tenant admins. None uses the
            `gcp-devops` group.
        locations: Tenant locations. None uses the region for both.
    """

    descriptive_name: str = pydantic.Field(min_length=1)
    admin_principal: str | None = None
    locations: TenantLocations | None = None


def _default_envs():
    return {"Prod": EnvFolder(), "Int": EnvFolder(), "Test": EnvFolder()}


class Resman(_Model):
    """Stage 1 environments and tenants."""

    envs: dict[str, EnvFolder] = pydantic.Field(default_factory=_default_envs)
    tenants: dict[str, Tenant] = pydantic.Field(default_factory=dict)

    @pydantic.field_validator("envs")
    @classmethod
    def _check_envs(cls, envs):
        lowered = {}
        for key in envs:
            if not re.match(ENV_KEY_PATTERN, key):
                raise ValueError(
                    f"Env key {key!r} must start with a letter and use only "
                    "letters, digits and hyphens"
                )
            # Stage 1 lowercases env keys into project IDs, so `Prod` and
            # `prod` would create the same projects.
            if key.lower() in lowered:
                raise ValueError(
                    f"Env keys {lowered[key.lower()]!r} and {key!r} differ "
                    "only in case"
                )
            lowered[key.lower()] = key
        return envs

    @pydantic.field_validator("tenants")
    @classmethod
    def _check_tenants(cls, tenants):
        for key in tenants:
            if not re.match(TENANT_KEY_PATTERN, key):
                raise ValueError(
                    f"Tenant key {key!r} must start with a lowercase letter "
                    "and use only lowercase letters, digits and hyphens"
                )
        return tenants


class Engine(_Model):
    """The engine checkout that renders this environment.

    Attributes:
        path: Absolute path of the checkout.
    """

    path: str = pydantic.Field(min_length=1)


class Answers(_Model):
    """Every answer that Stages 0 and 1 need for one environment.

    Attributes:
        overrides: Stage name to raw tfvars that the renderer deep-merges
            last, for variables the model does not cover, such as the
            Stage 0 `iam` map.
        imports: Stage name to a map of Terraform resource address to
            import ID, for resources that exist before the first apply,
            such as projects pre-created where billing linkage needs a
            human.
        keep_imported_projects: Whether `terraform destroy` of Stage 0
            keeps the Stage 0 projects that `imports` adopts, because
            someone else created them. stellar then sets their deletion
            policy to ABANDON, when the Stage 0 version supports it.
        existing_org_policies: Constraints whose organization policies
            exist before Stage 0 and that Stage 0 declares, which the final
            Stage 0 apply imports. `stellar imports scan` fills it.
        stage0_phase: Which Stage 0 apply comes next. The bootstrap phase
            sets `bootstrap_user` through a generated file; the final phase,
            after the state migration, leaves it unset.
    """

    schema_version: Literal[1] = 1
    prefix: str = pydantic.Field(
        pattern=PREFIX_PATTERN,
        json_schema_extra={"maxLength": PREFIX_SCHEMA_MAX_LENGTH},
    )
    engine: Engine | None = None
    organization: Organization
    billing: Billing
    billing_override: BillingOverride | None = None
    bootstrap_project: str = pydantic.Field(pattern=patterns.PROJECT_ID)
    bootstrap_user: str | None = pydantic.Field(
        default=None, pattern=EMAIL_PATTERN
    )
    stage0_phase: Stage0Phase = pydantic.Field(
        default=STAGE0_BOOTSTRAP,
        description=(
            "The next Stage 0 apply. bootstrap sets bootstrap_user for the "
            "first apply; final leaves it unset after the state migration, "
            "so Stage 0 manages the organization policies. Never return to "
            "bootstrap after a final apply."
        ),
    )
    region: str = pydantic.Field(min_length=1)
    compliance: Compliance
    kms_protection_level: Literal["SOFTWARE", "HSM"] | None = None
    alert_email: str = pydantic.Field(pattern=EMAIL_PATTERN)
    essential_contacts: str | dict[str, list[str]] | None = None
    groups: dict[str, str] = pydantic.Field(default_factory=dict)
    logging: Logging = pydantic.Field(default_factory=Logging)
    budget: Budget = pydantic.Field(default_factory=Budget)
    org_policies: OrgPolicies = pydantic.Field(default_factory=OrgPolicies)
    resman: Resman = pydantic.Field(default_factory=Resman)
    overrides: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    imports: dict[str, dict[str, _NonEmpty]] = pydantic.Field(
        default_factory=dict
    )
    keep_imported_projects: bool = pydantic.Field(
        default=True,
        description=(
            "Keep the imported Stage 0 projects when Terraform destroys "
            "Stage 0, through an ABANDON deletion policy."
        ),
    )
    existing_org_policies: list[_Constraint] = pydantic.Field(
        default_factory=list
    )

    @pydantic.field_validator("existing_org_policies")
    @classmethod
    def _sort_constraints(cls, value):
        return sorted(set(value))

    @pydantic.field_validator("overrides", "imports")
    @classmethod
    def _check_stage_keys(cls, value, info):
        unknown = sorted(set(value) - set(paths.STAGES))
        if unknown:
            raise ValueError(
                f"Unknown stage {', '.join(unknown)} in {info.field_name}; "
                f"use one of {', '.join(paths.STAGES)}"
            )
        return value
