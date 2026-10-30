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

"""Tests for the `stellar env` commands."""

import pytest

import conftest
import helpers
from stellar_engine import cli

pytestmark = pytest.mark.usefixtures("isolated_home")

# What `env list` printed for the `known_envs` environments before the
# commands moved out of cli.py.
_LIST_TABLE = """\
┏━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃   ┃ Prefix ┃ Regime ┃ Region   ┃ Organization ┃
┡━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│   │ aaa    │ IL5    │ us-east4 │ 123456789012 │
│ * │ bbb    │ IL4    │ us-east4 │ 123456789012 │
└───┴────────┴────────┴──────────┴──────────────┘
"""
# The same table without a current environment.
_STALE_LIST_TABLE = """\
┏━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃  ┃ Prefix ┃ Regime ┃ Region   ┃ Organization ┃
┡━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│  │ aaa    │ IL5    │ us-east4 │ 123456789012 │
│  │ bbb    │ IL4    │ us-east4 │ 123456789012 │
└──┴────────┴────────┴──────────┴──────────────┘
"""


def test_env_list_use_show(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner, "aaa").exit_code == 0
    assert (
        helpers.init_env(
            cli_runner, "bbb", sets=("compliance.regime=IL4",)
        ).exit_code
        == 0
    )
    listing = helpers.invoke(cli_runner, "env", "list")
    assert listing.exit_code == 0, listing.output
    assert "aaa" in listing.output
    assert "IL4" in listing.output
    lines = [line for line in listing.output.splitlines() if "bbb" in line]
    assert "*" in lines[0]

    use = helpers.invoke(cli_runner, "env", "use", "aaa")
    assert use.exit_code == 0, use.output
    assert (isolated_home / "current").read_text().strip() == "aaa"
    assert helpers.invoke(cli_runner, "env", "use", "zzz").exit_code == 2

    show = helpers.invoke(cli_runner, "env", "show")
    assert show.exit_code == 0, show.output
    assert f"Home: {isolated_home} (from STELLAR_HOME)" in show.output
    assert "Environment: aaa (current)" in show.output
    assert "KMS protection level: HSM" in show.output
    assert "aaa-prod-iac-core-0" in show.output
    assert "Stage 0 phase: bootstrap" in show.output
    other = helpers.invoke(cli_runner, "env", "show", "--prefix", "bbb")
    assert "Environment: bbb\n" in other.output


def test_env_list_without_envs(cli_runner, isolated_home):
    outcome = helpers.invoke(cli_runner, "env", "list")
    assert outcome.exit_code == 0
    assert "No environments" in outcome.output


def test_env_show_without_env_exits_2(cli_runner):
    outcome = helpers.invoke(cli_runner, "env", "show")
    assert outcome.exit_code == 2
    assert "stellar init" in outcome.output


def test_home_from_flag_wins(cli_runner, isolated_home, tmp_path):
    flagged = tmp_path / "flagged"
    outcome = helpers.init_env(cli_runner, "tst", "--home", str(flagged))
    assert outcome.exit_code == 0, outcome.output
    assert (flagged / "envs" / "tst" / "answers.yaml").is_file()
    assert not isolated_home.exists()
    show = helpers.invoke(cli_runner, "env", "show", "--home", str(flagged))
    assert f"Home: {flagged} (from the --home flag)" in show.output


def test_home_defaults_into_the_engine(cli_runner, tmp_path, monkeypatch):
    monkeypatch.delenv("STELLAR_HOME")
    engine = helpers.engine_copy(tmp_path)
    args = ["--repo", str(engine)]
    outcome = cli_runner.invoke(
        cli.app,
        [
            "init",
            "--non-interactive",
            "--prefix",
            "tst",
            *helpers.set_args(),
            *args,
        ],
    )
    assert outcome.exit_code == 0, outcome.output
    home = engine / ".stellar"
    assert (home / "envs" / "tst" / "answers.yaml").is_file()
    show = cli_runner.invoke(cli.app, ["env", "show", *args])
    assert f"Home: {home} (default inside the engine checkout)" in show.output


def test_stale_current_environment(cli_runner, isolated_home):
    assert helpers.init_env(cli_runner).exit_code == 0
    (isolated_home / "current").write_text("zzz\n")
    for args in (["env", "show"], ["render"]):
        outcome = helpers.invoke(cli_runner, *args)
        assert outcome.exit_code == 2
        assert "current environment zzz no longer exists" in outcome.output
        assert "stellar env use PREFIX" in outcome.output
    listed = helpers.invoke(cli_runner, "env", "list")
    assert listed.exit_code == 0
    assert "zzz no longer exists" in listed.output
    # A plain init starts the stale prefix from scratch instead of
    # reporting a missing prefix.
    outcome = helpers.invoke(
        cli_runner, "init", "--non-interactive", *helpers.set_args()
    )
    assert outcome.exit_code == 0, outcome.output
    assert "init now creates zzz from scratch" in outcome.output
    assert helpers.load_answers(isolated_home, "zzz").prefix == "zzz"


