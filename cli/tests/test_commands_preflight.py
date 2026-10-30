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

"""Tests for the `stellar preflight` command and the root options."""

import json

import pytest

import conftest
import helpers
import stellar_engine
from stellar_engine import cli

pytestmark = pytest.mark.usefixtures("isolated_home")

BASE_ARGS = [
    "preflight",
    "--org",
    conftest.ORG_ID,
    "--billing-account",
    conftest.BILLING,
    "--project",
    conftest.PROJECT,
    "--prefix",
    "tst",
    "--regime",
    "IL5",
    "--region",
    "us-east4",
    "--repo",
    str(conftest.REPO_ROOT),
]


def test_version(cli_runner):
    outcome = cli_runner.invoke(cli.app, ["--version"])
    assert outcome.exit_code == 0
    assert stellar_engine.__version__ in outcome.output


def test_preflight_json_passes(cli_runner, fake_cloud):
    outcome = cli_runner.invoke(cli.app, [*BASE_ARGS, "--json"])
    assert outcome.exit_code == 0, outcome.output
    document = json.loads(outcome.stdout)
    assert document["summary"]["fail"] == 0
    assert document["inputs"]["prefix"] == "tst"


def test_preflight_table_fails(cli_runner, fake_cloud):
    fake_cloud.projects = {}
    outcome = cli_runner.invoke(cli.app, BASE_ARGS)
    assert outcome.exit_code == 1
    assert "Bootstrap project" in outcome.stdout


def test_strict_fails_on_warning(cli_runner, fake_cloud):
    fake_cloud.custom_roles = {"tagViewer"}
    assert cli_runner.invoke(cli.app, [*BASE_ARGS, "--json"]).exit_code == 0
    strict = cli_runner.invoke(cli.app, [*BASE_ARGS, "--json", "--strict"])
    assert strict.exit_code == 1


def test_env_vars_are_read(cli_runner, fake_cloud, monkeypatch):
    monkeypatch.setenv("STELLAR_PREFIX", "envpfx")
    args = [arg for arg in BASE_ARGS if arg not in ("--prefix", "tst")]
    outcome = cli_runner.invoke(cli.app, [*args, "--json"])
    assert json.loads(outcome.stdout)["inputs"]["prefix"] == "envpfx"


def test_group_overrides(cli_runner, fake_cloud):
    outcome = cli_runner.invoke(
        cli.app,
        [*BASE_ARGS, "--json", "--group", "gcp-devops=platform-ops"],
    )
    document = json.loads(outcome.stdout)
    assert document["inputs"]["groups"] == {"gcp-devops": "platform-ops"}
    ids = {check["check_id"] for check in document["checks"]}
    assert "groups.platform-ops@example.com" in ids


def test_bad_group_syntax(cli_runner, fake_cloud):
    outcome = cli_runner.invoke(cli.app, [*BASE_ARGS, "--group", "nonsense"])
    assert outcome.exit_code == 2
    assert "KEY=NAME" in outcome.output


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--regime", "PCI"], "Unknown regime PCI"),
        (["--group", "gcp-nope=x"], "Unknown group keys gcp-nope"),
    ],
)
def test_values_unknown_to_stage0_exit_2(cli_runner, fake_cloud, args, message):
    outcome = cli_runner.invoke(cli.app, [*BASE_ARGS, *args])
    assert outcome.exit_code == 2
    assert f"Error: {message}" in outcome.output


def test_invalid_billing_format_exits_2(cli_runner, fake_cloud):
    args = [*BASE_ARGS]
    args[args.index(conftest.BILLING)] = "not-a-billing-id"
    outcome = cli_runner.invoke(cli.app, args)
    assert outcome.exit_code == 2
    assert "billing_account" in outcome.output


def test_config_env(cli_runner, fake_cloud, tmp_path):
    config = tmp_path / "config.env"
    config.write_text("PREFIX=fromenv\nREGION=us-west1\n", encoding="utf-8")
    args = [
        "preflight",
        "--org",
        conftest.ORG_ID,
        "--config-env",
        str(config),
        "--repo",
        str(conftest.REPO_ROOT),
        "--json",
    ]
    document = json.loads(cli_runner.invoke(cli.app, args).stdout)
    assert document["inputs"]["prefix"] == "fromenv"
    assert document["inputs"]["region"] == "us-west1"


def test_billing_no_iam(cli_runner, fake_cloud):
    args = [*BASE_ARGS, "--json", "--billing-no-iam"]
    document = json.loads(cli_runner.invoke(cli.app, args).stdout)
    checks_by_id = {c["check_id"]: c for c in document["checks"]}
    assert document["inputs"]["billing_no_iam"] is True
    assert checks_by_id["billing.link"]["status"] == "pass"
    assert "iam.roles/billing.admin" not in checks_by_id


def test_service_account_with_bootstrap_user(cli_runner, fake_cloud):
    sa = "sa@example-project.iam.gserviceaccount.com"
    fake_cloud.principal = conftest.api.Principal(
        sa, conftest.api.PrincipalKind.SERVICE_ACCOUNT
    )
    args = [*BASE_ARGS, "--json", "--bootstrap-user", "admin@example.com"]
    document = json.loads(cli_runner.invoke(cli.app, args).stdout)
    checks_by_id = {c["check_id"]: c for c in document["checks"]}
    assert checks_by_id["identity.bootstrap_user"]["status"] == "pass"
    assert document["inputs"]["bootstrap_user"] == "admin@example.com"


def test_preflight_reads_answers(cli_runner, fake_cloud, isolated_home):
    outcome = helpers.init_env(
        cli_runner,
        sets=(
            "billing.no_iam=true",
            "resman.tenants.ten1={descriptive_name: tenant-1}",
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            f'imports.0-bootstrap."{conftest.LOG_EXPORT_ADDRESS}"=tst-prod-audit-logs-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    preflight = helpers.invoke(cli_runner, "preflight", "--json")
    assert preflight.exit_code in (0, 1), preflight.output
    document = json.loads(preflight.stdout)
    inputs = document["inputs"]
    assert inputs["prefix"] == "tst"
    assert inputs["org_id"] == conftest.ORG_ID
    assert inputs["billing_no_iam"] is True
    assert inputs["bootstrap_user"] == "admin@example.com"
    assert "tst-prod-ten1-iac-core-0" in inputs["tenant_project_ids"]
    assert inputs["imported_project_ids"] == [
        "tst-prod-audit-logs-0",
        "tst-prod-iac-core-0",
    ]
    ids = {check["check_id"] for check in document["checks"]}
    assert "naming.imported_projects" in ids
    assert "naming.tenant_projects" in ids


def test_preflight_flags_override_answers(cli_runner, fake_cloud):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome = helpers.invoke(
        cli_runner, "preflight", "--json", "--region", "us-west1"
    )
    document = json.loads(outcome.stdout)
    assert document["inputs"]["region"] == "us-west1"
    assert document["inputs"]["regime"] == "IL5"


def test_preflight_rejects_broken_answers(
    cli_runner, fake_cloud, isolated_home
):
    assert helpers.init_env(cli_runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text("prefix: [unclosed\n")
    outcome = helpers.invoke(cli_runner, "preflight", "--json")
    assert outcome.exit_code == 2
