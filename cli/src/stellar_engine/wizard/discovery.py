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

"""Reads wizard defaults from Google Cloud and the local gcloud setup.

Discovery only prefills prompts, so a failed call never stops the wizard:
it leaves that value empty and records why, and the operator types the
value instead.
"""

import dataclasses

from stellar_engine import tools as tools_lib
from stellar_engine.gcp import api


@dataclasses.dataclass(frozen=True)
class Discovered:
    """Defaults found for the wizard.

    Attributes:
        organizations: Organizations visible to the credentials.
        billing_accounts: Billing accounts visible to the credentials.
        gcloud_account: Active gcloud account, or None.
        gcloud_project: Active gcloud project, or None.
        problems: Why a lookup returned nothing, one sentence each.
    """

    organizations: tuple[api.Organization, ...] = ()
    billing_accounts: tuple[api.BillingAccount, ...] = ()
    gcloud_account: str | None = None
    gcloud_project: str | None = None
    problems: tuple[str, ...] = ()


def _guarded(what, call, problems, empty):
    # Any failure, including credential and transport errors the facade
    # does not translate, only costs a default, so none of them propagate.
    try:
        return call()
    except Exception as error:
        problems.append(f"Cannot read {what}: {error}")
        return empty


def discover(
    cloud: api.CloudApi | None, local_tools: tools_lib.LocalTools
) -> Discovered:
    """Looks up wizard defaults.

    Args:
        cloud: Google Cloud facade, or None to skip cloud lookups, as
            `stellar init --offline` does.
        local_tools: Local tool queries for the gcloud account and project.

    Returns:
        The defaults found; lookups that failed are empty.
    """
    problems = []
    organizations = []
    billing_accounts = []
    if cloud is not None:
        organizations = _guarded(
            "organizations", cloud.search_organizations, problems, []
        )
        billing_accounts = _guarded(
            "billing accounts", cloud.list_billing_accounts, problems, []
        )
    return Discovered(
        organizations=tuple(organizations),
        billing_accounts=tuple(billing_accounts),
        gcloud_account=_guarded(
            "the gcloud account", local_tools.gcloud_account, problems, None
        ),
        gcloud_project=_guarded(
            "the gcloud project", local_tools.gcloud_project, problems, None
        ),
        problems=tuple(problems),
    )
