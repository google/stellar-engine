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

"""Tests for the home layout and environment paths."""

import os
import pathlib
import shutil
import subprocess

import pytest

import conftest
from stellar_engine import paths


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("0-bootstrap", "0-bootstrap"),
        ("1-resman", "1-resman"),
        ("0", "0-bootstrap"),
        ("1", "1-resman"),
    ],
)
def test_resolve_stage(name, expected):
    assert paths.resolve_stage(name) == expected


@pytest.mark.parametrize("name", ["2-networking", "2", "", "bootstrap"])
def test_resolve_stage_unknown(name):
    with pytest.raises(ValueError, match="Unknown stage"):
        paths.resolve_stage(name)


def test_resolve_home_flag_wins(tmp_path):
    flag = tmp_path / "flag-home"
    environ = {paths.HOME_ENV_VAR: str(tmp_path / "env-home")}
    resolved = paths.resolve_home(flag, environ, tmp_path / "engine")
    assert resolved == paths.ResolvedHome(flag, paths.HomeSource.FLAG)


def test_resolve_home_env_var(tmp_path):
    environ = {paths.HOME_ENV_VAR: str(tmp_path / "env-home")}
    resolved = paths.resolve_home(None, environ, tmp_path / "engine")
    assert resolved.path == tmp_path / "env-home"
    assert resolved.source is paths.HomeSource.ENV


@pytest.mark.parametrize("environ", [{}, {paths.HOME_ENV_VAR: "  "}])
def test_resolve_home_default(tmp_path, environ):
    resolved = paths.resolve_home(None, environ, tmp_path / "engine")
    assert resolved.path == tmp_path / "engine" / paths.HOME_DIRNAME
    assert resolved.source is paths.HomeSource.DEFAULT


def test_resolve_home_expands_user_and_relative(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "user"))
    environ = {paths.HOME_ENV_VAR: "~/deployments/lab"}
    resolved = paths.resolve_home(None, environ, tmp_path)
    assert resolved.path == (tmp_path / "user/deployments/lab").resolve()
    monkeypatch.chdir(tmp_path)
    relative = paths.resolve_home(pathlib.Path("rel"), {}, tmp_path)
    assert relative.path == (tmp_path / "rel").resolve()
    assert relative.path.is_absolute()


def test_home_ensure_creates_private_home_and_gitignore(tmp_path):
    home = paths.Home(tmp_path / "a" / "home")
    home.ensure()
    assert conftest.mode(tmp_path / "a") == 0o700
    assert conftest.mode(home.root) == 0o700
    assert conftest.mode(home.envs_dir) == 0o700
    assert home.gitignore_path.read_text() == paths.GITIGNORE


def test_home_ensure_keeps_existing_gitignore(tmp_path):
    home = paths.Home(tmp_path)
    home.gitignore_path.write_text("custom\n")
    home.ensure()
    assert home.gitignore_path.read_text() == "custom\n"


@pytest.mark.skipif(shutil.which("git") is None, reason="git is missing")
def test_gitignore_tracks_answers_only(tmp_path):
    home = paths.Home(tmp_path)
    home.ensure()
    env = home.env("abc")
    env.ensure()
    env.answers.write_text("prefix: abc\n")
    (env.root / "run-state.json").write_text("{}")
    (env.logs / "run.log").write_text("log")
    (env.workspace("0") / "terraform.tfvars").parent.mkdir(parents=True)
    (env.workspace("0") / "terraform.tfvars").write_text("x = 1")
    home.current_file.write_text("abc\n")
    home.schema_path.write_text("{}")
    _git(tmp_path, "init", "-q")
    listed = subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "ls-files",
            "--others",
            "--exclude-standard",
        ],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.split()
    assert sorted(listed) == [".gitignore", "envs/abc/answers.yaml"]


def test_current_and_set_current(tmp_path):
    home = paths.Home(tmp_path / "home")
    assert home.current() is None
    home.set_current("abc")
    assert home.current_file.read_text() == "abc\n"
    assert home.current() == "abc"
    home.current_file.write_text("\n")
    assert home.current() is None


