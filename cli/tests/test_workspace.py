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

import os
import pathlib
import shutil
import subprocess

import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine import workspace

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


def test_sync_real_engine_layout(env):
    report = workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    assert "main.tf" in report.linked
    assert "templates" in report.linked
    assert not any(workspace.is_excluded(name) for name in report.linked)
    assert report.conflicts == []


@pytest.mark.terraform
def test_bootstrap_workspace_validates(env):
    workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    ws = env.workspace("0-bootstrap")
    init = helpers.terraform(ws, "init", "-backend=false", "-input=false")
    assert init.returncode == 0, init.stderr
    validate = helpers.terraform(ws, "validate")
    assert validate.returncode == 0, validate.stderr
