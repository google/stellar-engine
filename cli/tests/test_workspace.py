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

"""Tests for the stage workspace symlink farms."""

import datetime
import os
import pathlib
import shutil
import subprocess

import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine import workspace
from stellar_engine.render import writer

_NOW = datetime.datetime(2026, 10, 30, 9, 0, tzinfo=datetime.UTC)
_MANIFEST = str(workspace.MODULE_MANIFEST)

_ENGINE_FILES = {
    "0-bootstrap": [
        "main.tf",
        "variables.tf",
        "setIAM.sh",
        "setIAM.yaml.sample",
        "providers.tf.tmp",
        "terraform.tfvars.sample",
        "README.md",
        "diagram.png",
        "diagram.svg",
        "groups.gif",
        "data/custom-roles/role.yaml",
        "templates/providers.tf.tpl",
    ],
    "1-resman": [
        "main.tf",
        "variables.tf",
        "terraform.tfvars.sample",
        "IAM.md",
        "templates/providers.tf.tpl",
    ],
}


@pytest.fixture
def engine(tmp_path):
    """Returns a minimal fake engine checkout."""
    root = tmp_path / "engine"
    (root / "modules" / "project").mkdir(parents=True)
    for stage, files in _ENGINE_FILES.items():
        for name in files:
            path = paths.stage_dir(root, stage) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {name}\n")
    return root


@pytest.fixture
def env(tmp_path):
    """Returns the paths of an environment in a home outside the engine."""
    return paths.Home(tmp_path / "home").env("abc")


def _links(directory):
    return {
        path.name: pathlib.Path(os.readlink(path))
        for path in directory.iterdir()
        if path.is_symlink()
    }


def test_sync_bootstrap_layout(engine, env):
    report = workspace.sync(env, engine, "0")
    ws = env.workspace("0-bootstrap")
    stage_dir = paths.stage_dir(engine, paths.BOOTSTRAP)
    assert report.stage == "0-bootstrap"
    assert report.path == ws
    assert report.linked == [
        "data",
        "main.tf",
        "setIAM.sh",
        "setIAM.yaml.sample",
        "templates",
        "variables.tf",
    ]
    assert _links(ws) == {name: stage_dir / name for name in report.linked}
    assert all(target.is_absolute() for target in _links(ws).values())
    assert report.created == [workspace.BOOTSTRAP_PROVIDERS]
    providers = ws / workspace.BOOTSTRAP_PROVIDERS
    assert not providers.is_symlink()
    assert providers.read_text() == "# providers.tf.tmp\n"
    assert report.removed == report.conflicts == report.pending == []
    assert os.readlink(env.modules_link) == str(engine / "modules")
    assert (ws / "../../../modules/project").resolve().is_dir()


def test_sync_is_idempotent(engine, env):
    workspace.sync(env, engine, "0-bootstrap")
    again = workspace.sync(env, engine, "0-bootstrap")
    assert again.linked == again.removed == again.created == []


def test_sync_leaves_env_files_alone(engine, env):
    workspace.sync(env, engine, "0-bootstrap")
    ws = env.workspace("0-bootstrap")
    owned = {
        "terraform.tfvars": 'prefix = "abc"\n',
        "terraform.tfvars.backup.20261023T000000Z": "old\n",
        "0-bootstrap-imports.tf": "import {}\n",
        "0-bootstrap-phase.auto.tfvars": 'bootstrap_user = "a@example.com"\n',
        "0-bootstrap-providers.tf": "# remote providers\n",
        "terraform.tfstate": "{}",
        ".terraform.lock.hcl": "# lock\n",
    }
    for name, content in owned.items():
        (ws / name).write_text(content)
    (ws / ".terraform").mkdir()
    report = workspace.sync(env, engine, "0-bootstrap")
    for name, content in owned.items():
        assert not (ws / name).is_symlink()
        assert (ws / name).read_text() == content
    assert (ws / ".terraform").is_dir()
    assert report.linked == report.removed == report.created == []
    assert report.conflicts == []