def test_env_show_lists_existing_org_policies(cli_runner, isolated_home):
    assert (
        helpers.init_env(
            cli_runner,
            sets=("existing_org_policies=[iam.allowedPolicyMemberDomains]",),
        ).exit_code
        == 0
    )
    outcome = helpers.invoke(cli_runner, "env", "show")
    assert outcome.exit_code == 0, outcome.output
    assert "Existing organization policies" in outcome.output
    assert "  iam.allowedPolicyMemberDomains" in outcome.output


@pytest.fixture
def known_envs(cli_runner, isolated_home, monkeypatch):
    """Creates the environments aaa and bbb, and leaves bbb current.

    bbb has a tenant, an import and an existing organization policy, so
    `env show` prints every section. The fixture also pins the table width
    and turns color off, so the output is the same in every terminal.

    Returns:
        The home that holds the environments.
    """
    monkeypatch.setenv("COLUMNS", "80")
    for name in ("FORCE_COLOR", "TTY_COMPATIBLE"):
        monkeypatch.delenv(name, raising=False)
    assert helpers.init_env(cli_runner, "aaa").exit_code == 0
    outcome = helpers.init_env(
        cli_runner,
        "bbb",
        sets=(
            "compliance.regime=IL4",
            "resman.tenants.ten1={descriptive_name: tenant-1}",
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=bbb-prod-iac-core-0',
            "existing_org_policies=[iam.allowedPolicyMemberDomains]",
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    return isolated_home


def _show_header(home, prefix, current=""):
    """Returns the `env show` lines up to the derived values."""
    env = home / "envs" / prefix
    return [
        f"Home: {home} (from STELLAR_HOME)",
        f"Environment: {prefix}{current}",
        f"Answers: {env}/answers.yaml",
        f"Engine: {conftest.REPO_ROOT}",
        f"Outputs location: {env}/fast-config",
        "Stage 0 phase: bootstrap",
        "Workspaces:",
        f"  0-bootstrap: {env}/fast/stages-aw/0-bootstrap",
        f"  1-resman: {env}/fast/stages-aw/1-resman",
        "Derived values:",
        "  KMS protection level: HSM",
        "  Assured Workloads location: us-east4",
        "  Stage 0 project IDs and deletion policies:",
    ]


def test_env_list_output_is_unchanged(cli_runner, known_envs):
    outcome = helpers.invoke(cli_runner, "env", "list")
    assert outcome.exit_code == 0, outcome.output
    assert outcome.stdout == f"{_LIST_TABLE}Home: {known_envs}\n"
    assert outcome.stderr == ""


def test_env_list_output_with_a_stale_current_is_unchanged(
    cli_runner, known_envs
):
    (known_envs / "current").write_text("zzz\n")
    outcome = helpers.invoke(cli_runner, "env", "list")
    assert outcome.exit_code == 0, outcome.output
    assert outcome.stdout == f"{_STALE_LIST_TABLE}Home: {known_envs}\n"
    assert outcome.stderr == (
        f"Warning: The current environment zzz no longer exists in "
        f"{known_envs}. Run `stellar env list` to see the environments and "
        "`stellar env use PREFIX` to pick one, or pass --prefix.\n"
    )


def test_env_show_output_is_unchanged(cli_runner, known_envs):
    outcome = helpers.invoke(cli_runner, "env", "show")
    assert outcome.exit_code == 0, outcome.output
    lines = [
        *_show_header(known_envs, "bbb", " (current)"),
        "    bbb-prod-iac-core-0  ABANDON",
        "    bbb-prod-audit-logs-0  DELETE",
        "    bbb-prod-billing-exp-0  DELETE",
        "  Tenant ten1 project IDs:",
        "    bbb-prod-ten1-iac-core-0",
        "    bbb-prod-ten1-main-0",
        "    bbb-int-ten1-iac-core-0",
        "    bbb-int-ten1-main-0",
        "    bbb-test-ten1-iac-core-0",
        "    bbb-test-ten1-main-0",
        "Imports for 0-bootstrap:",
        f"  {conftest.AUTOMATION_ADDRESS} = bbb-prod-iac-core-0",
        "Existing organization policies that Stage 0 imports:",
        "  iam.allowedPolicyMemberDomains",
    ]
    assert outcome.stdout == "\n".join(lines) + "\n"
    assert outcome.stderr == ""


def test_env_show_output_of_another_env_is_unchanged(cli_runner, known_envs):
    outcome = helpers.invoke(cli_runner, "env", "show", "--prefix", "aaa")
    assert outcome.exit_code == 0, outcome.output
    lines = [
        *_show_header(known_envs, "aaa"),
        "    aaa-prod-iac-core-0  DELETE",
        "    aaa-prod-audit-logs-0  DELETE",
        "    aaa-prod-billing-exp-0  DELETE",
    ]
    assert outcome.stdout == "\n".join(lines) + "\n"
    assert outcome.stderr == ""


def test_env_show_output_with_a_stale_current_is_unchanged(
    cli_runner, known_envs
):
    (known_envs / "current").write_text("zzz\n")
    outcome = helpers.invoke(cli_runner, "env", "show")
    assert outcome.exit_code == 2
    assert outcome.stdout == f"Home: {known_envs} (from STELLAR_HOME)\n"
    assert outcome.stderr == (
        f"Error: The current environment zzz no longer exists in "
        f"{known_envs}. Run `stellar env list` to see the environments and "
        "`stellar env use PREFIX` to pick one, or pass --prefix.\n"
    )
