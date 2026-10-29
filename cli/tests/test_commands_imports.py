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

"""Tests for the `stellar imports scan` command."""

import pytest

import conftest
import helpers

pytestmark = pytest.mark.usefixtures("isolated_home")

_SCANNED = [
    "storage.uniformBucketLevelAccess",
    "custom.kmsRotation",
    "unmanaged.constraint",
    "iam.allowedPolicyMemberDomains",
]


def test_imports_scan_without_environment_exits_2(cli_runner, fake_cloud):
    outcome = helpers.invoke(cli_runner, "imports", "scan")
    assert outcome.exit_code == 2
    assert "stellar init" in outcome.output


def test_imports_scan_saves_declared_policies(
    cli_runner, fake_cloud, isolated_home, fake_tools
):
    assert helpers.init_env(cli_runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text("# my note\n" + path.read_text())
    fake_cloud.org_policies = _SCANNED
    outcome = helpers.invoke(cli_runner, "imports", "scan")
    assert outcome.exit_code == 0, outcome.output
    assert ("org_policies", conftest.ORG_ID) in fake_cloud.calls
    for name in _SCANNED:
        assert name in outcome.output
    assert "Saved 2 organization policies" in outcome.output
    assert "Next: stellar render" in outcome.output
    assert helpers.load_answers(isolated_home).existing_org_policies == [
        "iam.allowedPolicyMemberDomains",
        "storage.uniformBucketLevelAccess",
    ]
    assert "# my note" in path.read_text()
    assert conftest.mode(path) == 0o600

    rerun = helpers.invoke(cli_runner, "imports", "scan")
    assert rerun.exit_code == 0, rerun.output
    assert "already lists these policies" in rerun.output

    render = helpers.invoke(cli_runner, "render", "--stage", "0")
    assert render.exit_code == 0, render.output
    text = (
        helpers.workspace(isolated_home, "0-bootstrap")
        / "0-bootstrap-imports.tf"
    )
    assert '"storage.uniformBucketLevelAccess",' in text.read_text()


def test_imports_scan_clears_policies_that_are_gone(
    cli_runner, fake_cloud, isolated_home
):
    assert (
        helpers.init_env(
            cli_runner, sets=("existing_org_policies=[unmanaged.constraint]",)
        ).exit_code
        == 2
    )
    assert (
        helpers.init_env(
            cli_runner,
            sets=("existing_org_policies=[iam.allowedPolicyMemberDomains]",),
        ).exit_code
        == 0
    )
    # A newer engine may drop a declared policy; the scan still runs.
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text(
        path.read_text().replace(
            "iam.allowedPolicyMemberDomains", "unmanaged.constraint"
        )
    )
    assert helpers.invoke(cli_runner, "render").exit_code == 2
    outcome = helpers.invoke(cli_runner, "imports", "scan")
    assert outcome.exit_code == 0, outcome.output
    assert "has no organization policies" in outcome.output
    assert helpers.load_answers(isolated_home).existing_org_policies == []


def test_imports_scan_refuses_import_defaults(
    cli_runner, fake_cloud, isolated_home
):
    assert (
        helpers.init_env(
            cli_runner,
            sets=(
                "overrides.0-bootstrap.org_policies_config="
                "{import_defaults: true}",
            ),
        ).exit_code
        == 0
    )
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    before = path.read_text()
    fake_cloud.org_policies = ["iam.allowedPolicyMemberDomains"]
    outcome = helpers.invoke(cli_runner, "imports", "scan")
    assert outcome.exit_code == 2
    assert "import_defaults" in outcome.output
    assert path.read_text() == before


def test_imports_scan_prints_the_table_before_answer_problems(
    cli_runner, fake_cloud, isolated_home
):
    sets = (
        "overrides.0-bootstrap.org_policies_config={import_defaults: true}",
    )
    assert helpers.init_env(cli_runner, sets=sets).exit_code == 0
    fake_cloud.org_policies = ["iam.allowedPolicyMemberDomains"]
    outcome = helpers.invoke(cli_runner, "imports", "scan")
    assert outcome.exit_code == 2
    assert "iam.allowedPolicyMemberDomains" in outcome.stdout
    assert outcome.stderr.startswith("Error: The answers have problems:")


def test_imports_scan_follows_the_regime(cli_runner, fake_cloud, isolated_home):
    assert (
        helpers.init_env(
            cli_runner, sets=("compliance.regime=FEDRAMP_MODERATE",)
        ).exit_code
        == 0
    )
    gated = "compute.managed.restrictProtocolForwardingCreationForTypes"
    fake_cloud.org_policies = [gated, "custom.myOrgRule"]
    outcome = helpers.invoke(cli_runner, "imports", "scan")
    assert outcome.exit_code == 0, outcome.output
    # The table wraps its cells, so check single words.
    assert "regime" in outcome.output
    assert "creates" not in outcome.output
    assert helpers.load_answers(isolated_home).existing_org_policies == []


def test_imports_scan_reports_cloud_errors(
    cli_runner, fake_cloud, isolated_home
):
    assert helpers.init_env(cli_runner).exit_code == 0
    fake_cloud.org_policies = conftest.api.AccessDeniedError(
        "no orgpolicy access"
    )
    outcome = helpers.invoke(cli_runner, "imports", "scan")
    assert outcome.exit_code == 1
    assert "no orgpolicy access" in outcome.output