def test_sync_reports_conflicts_without_overwriting(engine, env):
    ws = env.workspace("0-bootstrap")
    ws.mkdir(parents=True)
    (ws / "main.tf").write_text("# local copy\n")
    report = workspace.sync(env, engine, "0-bootstrap")
    assert report.conflicts == ["main.tf"]
    assert not (ws / "main.tf").is_symlink()
    assert (ws / "main.tf").read_text() == "# local copy\n"
    assert "main.tf" not in report.linked


def test_sync_removes_stale_engine_links(engine, env):
    workspace.sync(env, engine, "0-bootstrap")
    ws = env.workspace("0-bootstrap")
    stage_dir = paths.stage_dir(engine, paths.BOOTSTRAP)
    (stage_dir / "setIAM.sh").unlink()
    # A link that now matches an excluded pattern is stale as well.
    (ws / "README.md").symlink_to(stage_dir / "README.md")
    foreign = engine / "elsewhere.tf"
    foreign.write_text("")
    (ws / "operator.tf").symlink_to(foreign)
    report = workspace.sync(env, engine, "0-bootstrap")
    assert report.removed == ["README.md", "setIAM.sh"]
    assert not (ws / "setIAM.sh").is_symlink()
    assert (ws / "operator.tf").is_symlink()


def test_sync_repoints_links_to_a_moved_engine(engine, env, tmp_path):
    workspace.sync(env, engine, "0-bootstrap")
    moved = tmp_path / "moved-engine"
    shutil.copytree(engine, moved)
    report = workspace.sync(env, moved, "0-bootstrap")
    ws = env.workspace("0-bootstrap")
    assert "main.tf" in report.linked
    assert os.readlink(ws / "main.tf") == str(
        paths.stage_dir(moved, paths.BOOTSTRAP) / "main.tf"
    )
    assert os.readlink(env.modules_link) == str(moved / "modules")


def test_sync_removes_links_into_a_previous_engine(engine, env, tmp_path):
    workspace.sync(env, engine, "0-bootstrap")
    other = tmp_path / "other-engine"
    shutil.copytree(engine, other)
    (paths.stage_dir(other, paths.BOOTSTRAP) / "setIAM.sh").unlink()
    ws = env.workspace("0-bootstrap")
    # A hand-made link elsewhere in the first engine is not an engine link.
    (ws / "operator.tf").symlink_to(engine / "modules")
    report = workspace.sync(env, other, "0-bootstrap")
    assert report.removed == ["setIAM.sh"]
    assert not (ws / "setIAM.sh").is_symlink()
    assert (ws / "operator.tf").is_symlink()
    other_stage = paths.stage_dir(other, paths.BOOTSTRAP)
    engine_links = {
        name: target
        for name, target in _links(ws).items()
        if name != "operator.tf"
    }
    assert engine_links == {name: other_stage / name for name in engine_links}


def test_sync_keeps_output_links_named_like_old_engine_files(engine, env):
    workspace.sync(env, engine, "1-resman")
    ws = env.workspace("1-resman")
    source = paths.stage_dir(env.fast_config, paths.RESMAN) / "x.tf"
    source.parent.mkdir(parents=True)
    source.write_text("")
    (ws / "x.tf").symlink_to(source)
    report = workspace.sync(env, engine, "1-resman")
    assert "x.tf" not in report.removed
    assert (ws / "x.tf").is_symlink()


def test_sync_refuses_real_modules_dir(engine, env):
    env.modules_link.mkdir(parents=True)
    with pytest.raises(workspace.WorkspaceError, match="real file"):
        workspace.sync(env, engine, "0-bootstrap")


def test_sync_unknown_stage(engine, env):
    with pytest.raises(ValueError):
        workspace.sync(env, engine, "2-networking")


def test_sync_missing_engine_stage(tmp_path, env):
    with pytest.raises(workspace.WorkspaceError, match="no stage"):
        workspace.sync(env, tmp_path / "empty", "1-resman")


