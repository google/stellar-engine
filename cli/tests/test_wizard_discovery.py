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

"""Tests for wizard discovery."""

import conftest
from stellar_engine.gcp import api
from stellar_engine.wizard import discovery


def test_discovers_everything(cloud, local_tools):
    found = discovery.discover(cloud, local_tools)
    assert found.organizations == (
        api.Organization(
            conftest.ORG_ID, conftest.DOMAIN, conftest.CUSTOMER_ID
        ),
    )
    assert found.billing_accounts == (
        api.BillingAccount(conftest.BILLING, True),
    )
    assert found.gcloud_account == conftest.USER
    assert found.gcloud_project == conftest.PROJECT
    assert found.problems == ()


def test_offline_skips_cloud(local_tools):
    found = discovery.discover(None, local_tools)
    assert found.organizations == ()
    assert found.billing_accounts == ()
    assert found.gcloud_project == conftest.PROJECT


def test_errors_become_empty_values(cloud, local_tools):
    cloud.orgs = api.AccessDeniedError("denied")
    cloud.billing_accounts = api.CredentialsError("no credentials")

    def broken():
        raise RuntimeError("gcloud crashed")

    local_tools.gcloud_account = broken
    found = discovery.discover(cloud, local_tools)
    assert found.organizations == ()
    assert found.billing_accounts == ()
    assert found.gcloud_account is None
    assert found.gcloud_project == conftest.PROJECT
    assert found.problems == (
        "Cannot read organizations: denied",
        "Cannot read billing accounts: no credentials",
        "Cannot read the gcloud account: gcloud crashed",
    )


def test_missing_gcloud_values(cloud, local_tools):
    local_tools.account = None
    local_tools.project = None
    found = discovery.discover(cloud, local_tools)
    assert found.gcloud_account is None
    assert found.gcloud_project is None
    assert found.problems == ()