@pytest.mark.parametrize("prefix", ["", "../x", "Abc", "1ab", "a/b", "ab-"])
def test_invalid_env_names(tmp_path, prefix):
    home = paths.Home(tmp_path)
    with pytest.raises(ValueError, match="Invalid prefix"):
        home.env(prefix)
    with pytest.raises(ValueError, match="Invalid prefix"):
        home.set_current(prefix)


def test_hyphenated_env_name(tmp_path):
    home = paths.Home(tmp_path)
    assert home.env("ab-c").root == home.envs_dir / "ab-c"


def test_list_envs_requires_answers(tmp_path):
    home = paths.Home(tmp_path)
    assert home.list_envs() == []
    for prefix in ("zed", "abc", "noans"):
        home.env(prefix).ensure()
    home.env("zed").answers.write_text("{}")
    home.env("abc").answers.write_text("{}")
    (home.envs_dir / "README").write_text("not an env")
    assert home.list_envs() == ["abc", "zed"]


def test_resolve_prefix(tmp_path):
    home = paths.Home(tmp_path)
    with pytest.raises(paths.NoEnvironmentError, match="stellar init"):
        home.resolve_prefix(None)
    assert home.resolve_prefix("abc") == "abc"
    home.set_current("cur")
    assert home.stale_current_message() is not None
    with pytest.raises(paths.NoEnvironmentError, match="no longer exists"):
        home.resolve_prefix(None)
    home.env("cur").ensure()
    home.env("cur").answers.write_text("prefix: cur\n")
    assert home.stale_current_message() is None
    assert home.resolve_prefix(None) == "cur"
    assert home.resolve_prefix("abc") == "abc"


def test_env_paths_layout(tmp_path):
    env = paths.Home(tmp_path).env("abc")
    root = tmp_path / "envs" / "abc"
    assert env.root == root
    assert env.prefix == "abc"
    assert env.answers == root / "answers.yaml"
    assert env.run_state == root / "run-state.json"
    assert env.logs == root / "logs"
    assert env.plans == root / "plans"
    assert env.iam_snapshots == root / "iam-snapshots"
    assert env.generated == root / "generated"
    assert env.fast_config == root / "fast-config"
    assert env.modules_link == root / "modules"
    assert env.stages_dir == root / "fast" / "stages-aw"
    assert env.workspace("0") == root / "fast/stages-aw/0-bootstrap"
    assert env.workspace("1-resman") == root / "fast/stages-aw/1-resman"
    assert env.generated_hash("1") == root / "generated/1-resman.sha256"
    with pytest.raises(ValueError):
        env.workspace("3-security")


def test_env_ensure_private_dirs(tmp_path):
    env = paths.Home(tmp_path / "home").env("abc")
    env.ensure()
    for directory in (
        env.root,
        env.logs,
        env.plans,
        env.iam_snapshots,
        env.generated,
        env.fast_config,
        env.stages_dir,
        env.stages_dir.parent,
    ):
        assert directory.is_dir()
        assert conftest.mode(directory) == 0o700
    env.ensure()


def test_modules_link_matches_stage_relative_path(tmp_path):
    # Stage code reaches modules as ../../../modules from its directory.
    env = paths.Home(tmp_path).env("abc")
    for stage in paths.STAGES:
        resolved = env.workspace(stage) / ".." / ".." / ".." / "modules"
        assert pathlib.Path(resolved).resolve() == env.modules_link.resolve()


def test_two_homes_are_independent(tmp_path):
    engine = tmp_path / "engine"
    first = paths.Home(paths.resolve_home(tmp_path / "one", {}, engine).path)
    second = paths.Home(
        paths.resolve_home(
            None, {paths.HOME_ENV_VAR: str(tmp_path / "two")}, engine
        ).path
    )
    first.set_current("abc")
    second.set_current("xyz")
    assert first.current() == "abc"
    assert second.current() == "xyz"
    assert first.env("abc").root != second.env("abc").root


def _git(root, *args):
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        },
    )