def test_sync_resman_pending_then_linked(engine, env):
    report = workspace.sync(env, engine, "1")
    ws = env.workspace("1-resman")
    assert report.pending == list(workspace.OUTPUT_LINKS["1-resman"])
    assert report.created == []
    assert sorted(_links(ws)) == ["main.tf", "templates", "variables.tf"]

    for relative in workspace.OUTPUT_LINKS["1-resman"]:
        path = env.fast_config / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    report = workspace.sync(env, engine, "1")
    assert report.pending == []
    assert report.linked == [
        "1-resman-providers.tf",
        "0-globals.auto.tfvars.json",
        "0-bootstrap.auto.tfvars.json",
    ]
    assert os.readlink(ws / "1-resman-providers.tf") == str(
        env.fast_config / "providers/1-resman-providers.tf"
    )
    assert workspace.sync(env, engine, "1").linked == []


def test_sync_resman_drops_dangling_output_links(engine, env):
    source = env.fast_config / "tfvars/0-bootstrap.auto.tfvars.json"
    source.parent.mkdir(parents=True)
    source.write_text("{}")
    workspace.sync(env, engine, "1-resman")
    source.unlink()
    report = workspace.sync(env, engine, "1-resman")
    assert report.removed == ["0-bootstrap.auto.tfvars.json"]
    assert "tfvars/0-bootstrap.auto.tfvars.json" in report.pending


def test_sync_resman_keeps_hand_placed_outputs(engine, env):
    ws = env.workspace("1-resman")
    ws.mkdir(parents=True)
    (ws / "1-resman-providers.tf").write_text("# copied by hand\n")
    report = workspace.sync(env, engine, "1-resman")
    assert (ws / "1-resman-providers.tf").read_text() == "# copied by hand\n"
    assert "1-resman-providers.tf" not in report.linked


def _write_outputs(env):
    for relative in workspace.OUTPUT_LINKS["1-resman"]:
        path = env.fast_config / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")


def test_stale_links_lists_what_sync_changes(engine, env):
    assert workspace.stale_links(env, engine, "1") == [
        workspace.MODULES,
        "main.tf",
        "templates",
        "variables.tf",
        *workspace.OUTPUT_LINKS["1-resman"],
    ]
    _write_outputs(env)
    workspace.sync(env, engine, "1")
    assert workspace.stale_links(env, engine, "1") == []
    ws = env.workspace("1-resman")
    (ws / "main.tf").unlink()
    (ws / "old.tf").symlink_to(paths.stage_dir(engine, "1-resman") / "old.tf")
    assert workspace.stale_links(env, engine, "1-resman") == [
        "main.tf",
        "old.tf",
    ]
    workspace.sync(env, engine, "1-resman")
    assert workspace.stale_links(env, engine, "1-resman") == []


def test_stale_links_follow_a_moved_engine(engine, env, tmp_path):
    workspace.sync(env, engine, "0")
    moved = tmp_path / "moved"
    shutil.copytree(engine, moved)
    assert workspace.stale_links(env, moved, "0") == [
        workspace.MODULES,
        "data",
        "main.tf",
        "setIAM.sh",
        "setIAM.yaml.sample",
        "templates",
        "variables.tf",
    ]


def test_stale_links_skip_real_files(engine, env):
    _write_outputs(env)
    workspace.sync(env, engine, "1")
    ws = env.workspace("1-resman")
    for name in ("variables.tf", "1-resman-providers.tf"):
        (ws / name).unlink()
        (ws / name).write_text("# placed by hand\n")
    assert workspace.stale_links(env, engine, "1") == []


def test_stale_links_change_nothing(engine, env):
    found = workspace.stale_links(env, engine, "0")
    assert workspace.BOOTSTRAP_PROVIDERS in found
    assert not env.workspace("0-bootstrap").exists()
    assert not env.modules_link.is_symlink()


def test_stale_links_list_the_bootstrap_providers_copy(engine, env):
    workspace.sync(env, engine, "0")
    assert workspace.stale_links(env, engine, "0") == []
    (env.workspace("0-bootstrap") / workspace.BOOTSTRAP_PROVIDERS).unlink()
    assert workspace.stale_links(env, engine, "0") == [
        workspace.BOOTSTRAP_PROVIDERS
    ]


