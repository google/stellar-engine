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

"""Tests for the `stellar` command line."""

import json
import os
import pathlib

import pytest
from ruamel import yaml
from typer import testing

import conftest
import helpers
import stellar_engine
from stellar_engine import cli
from stellar_engine import paths
from stellar_engine.config import answers as answers_lib

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


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Points every command at a temp home outside the repository."""
    home = tmp_path / "home"
    monkeypatch.setenv("STELLAR_HOME", str(home))
    monkeypatch.delenv("STELLAR_PREFIX", raising=False)
    return home


@pytest.fixture
def fake_cloud(monkeypatch):
    cloud = conftest.FakeCloud()
    monkeypatch.setattr(cli.live, "LiveCloudApi", lambda: cloud)
    monkeypatch.setattr(cli.tools_lib, "SystemTools", conftest.FakeTools)
    monkeypatch.delenv("GOOGLE_IMPERSONATE_SERVICE_ACCOUNT", raising=False)
    return cloud


@pytest.fixture
def runner():
    return testing.CliRunner()


def test_version(runner):
    outcome = runner.invoke(cli.app, ["--version"])
    assert outcome.exit_code == 0
    assert stellar_engine.__version__ in outcome.output


def test_preflight_json_passes(runner, fake_cloud):
    outcome = runner.invoke(cli.app, [*BASE_ARGS, "--json"])
    assert outcome.exit_code == 0, outcome.output
    document = json.loads(outcome.stdout)
    assert document["summary"]["fail"] == 0
    assert document["inputs"]["prefix"] == "tst"


def test_preflight_table_fails(runner, fake_cloud):
    fake_cloud.projects = {}
    outcome = runner.invoke(cli.app, BASE_ARGS)
    assert outcome.exit_code == 1
    assert "Bootstrap project" in outcome.stdout


def test_strict_fails_on_warning(runner, fake_cloud):
    fake_cloud.custom_roles = {"tagViewer"}
    assert runner.invoke(cli.app, [*BASE_ARGS, "--json"]).exit_code == 0
    strict = runner.invoke(cli.app, [*BASE_ARGS, "--json", "--strict"])
    assert strict.exit_code == 1


def test_env_vars_are_read(runner, fake_cloud, monkeypatch):
    monkeypatch.setenv("STELLAR_PREFIX", "envpfx")
    args = [arg for arg in BASE_ARGS if arg not in ("--prefix", "tst")]
    outcome = runner.invoke(cli.app, [*args, "--json"])
    assert json.loads(outcome.stdout)["inputs"]["prefix"] == "envpfx"


def test_group_overrides(runner, fake_cloud):
    outcome = runner.invoke(
        cli.app,
        [*BASE_ARGS, "--json", "--group", "gcp-devops=platform-ops"],
    )
    document = json.loads(outcome.stdout)
    assert document["inputs"]["groups"] == {"gcp-devops": "platform-ops"}
    ids = {check["check_id"] for check in document["checks"]}
    assert "groups.platform-ops@example.com" in ids


def test_bad_group_syntax(runner, fake_cloud):
    outcome = runner.invoke(cli.app, [*BASE_ARGS, "--group", "nonsense"])
    assert outcome.exit_code == 2
    assert "KEY=NAME" in outcome.output


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--regime", "PCI"], "Unknown regime PCI"),
        (["--group", "gcp-nope=x"], "Unknown group keys gcp-nope"),
    ],
)
def test_values_unknown_to_stage0_exit_2(runner, fake_cloud, args, message):
    outcome = runner.invoke(cli.app, [*BASE_ARGS, *args])
    assert outcome.exit_code == 2
    assert f"Error: {message}" in outcome.output


def test_invalid_billing_format_exits_2(runner, fake_cloud):
    args = [*BASE_ARGS]
    args[args.index(conftest.BILLING)] = "not-a-billing-id"
    outcome = runner.invoke(cli.app, args)
    assert outcome.exit_code == 2
    assert "billing_account" in outcome.output


def test_config_env(runner, fake_cloud, tmp_path):
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
    document = json.loads(runner.invoke(cli.app, args).stdout)
    assert document["inputs"]["prefix"] == "fromenv"
    assert document["inputs"]["region"] == "us-west1"


def test_billing_no_iam(runner, fake_cloud):
    args = [*BASE_ARGS, "--json", "--billing-no-iam"]
    document = json.loads(runner.invoke(cli.app, args).stdout)
    checks_by_id = {c["check_id"]: c for c in document["checks"]}
    assert document["inputs"]["billing_no_iam"] is True
    assert checks_by_id["billing.link"]["status"] == "pass"
    assert "iam.roles/billing.admin" not in checks_by_id


def test_service_account_with_bootstrap_user(runner, fake_cloud):
    sa = "sa@example-project.iam.gserviceaccount.com"
    fake_cloud.principal = conftest.api.Principal(
        sa, conftest.api.PrincipalKind.SERVICE_ACCOUNT
    )
    args = [*BASE_ARGS, "--json", "--bootstrap-user", "admin@example.com"]
    document = json.loads(runner.invoke(cli.app, args).stdout)
    checks_by_id = {c["check_id"]: c for c in document["checks"]}
    assert checks_by_id["identity.bootstrap_user"]["status"] == "pass"
    assert document["inputs"]["bootstrap_user"] == "admin@example.com"


# Answers for a complete IL5 environment, as `init --set` assignments.
REQUIRED_SETS = [
    f"organization.id={conftest.ORG_ID}",
    f"organization.domain={conftest.DOMAIN}",
    f"organization.customer_id={conftest.CUSTOMER_ID}",
    f"billing.account_id={conftest.BILLING}",
    f"bootstrap_project={conftest.PROJECT}",
    "region=us-east4",
    "compliance.regime=IL5",
    "alert_email=alerts@example.com",
    "bootstrap_user=admin@example.com",
]


def _sets(*assignments):
    args = []
    for assignment in [*REQUIRED_SETS, *assignments]:
        args += ["--set", assignment]
    return args


def _init(runner, prefix: str | None = "tst", *extra, sets=()):
    args = [
        "init",
        "--non-interactive",
        "--repo",
        str(conftest.REPO_ROOT),
        *(["--prefix", prefix] if prefix else []),
        *_sets(*sets),
        *extra,
    ]
    return runner.invoke(cli.app, args)


def _invoke(runner, *args):
    return runner.invoke(cli.app, [*args, "--repo", str(conftest.REPO_ROOT)])


def _answers(home, prefix="tst"):
    return answers_lib.load(home / "envs" / prefix / "answers.yaml")


def _workspace(home, stage, prefix="tst"):
    return paths.stage_dir(home / "envs" / prefix, stage)


@pytest.fixture
def fake_tools(monkeypatch):
    monkeypatch.setattr(cli.tools_lib, "SystemTools", conftest.FakeTools)


def test_init_non_interactive_with_sets(runner, isolated_home):
    outcome = _init(
        runner,
        sets=(
            "billing.no_iam=true",
            "org_policies.allowed_policy_member_domains=[is:C0AAAAAAA, "
            '"is:principalSet://iam.googleapis.com/organizations/'
            f'{conftest.ORG_ID}"]',
            "resman.tenants.ten1={descriptive_name: tenant-1}",
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            'overrides.0-bootstrap.iam={"roles/viewer": '
            '["user:admin@example.com"]}',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    answers = _answers(isolated_home)
    assert answers.organization.id == conftest.ORG_ID
    assert answers.billing.no_iam is True
    assert answers.org_policies.allowed_policy_member_domains[1].startswith(
        "is:principalSet://"
    )
    assert answers.resman.tenants["ten1"].descriptive_name == "tenant-1"
    assert answers.imports == {
        "0-bootstrap": {conftest.AUTOMATION_ADDRESS: "tst-prod-iac-core-0"}
    }
    assert answers.overrides["0-bootstrap"]["iam"] == {
        "roles/viewer": ["user:admin@example.com"]
    }
    assert answers.engine is not None
    assert answers.engine.path == str(conftest.REPO_ROOT)
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    assert conftest.mode(path) == 0o600
    assert (isolated_home / "answers.schema.json").is_file()
    assert (isolated_home / ".gitignore").is_file()
    assert (isolated_home / "current").read_text().strip() == "tst"
    assert "Next: stellar render" in outcome.output


def test_init_reports_every_problem(runner, isolated_home):
    outcome = _invoke(
        runner,
        "init",
        "--non-interactive",
        "--prefix",
        "tst",
        "--set",
        "region=us-east4",
    )
    assert outcome.exit_code == 2
    for field in ("organization", "billing", "compliance", "alert_email"):
        assert field in outcome.output
    assert not (isolated_home / "envs" / "tst").exists()


def test_init_rejects_repo_rules(runner, isolated_home):
    outcome = _init(runner, sets=("region=europe-west1",))
    assert outcome.exit_code == 2
    assert "region europe-west1" in outcome.output


def test_init_malformed_set_exits_2(runner):
    outcome = _init(runner, sets=("nonsense",))
    assert outcome.exit_code == 2
    assert "KEY=VALUE" in outcome.output


def test_section_needs_interactive(runner):
    outcome = _init(runner, "tst", "--section", "groups")
    assert outcome.exit_code == 2
    assert "interactive" in outcome.output


def test_init_rerun_keeps_comments(runner, isolated_home):
    assert _init(runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    text = path.read_text().replace(
        "region: us-east4", "# Closest to the operators.\nregion: us-east4"
    )
    path.write_text(text)
    outcome = _invoke(
        runner, "init", "--non-interactive", "--set", "budget.amount=100"
    )
    assert outcome.exit_code == 0, outcome.output
    saved = path.read_text()
    assert "# Closest to the operators.\nregion: us-east4" in saved
    assert _answers(isolated_home).budget.amount == 100


def test_init_refuses_to_replace_another_env(runner):
    assert _init(runner).exit_code == 0
    outcome = _init(runner, None, "--answers-from", "tst", sets=("prefix=tst",))
    assert outcome.exit_code == 2
    assert "already exists" in outcome.output


def test_answers_from_seeds_and_notes_regime_change(runner, isolated_home):
    first = _init(
        runner,
        sets=(
            "kms_protection_level=HSM",
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
        ),
    )
    assert first.exit_code == 0, first.output
    outcome = _invoke(
        runner,
        "init",
        "--non-interactive",
        "--prefix",
        "new",
        "--answers-from",
        "tst",
        "--set",
        "compliance.regime=FEDRAMP_MODERATE",
    )
    assert outcome.exit_code == 0, outcome.output
    assert "Seeding from" in outcome.output
    assert "kms_protection_level HSM is explicit" in outcome.output
    assert "the copy drops the imports" in outcome.output
    seeded = _answers(isolated_home, "new")
    assert seeded.prefix == "new"
    assert seeded.organization.domain == conftest.DOMAIN
    assert seeded.compliance.regime == "FEDRAMP_MODERATE"
    assert seeded.imports == {}
    assert (isolated_home / "current").read_text().strip() == "new"


def test_answers_from_a_file(runner, isolated_home, tmp_path):
    assert _init(runner).exit_code == 0
    source = tmp_path / "elsewhere.yaml"
    source.write_text(
        (isolated_home / "envs" / "tst" / "answers.yaml").read_text()
    )
    outcome = _invoke(
        runner,
        "init",
        "--non-interactive",
        "--prefix",
        "oth",
        "--answers-from",
        str(source),
    )
    assert outcome.exit_code == 0, outcome.output
    assert _answers(isolated_home, "oth").region == "us-east4"


def test_new_prefix_suggests_one(runner, isolated_home):
    assert _init(runner).exit_code == 0
    outcome = _invoke(
        runner,
        "init",
        "--non-interactive",
        "--answers-from",
        "tst",
        "--new-prefix",
    )
    assert outcome.exit_code == 0, outcome.output
    current = (isolated_home / "current").read_text().strip()
    assert current != "tst"
    assert current.startswith("tst")
    assert len(current) <= 7
    assert f"Suggested prefix {current}." in outcome.output
    assert _answers(isolated_home, current).prefix == current


def test_interactive_init_runs_the_wizard(runner, isolated_home, monkeypatch):
    calls = {}

    def fake_run(data, *, prompter, repo, discovered, sections):
        calls["sections"] = sections
        calls["discovered"] = discovered
        return {**data, "alert_email": "wizard@example.com"}

    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: True)
    monkeypatch.setattr(cli.flow, "run", fake_run)
    monkeypatch.setattr(cli.tools_lib, "SystemTools", conftest.FakeTools)
    outcome = runner.invoke(
        cli.app,
        [
            "init",
            "--prefix",
            "tst",
            "--offline",
            "--section",
            "contacts",
            *_sets(),
            "--repo",
            str(conftest.REPO_ROOT),
        ],
    )
    assert outcome.exit_code == 0, outcome.output
    assert calls["sections"] == ["contacts"]
    assert calls["discovered"].organizations == ()
    assert calls["discovered"].gcloud_account == conftest.USER
    assert _answers(isolated_home).alert_email == "wizard@example.com"


def test_env_list_use_show(runner, isolated_home):
    assert _init(runner, "aaa").exit_code == 0
    assert _init(runner, "bbb", sets=("compliance.regime=IL4",)).exit_code == 0
    listing = _invoke(runner, "env", "list")
    assert listing.exit_code == 0, listing.output
    assert "aaa" in listing.output
    assert "IL4" in listing.output
    lines = [line for line in listing.output.splitlines() if "bbb" in line]
    assert "*" in lines[0]

    use = _invoke(runner, "env", "use", "aaa")
    assert use.exit_code == 0, use.output
    assert (isolated_home / "current").read_text().strip() == "aaa"
    assert _invoke(runner, "env", "use", "zzz").exit_code == 2

    show = _invoke(runner, "env", "show")
    assert show.exit_code == 0, show.output
    assert f"Home: {isolated_home} (from STELLAR_HOME)" in show.output
    assert "Environment: aaa (current)" in show.output
    assert "KMS protection level: HSM" in show.output
    assert "aaa-prod-iac-core-0" in show.output
    assert "Stage 0 phase: bootstrap" in show.output
    other = _invoke(runner, "env", "show", "--prefix", "bbb")
    assert "Environment: bbb\n" in other.output


def test_env_list_without_envs(runner, isolated_home):
    outcome = _invoke(runner, "env", "list")
    assert outcome.exit_code == 0
    assert "No environments" in outcome.output


def test_env_show_without_env_exits_2(runner):
    outcome = _invoke(runner, "env", "show")
    assert outcome.exit_code == 2
    assert "stellar init" in outcome.output


def test_home_from_flag_wins(runner, isolated_home, tmp_path):
    flagged = tmp_path / "flagged"
    outcome = _init(runner, "tst", "--home", str(flagged))
    assert outcome.exit_code == 0, outcome.output
    assert (flagged / "envs" / "tst" / "answers.yaml").is_file()
    assert not isolated_home.exists()
    show = _invoke(runner, "env", "show", "--home", str(flagged))
    assert f"Home: {flagged} (from the --home flag)" in show.output


def _engine_copy(tmp_path):
    """Links the repository's top-level entries into a fresh engine root.

    The default home lives inside the engine checkout, so the test needs a
    checkout it may write into.
    """
    engine = tmp_path / "engine"
    engine.mkdir()
    for entry in conftest.REPO_ROOT.iterdir():
        if entry.name not in (".git", ".stellar"):
            (engine / entry.name).symlink_to(entry)
    return engine


def test_home_defaults_into_the_engine(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("STELLAR_HOME")
    engine = _engine_copy(tmp_path)
    args = ["--repo", str(engine)]
    outcome = runner.invoke(
        cli.app,
        ["init", "--non-interactive", "--prefix", "tst", *_sets(), *args],
    )
    assert outcome.exit_code == 0, outcome.output
    home = engine / ".stellar"
    assert (home / "envs" / "tst" / "answers.yaml").is_file()
    show = runner.invoke(cli.app, ["env", "show", *args])
    assert f"Home: {home} (default inside the engine checkout)" in show.output


def test_render_creates_workspace_tfvars_and_imports(
    runner, isolated_home, fake_tools
):
    assert (
        _init(
            runner,
            sets=(
                f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            ),
        ).exit_code
        == 0
    )
    outcome = _invoke(runner, "render")
    assert outcome.exit_code == 0, outcome.output
    workspace = _workspace(isolated_home, "0-bootstrap")
    tfvars = workspace / "terraform.tfvars"
    assert 'prefix = "tst"' in tfvars.read_text()
    assert conftest.mode(tfvars) == 0o600
    imports_file = workspace / "0-bootstrap-imports.tf"
    assert "tst-prod-iac-core-0" in imports_file.read_text()
    assert (workspace / "main.tf").is_symlink()
    # The home lives outside the repository, so the links are absolute.
    target = pathlib.Path(os.readlink(workspace / "main.tf"))
    assert target.is_absolute()
    assert target.is_relative_to(conftest.REPO_ROOT)
    assert (workspace / "0-bootstrap-providers.tf").is_file()
    assert (
        _workspace(isolated_home, "1-resman") / "terraform.tfvars"
    ).is_file()
    assert f"created    {tfvars}" in outcome.output
    assert f"created    {imports_file}" in outcome.output
    assert f"terraform -chdir={workspace} init" in outcome.output
    phase_file = workspace / "0-bootstrap-phase.auto.tfvars"
    assert 'bootstrap_user = "admin@example.com"' in phase_file.read_text()
    assert conftest.mode(phase_file) == 0o600
    assert f"created    {phase_file}" in outcome.output
    assert f"terraform -chdir={workspace} plan -out=s0.tfplan" in (
        outcome.output
    )
    assert f"terraform -chdir={workspace} apply s0.tfplan" in outcome.output
    assert "-var" not in outcome.output
    assert "stellar init --set stage0_phase=final" in outcome.output
    assert "1-resman waits for Stage 0 outputs" in outcome.output


def test_render_rerun_is_unchanged(runner, isolated_home, fake_tools):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    again = _invoke(runner, "render")
    assert again.exit_code == 0, again.output
    assert "created" not in again.output
    # The two tfvars files and the Stage 0 phase file.
    assert again.output.count("  unchanged  ") == 3


def test_render_one_stage_by_alias(runner, isolated_home, fake_tools):
    assert _init(runner).exit_code == 0
    outcome = _invoke(runner, "render", "--stage", "0")
    assert outcome.exit_code == 0, outcome.output
    assert (
        _workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    ).exists()
    assert not _workspace(isolated_home, "1-resman").exists()
    assert _invoke(runner, "render", "--stage", "9").exit_code == 2


def test_render_removes_dropped_imports(runner, isolated_home, fake_tools):
    assert (
        _init(
            runner,
            sets=(
                f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            ),
        ).exit_code
        == 0
    )
    assert _invoke(runner, "render").exit_code == 0
    rerun = _invoke(runner, "init", "--non-interactive", "--set", "imports={}")
    assert rerun.exit_code == 0, rerun.output
    outcome = _invoke(runner, "render")
    imports_file = _workspace(isolated_home, "0-bootstrap") / (
        "0-bootstrap-imports.tf"
    )
    assert f"removed    {imports_file}" in outcome.output
    assert not imports_file.exists()


def test_render_warns_on_billing_export_import(
    runner, isolated_home, fake_tools
):
    outcome = _init(
        runner,
        sets=(
            "billing.no_iam=true",
            f'imports.0-bootstrap."{conftest.BILLING_EXPORT_ADDRESS}"=tst-prod-billing-exp-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    assert "Warning: imports.0-bootstrap" in outcome.output
    rendered = _invoke(runner, "render")
    assert rendered.exit_code == 0
    assert "billing export project" in rendered.output


def test_render_manual_edit_exits_3(runner, isolated_home, fake_tools):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    tfvars = _workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    edited = tfvars.read_text() + "# operator note\n"
    tfvars.write_text(edited)
    outcome = _invoke(runner, "render")
    assert outcome.exit_code == 3
    assert "manual edits" in outcome.output
    assert tfvars.read_text() == edited
    # The other stage still renders.
    assert "1-resman     unchanged" in outcome.output


def test_render_force_backs_up(runner, isolated_home, fake_tools):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    workspace = _workspace(isolated_home, "0-bootstrap")
    tfvars = workspace / "terraform.tfvars"
    rendered = tfvars.read_text()
    tfvars.write_text(rendered + "# operator note\n")
    outcome = _invoke(runner, "render", "--force")
    assert outcome.exit_code == 0, outcome.output
    assert tfvars.read_text() == rendered
    backups = list(workspace.glob("terraform.tfvars.backup.*"))
    assert len(backups) == 1
    assert backups[0].read_text().endswith("# operator note\n")
    assert f"backup {backups[0]}" in outcome.output


def test_render_interactive_confirm(
    runner, isolated_home, fake_tools, monkeypatch
):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    tfvars = _workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    tfvars.write_text(tfvars.read_text() + "# operator note\n")
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: True)
    declined = runner.invoke(
        cli.app,
        ["render", "--stage", "0", "--repo", str(conftest.REPO_ROOT)],
        input="n\n",
    )
    assert declined.exit_code == 0, declined.output
    assert "skipped" in declined.output
    assert tfvars.read_text().endswith("# operator note\n")
    accepted = runner.invoke(
        cli.app,
        ["render", "--stage", "0", "--repo", str(conftest.REPO_ROOT)],
        input="y\n",
    )
    assert accepted.exit_code == 0, accepted.output
    assert not tfvars.read_text().endswith("# operator note\n")


def test_render_diff_writes_nothing(runner, isolated_home, fake_tools):
    assert _init(runner).exit_code == 0
    outcome = _invoke(runner, "render", "--diff")
    assert outcome.exit_code == 0, outcome.output
    assert '+prefix = "tst"' in outcome.output
    assert not (
        paths.stage_dir(isolated_home / "envs" / "tst", paths.BOOTSTRAP)
        / "terraform.tfvars"
    ).exists()
    assert _invoke(runner, "render").exit_code == 0
    assert "No changes." in _invoke(runner, "render", "--diff").output


def test_render_without_answers_exits_2(runner):
    outcome = _invoke(runner, "render", "--prefix", "nope")
    assert outcome.exit_code == 2
    assert "stellar init --prefix nope" in outcome.output


def test_render_invalid_answers_exit_2(runner, isolated_home):
    assert _init(runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text(path.read_text().replace("IL5", "PCI"))
    outcome = _invoke(runner, "render")
    assert outcome.exit_code == 2
    assert "compliance.regime PCI" in outcome.output


def test_preflight_reads_answers(runner, fake_cloud, isolated_home):
    outcome = _init(
        runner,
        sets=(
            "billing.no_iam=true",
            "resman.tenants.ten1={descriptive_name: tenant-1}",
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
            f'imports.0-bootstrap."{conftest.LOG_EXPORT_ADDRESS}"=tst-prod-audit-logs-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    preflight = _invoke(runner, "preflight", "--json")
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


def test_preflight_flags_override_answers(runner, fake_cloud):
    assert _init(runner).exit_code == 0
    outcome = _invoke(runner, "preflight", "--json", "--region", "us-west1")
    document = json.loads(outcome.stdout)
    assert document["inputs"]["region"] == "us-west1"
    assert document["inputs"]["regime"] == "IL5"


def test_preflight_rejects_broken_answers(runner, fake_cloud, isolated_home):
    assert _init(runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text("prefix: [unclosed\n")
    outcome = _invoke(runner, "preflight", "--json")
    assert outcome.exit_code == 2


def test_saved_answers_are_valid_yaml(runner, isolated_home):
    assert _init(runner).exit_code == 0
    text = (isolated_home / "envs" / "tst" / "answers.yaml").read_text()
    assert text.startswith(answers_lib.SCHEMA_COMMENT + "\n")
    assert yaml.YAML(typ="safe").load(text)["prefix"] == "tst"


@pytest.mark.terraform
def test_rendered_bootstrap_workspace_validates(runner, isolated_home):
    outcome = _init(
        runner,
        sets=(
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    assert _invoke(runner, "render", "--stage", "0").exit_code == 0
    workspace = _workspace(isolated_home, "0-bootstrap")
    # The phase file sets bootstrap_user, so no command passes -var.
    assert (workspace / "0-bootstrap-phase.auto.tfvars").is_file()
    env = {**os.environ, "TF_IN_AUTOMATION": "1"}
    for command in (
        ["init", "-backend=false", "-input=false"],
        ["validate"],
    ):
        completed = helpers.terraform(workspace, *command, env=env)
        assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    "args",
    [
        ["--set", "prefix=xyz"],
        ["--prefix", "abc", "--set", "prefix=xyz"],
    ],
)
def test_init_refuses_to_change_the_prefix(runner, isolated_home, args):
    outcome = _init(
        runner,
        "abc",
        sets=(
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=abc-prod-iac-core-0',
        ),
    )
    assert outcome.exit_code == 0, outcome.output
    changed = _invoke(runner, "init", "--non-interactive", *args)
    assert changed.exit_code == 2
    assert "stellar init --answers-from abc --prefix xyz" in changed.output
    assert not (isolated_home / "envs" / "xyz").exists()


def test_init_rejects_overrides_that_render_would_reject(runner, isolated_home):
    outcome = _init(
        runner,
        sets=(
            "overrides.0-bootstrap.prefix=other",
            "overrides.0-bootstrap.not_a_var=1",
            "overrides.1-resman.prefix=zzz",
        ),
    )
    assert outcome.exit_code == 2
    assert "overrides.0-bootstrap sets prefix, which stellar" in outcome.output
    assert "overrides.0-bootstrap sets not_a_var" in outcome.output
    assert "overrides.1-resman sets prefix" in outcome.output
    assert not (isolated_home / "envs" / "tst").exists()


def test_init_rejects_import_ids_of_another_prefix(runner, isolated_home):
    outcome = _init(
        runner,
        sets=(
            f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=old-prod-iac-core-0',
        ),
    )
    assert outcome.exit_code == 2
    assert "Stage 0 names that project tst-prod-iac-core-0" in outcome.output


def test_render_rejects_answers_of_another_prefix(
    runner, isolated_home, fake_tools
):
    assert _init(runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text(path.read_text().replace("prefix: tst", "prefix: qqq"))
    outcome = _invoke(runner, "render", "--stage", "0")
    assert outcome.exit_code == 2
    assert "sets prefix qqq, but it belongs to environment tst" in (
        outcome.output
    )
    assert not (_workspace(isolated_home, "0-bootstrap")).exists()
    listed = _invoke(runner, "env", "list")
    assert "answers set prefix qqq" in listed.output


def test_stale_current_environment(runner, isolated_home):
    assert _init(runner).exit_code == 0
    (isolated_home / "current").write_text("zzz\n")
    for args in (["env", "show"], ["render"]):
        outcome = _invoke(runner, *args)
        assert outcome.exit_code == 2
        assert "current environment zzz no longer exists" in outcome.output
        assert "stellar env use PREFIX" in outcome.output
    listed = _invoke(runner, "env", "list")
    assert listed.exit_code == 0
    assert "zzz no longer exists" in listed.output
    # A plain init starts the stale prefix from scratch instead of
    # reporting a missing prefix.
    outcome = _invoke(runner, "init", "--non-interactive", *_sets())
    assert outcome.exit_code == 0, outcome.output
    assert "init now creates zzz from scratch" in outcome.output
    assert _answers(isolated_home, "zzz").prefix == "zzz"


def test_init_errors_name_their_source(runner, tmp_path):
    config = tmp_path / "config.env"
    config.write_text("PREFIX=abc\nORGANIZATION_ID=x\n", encoding="utf-8")
    outcome = _invoke(
        runner,
        "init",
        "--non-interactive",
        "--from-config-env",
        str(config),
    )
    assert outcome.exit_code == 2
    assert f"Invalid answers from --from-config-env {config}:" in (
        outcome.output
    )
    bare = _invoke(runner, "init", "--non-interactive", "--prefix", "abc")
    assert "Error: Invalid answers:" in bare.output


def test_init_accepts_a_home_that_holds_the_engine(runner, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    engine = _engine_copy(home)
    outcome = runner.invoke(
        cli.app,
        [
            "init",
            "--non-interactive",
            "--prefix",
            "tst",
            *_sets(),
            "--home",
            str(home),
            "--repo",
            str(engine),
        ],
    )
    assert outcome.exit_code == 0, outcome.output
    answers = answers_lib.load(home / "envs" / "tst" / "answers.yaml")
    assert answers.engine is not None
    assert answers.engine.path == str(engine)


_SCANNED = [
    "storage.uniformBucketLevelAccess",
    "custom.kmsRotation",
    "unmanaged.constraint",
    "iam.allowedPolicyMemberDomains",
]


def test_imports_scan_without_environment_exits_2(runner, fake_cloud):
    outcome = _invoke(runner, "imports", "scan")
    assert outcome.exit_code == 2
    assert "stellar init" in outcome.output


def test_imports_scan_saves_declared_policies(
    runner, fake_cloud, isolated_home, fake_tools
):
    assert _init(runner).exit_code == 0
    path = isolated_home / "envs" / "tst" / "answers.yaml"
    path.write_text("# my note\n" + path.read_text())
    fake_cloud.org_policies = _SCANNED
    outcome = _invoke(runner, "imports", "scan")
    assert outcome.exit_code == 0, outcome.output
    assert ("org_policies", conftest.ORG_ID) in fake_cloud.calls
    for name in _SCANNED:
        assert name in outcome.output
    assert "Saved 2 organization policies" in outcome.output
    assert "Next: stellar render" in outcome.output
    assert _answers(isolated_home).existing_org_policies == [
        "iam.allowedPolicyMemberDomains",
        "storage.uniformBucketLevelAccess",
    ]
    assert "# my note" in path.read_text()
    assert conftest.mode(path) == 0o600

    rerun = _invoke(runner, "imports", "scan")
    assert rerun.exit_code == 0, rerun.output
    assert "already lists these policies" in rerun.output

    render = _invoke(runner, "render", "--stage", "0")
    assert render.exit_code == 0, render.output
    text = _workspace(isolated_home, "0-bootstrap") / "0-bootstrap-imports.tf"
    assert '"storage.uniformBucketLevelAccess",' in text.read_text()


def test_imports_scan_clears_policies_that_are_gone(
    runner, fake_cloud, isolated_home
):
    assert (
        _init(
            runner, sets=("existing_org_policies=[unmanaged.constraint]",)
        ).exit_code
        == 2
    )
    assert (
        _init(
            runner,
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
    assert _invoke(runner, "render").exit_code == 2
    outcome = _invoke(runner, "imports", "scan")
    assert outcome.exit_code == 0, outcome.output
    assert "has no organization policies" in outcome.output
    assert _answers(isolated_home).existing_org_policies == []


def test_imports_scan_refuses_import_defaults(
    runner, fake_cloud, isolated_home
):
    assert (
        _init(
            runner,
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
    outcome = _invoke(runner, "imports", "scan")
    assert outcome.exit_code == 2
    assert "import_defaults" in outcome.output
    assert path.read_text() == before


def test_imports_scan_follows_the_regime(runner, fake_cloud, isolated_home):
    assert (
        _init(runner, sets=("compliance.regime=FEDRAMP_MODERATE",)).exit_code
        == 0
    )
    gated = "compute.managed.restrictProtocolForwardingCreationForTypes"
    fake_cloud.org_policies = [gated, "custom.myOrgRule"]
    outcome = _invoke(runner, "imports", "scan")
    assert outcome.exit_code == 0, outcome.output
    # The table wraps its cells, so check single words.
    assert "regime" in outcome.output
    assert "creates" not in outcome.output
    assert _answers(isolated_home).existing_org_policies == []


def test_imports_scan_reports_cloud_errors(runner, fake_cloud, isolated_home):
    assert _init(runner).exit_code == 0
    fake_cloud.org_policies = cli.api.AccessDeniedError("no orgpolicy access")
    outcome = _invoke(runner, "imports", "scan")
    assert outcome.exit_code == 1
    assert "no orgpolicy access" in outcome.output


def test_env_show_lists_existing_org_policies(runner, isolated_home):
    assert (
        _init(
            runner,
            sets=("existing_org_policies=[iam.allowedPolicyMemberDomains]",),
        ).exit_code
        == 0
    )
    outcome = _invoke(runner, "env", "show")
    assert outcome.exit_code == 0, outcome.output
    assert "Existing organization policies" in outcome.output
    assert "  iam.allowedPolicyMemberDomains" in outcome.output


_AUTOMATION_IMPORT = (
    f'imports.0-bootstrap."{conftest.AUTOMATION_ADDRESS}"=tst-prod-iac-core-0'
)


def _engine_invoke(runner, engine, *args):
    return runner.invoke(cli.app, [*args, "--repo", str(engine)])


def _init_engine(runner, engine):
    return _engine_invoke(
        runner,
        engine,
        "init",
        "--non-interactive",
        "--prefix",
        "tst",
        *_sets(_AUTOMATION_IMPORT),
    )


def test_render_warns_when_the_engine_cannot_keep_projects(
    runner, isolated_home, fake_tools, tmp_path
):
    engine = helpers.deletion_policy_engine(tmp_path / "engine", declared=False)
    assert _init_engine(runner, engine).exit_code == 0
    outcome = _engine_invoke(runner, engine, "render", "--stage", "0")
    assert outcome.exit_code == 0, outcome.output
    assert (
        "Warning: keep_imported_projects is true, but this engine version "
        "of 0-bootstrap cannot keep imported projects on destroy yet, so "
        "terraform destroy deletes tst-prod-iac-core-0."
    ) in outcome.output
    show = _engine_invoke(runner, engine, "env", "show")
    assert "    tst-prod-iac-core-0  DELETE" in show.output


def test_render_and_show_keep_imported_projects(
    runner, isolated_home, fake_tools, tmp_path
):
    engine = helpers.deletion_policy_engine(tmp_path / "engine")
    outcome = _init_engine(runner, engine)
    assert outcome.exit_code == 0, outcome.output
    rendered = _engine_invoke(runner, engine, "render", "--stage", "0")
    assert rendered.exit_code == 0, rendered.output
    assert "keep_imported_projects" not in rendered.output
    tfvars = _workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    assert 'automation = "ABANDON"' in tfvars.read_text()
    show = _engine_invoke(runner, engine, "env", "show")
    assert show.exit_code == 0, show.output
    assert "    tst-prod-iac-core-0  ABANDON" in show.output
    assert "    tst-prod-audit-logs-0  DELETE" in show.output


def _phase_file(home):
    return _workspace(home, "0-bootstrap") / "0-bootstrap-phase.auto.tfvars"


def test_render_final_phase_removes_the_phase_file(
    runner, isolated_home, fake_tools
):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    phase_file = _phase_file(isolated_home)
    assert phase_file.is_file()
    switch = _invoke(
        runner, "init", "--non-interactive", "--set", "stage0_phase=final"
    )
    assert switch.exit_code == 0, switch.output
    outcome = _invoke(runner, "render")
    assert outcome.exit_code == 0, outcome.output
    assert f"removed    {phase_file}" in outcome.output
    assert not phase_file.exists()
    workspace = _workspace(isolated_home, "0-bootstrap")
    assert f"terraform -chdir={workspace} plan -out=s0.tfplan" in (
        outcome.output
    )
    assert f"terraform -chdir={workspace} apply s0.tfplan" in outcome.output
    assert "stage0_phase" not in outcome.output
    again = _invoke(runner, "render")
    assert str(phase_file) not in again.output
    show = _invoke(runner, "env", "show")
    assert "Stage 0 phase: final" in show.output


def test_render_updates_the_phase_file_for_a_new_user(
    runner, isolated_home, fake_tools
):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    change = _invoke(
        runner,
        "init",
        "--non-interactive",
        "--set",
        "bootstrap_user=ops@example.com",
    )
    assert change.exit_code == 0, change.output
    outcome = _invoke(runner, "render", "--stage", "0")
    phase_file = _phase_file(isolated_home)
    assert f"updated    {phase_file}" in outcome.output
    assert "ops@example.com" in phase_file.read_text()


def test_render_refuses_a_phase_file_it_did_not_write(
    runner, isolated_home, fake_tools
):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    phase_file = _phase_file(isolated_home)
    phase_file.write_text('bootstrap_user = "someone@example.com"\n')
    for args in (["render"], ["render", "--diff"]):
        outcome = _invoke(runner, *args)
        assert outcome.exit_code == 2, outcome.output
        assert f"stellar did not write {phase_file}" in outcome.output
    assert phase_file.read_text() == 'bootstrap_user = "someone@example.com"\n'


def test_render_refuses_a_foreign_phase_file_before_any_write(
    runner, isolated_home, fake_tools
):
    assert _init(runner).exit_code == 0
    assert _invoke(runner, "render").exit_code == 0
    tfvars = _workspace(isolated_home, "0-bootstrap") / "terraform.tfvars"
    before = tfvars.read_text()
    change = _invoke(
        runner,
        "init",
        "--non-interactive",
        "--set",
        "alert_email=changed@example.com",
    )
    assert change.exit_code == 0, change.output
    _phase_file(isolated_home).write_text('bootstrap_user = "x@example.com"\n')
    outcome = _invoke(runner, "render")
    assert outcome.exit_code == 2, outcome.output
    assert tfvars.read_text() == before


def test_render_diff_shows_the_phase_file(runner, isolated_home, fake_tools):
    assert _init(runner).exit_code == 0
    outcome = _invoke(runner, "render", "--diff")
    assert outcome.exit_code == 0, outcome.output
    assert '+bootstrap_user = "admin@example.com"' in outcome.output
    assert not _phase_file(isolated_home).exists()
    assert _invoke(runner, "render").exit_code == 0
    switch = _invoke(
        runner, "init", "--non-interactive", "--set", "stage0_phase=final"
    )
    assert switch.exit_code == 0, switch.output
    removal = _invoke(runner, "render", "--diff")
    assert '-bootstrap_user = "admin@example.com"' in removal.output
    assert _phase_file(isolated_home).is_file()


def test_init_requires_bootstrap_user_in_the_bootstrap_phase(
    runner, isolated_home
):
    outcome = runner.invoke(
        cli.app,
        [
            "init",
            "--non-interactive",
            "--repo",
            str(conftest.REPO_ROOT),
            "--prefix",
            "tst",
            *[
                arg
                for assignment in REQUIRED_SETS
                if not assignment.startswith("bootstrap_user=")
                for arg in ("--set", assignment)
            ],
        ],
    )
    assert outcome.exit_code == 2, outcome.output
    assert "bootstrap_user is required while stage0_phase is bootstrap" in (
        outcome.output
    )