def test_sync_moves_the_module_manifest_of_another_engine(engine, env):
    # The previous engine is a worktree nested inside this checkout, so
    # its module directories lie under this engine's root too.
    nested = engine / ".claude" / "worktrees" / "a"
    shutil.copytree(engine, nested, ignore=shutil.ignore_patterns(".claude"))
    workspace.sync(env, nested, "0")
    ws = env.workspace("0-bootstrap")
    manifest = helpers.module_manifest(ws, (nested / "modules").resolve())
    recorded = manifest.read_bytes()
    assert workspace.stale_modules(ws) == []
    # While the links are stale, the list names them, and sync moves the
    # manifest once it relinked.
    assert workspace.MODULES in workspace.stale_links(env, engine, "0")
    report = workspace.sync(env, engine, "0", now=_NOW)
    assert report.reset == [_MANIFEST]
    stamp = writer.stamp(_NOW)
    assert report.backups == [env.plans / f"modules.json.0-bootstrap.{stamp}"]
    assert report.backups[0].read_bytes() == recorded
    assert conftest.mode(report.backups[0]) == 0o600
    assert not manifest.exists()
    assert (ws / ".terraform" / "modules").is_dir()
    assert workspace.stale_links(env, engine, "0") == []


def test_stale_links_list_a_module_manifest_the_links_moved(
    engine, env, tmp_path
):
    # A relink that kept the manifest, such as one by an earlier stellar.
    workspace.sync(env, engine, "0")
    ws = env.workspace("0-bootstrap")
    manifest = helpers.module_manifest(ws, tmp_path / "old" / "modules")
    assert workspace.stale_modules(ws) == ["automation-project"]
    assert workspace.stale_links(env, engine, "0") == [_MANIFEST]
    assert manifest.exists()
    report = workspace.sync(env, engine, "0", now=_NOW)
    assert report.reset == [_MANIFEST]
    assert not manifest.exists()
    assert workspace.stale_links(env, engine, "0") == []


def test_sync_keeps_a_module_manifest_that_matches(engine, env):
    workspace.sync(env, engine, "0")
    ws = env.workspace("0-bootstrap")
    manifest = helpers.module_manifest(ws, (engine / "modules").resolve())
    assert workspace.stale_links(env, engine, "0") == []
    assert workspace.sync(env, engine, "0").reset == []
    assert manifest.exists()
    # Terraform reports a manifest that it cannot parse on its own.
    manifest.write_text("not json")
    assert workspace.stale_modules(ws) == []


def test_stale_links_missing_engine_stage(tmp_path, env):
    with pytest.raises(workspace.WorkspaceError, match="no stage directory"):
        workspace.stale_links(env, tmp_path / "empty", "0")


def test_two_homes_share_one_engine(engine, tmp_path):
    first = paths.Home(tmp_path / "one").env("abc")
    second = paths.Home(tmp_path / "two").env("abc")
    workspace.sync(first, engine, "0-bootstrap")
    workspace.sync(second, engine, "0-bootstrap")
    for env in (first, second):
        ws = env.workspace("0-bootstrap")
        assert os.readlink(ws / "main.tf") == str(
            paths.stage_dir(engine, paths.BOOTSTRAP) / "main.tf"
        )
    (first.workspace("0") / "terraform.tfvars").write_text("one\n")
    assert not (second.workspace("0") / "terraform.tfvars").exists()


@pytest.mark.parametrize(
    ("name", "excluded"),
    [
        ("terraform.tfvars", True),
        ("terraform.tfvars.sample", True),
        ("terraform.tfvars.backup.20261023T000000Z", True),
        ("0-bootstrap-providers.tf", True),
        ("providers.tf.tmp", True),
        ("0-globals.auto.tfvars.json", True),
        ("terraform.tfstate.backup", True),
        (".terraform", True),
        ("main.tf", False),
        ("setIAM.yaml.sample", False),
        ("data", False),
    ],
)
def test_is_excluded(name, excluded):
    assert workspace.is_excluded(name) is excluded


def _stage_links_files(tmp_path, stage):
    """Returns the outputs files `fast/stage-links.sh` prints for a stage."""
    outputs = tmp_path / "fast-config"
    outputs.mkdir()
    cwd = tmp_path / stage
    cwd.mkdir()
    environ = {
        key: value
        for key, value in os.environ.items()
        if "IMPERSONATE" not in key
    }
    printed = subprocess.run(
        ["bash", str(conftest.REPO_ROOT / "fast/stage-links.sh"), str(outputs)],
        capture_output=True,
        check=True,
        cwd=cwd,
        env=environ,
        text=True,
    ).stdout
    prefix = f"ln -s {outputs}/"
    return [
        line.removeprefix(prefix).removesuffix(" ./")
        for line in printed.splitlines()
        if line.startswith(prefix)
    ]


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is missing")
def test_output_links_match_stage_links_script(tmp_path):
    files = _stage_links_files(tmp_path, "1-resman")
    assert files == list(workspace.OUTPUT_LINKS["1-resman"])


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is missing")
def test_bootstrap_links_only_the_remote_providers(tmp_path):
    # Stage 0 starts from providers.tf.tmp; the remote providers file the
    # script links replaces it only at state migration, so sync skips it.
    files = _stage_links_files(tmp_path, "0-bootstrap")
    assert files == ["providers/0-bootstrap-providers.tf"]
    assert workspace.OUTPUT_LINKS["0-bootstrap"] == ()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is missing")
def test_resman_outputs_match_stage_links_script(tmp_path):
    # Stages 2 and 3 link the Stage 1 outputs beside the Stage 0 tfvars.
    found = set()
    for stage in ("2-networking-a-fedramp", "3-security"):
        (tmp_path / stage).mkdir()
        found.update(_stage_links_files(tmp_path / stage, stage))
    stage0_outputs = {name for name in found if name.startswith("tfvars/0-")}
    assert sorted(found - stage0_outputs) == sorted(workspace.RESMAN_OUTPUTS)


def test_sync_real_engine_layout(env):
    report = workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    assert "main.tf" in report.linked
    assert "templates" in report.linked
    assert not any(workspace.is_excluded(name) for name in report.linked)
    assert report.conflicts == []


def _module_engine(root, value):
    """Returns an engine whose Stage 0 outputs a value from a local module."""
    stage = paths.stage_dir(root, paths.BOOTSTRAP)
    stage.mkdir(parents=True)
    (stage / "main.tf").write_text(
        'module "m" {\n  source = "../../../modules/m"\n}\n'
        'output "v" {\n  value = module.m.v\n}\n'
    )
    (stage / workspace.BOOTSTRAP_PROVIDERS_TEMPLATE).write_text("# local\n")
    module = root / "modules" / "m"
    module.mkdir(parents=True)
    (module / "main.tf").write_text(f'output "v" {{\n  value = "{value}"\n}}\n')
    return root


@pytest.mark.terraform
def test_a_relinked_workspace_plans_with_the_new_modules(env, tmp_path):
    # A plain init keeps the manifest record of an unchanged source, so
    # without the move the plan would still use the old engine's module.
    old = _module_engine(tmp_path / "old", "engine-A")
    new = _module_engine(tmp_path / "new", "engine-B")
    workspace.sync(env, old, "0")
    ws = env.workspace("0-bootstrap")
    for args in (("init", "-input=false"), ("apply", "-auto-approve")):
        completed = helpers.terraform(ws, *args)
        assert completed.returncode == 0, completed.stderr
    assert workspace.sync(env, new, "0", now=_NOW).reset == [_MANIFEST]
    completed = helpers.terraform(ws, "init", "-input=false")
    assert completed.returncode == 0, completed.stderr
    plan = helpers.terraform(ws, "plan", "-input=false")
    assert plan.returncode == 0, plan.stderr
    assert '"engine-A" -> "engine-B"' in plan.stdout


@pytest.mark.terraform
def test_bootstrap_workspace_validates(env):
    workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    ws = env.workspace("0-bootstrap")
    helpers.terraform_init(ws)
    validate = helpers.terraform(ws, "validate")
    assert validate.returncode == 0, validate.stderr
