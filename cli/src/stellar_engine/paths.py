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

"""Locates the stellar home, its environments and their stage workspaces.

Every answer, workspace, hash, log and Stage 0 output of a deployment lives
under one home folder, so pointing a deployment elsewhere takes one flag or
environment variable. The home may sit outside the engine checkout: the
workspaces link to the engine with absolute paths, so one checkout can serve
many homes.
"""

from collections.abc import Mapping
import dataclasses
import enum
import pathlib
import re

from stellar_engine import patterns

STAGES: tuple[str, ...] = ("0-bootstrap", "1-resman")
BOOTSTRAP, RESMAN = STAGES
STAGE_ALIASES: dict[str, str] = {stage.split("-")[0]: stage for stage in STAGES}
# Where the stages live, in the engine checkout and in each environment.
STAGES_DIR = pathlib.PurePosixPath("fast/stages-aw")

HOME_DIRNAME = ".stellar"
HOME_ENV_VAR = "STELLAR_HOME"

# Tracks answers only, so state, logs, plans and Stage 0 outputs never get
# committed when the operator turns the home into a private git repository.
GITIGNORE = """\
# stellar writes this file. Git tracks answers only, never state, logs or plans.
/*
!/.gitignore
!/envs/
/envs/*/*
!/envs/*/answers.yaml
"""

# An environment directory name is a prefix, and every command accepts the
# same prefixes. Length limits belong to the answers validation, which reads
# them from the repository.
PREFIX_RE = re.compile(patterns.PREFIX)
_PRIVATE_DIR_MODE = 0o700


class NoEnvironmentError(Exception):
    """Raised when no environment is selected and none is current."""


class HomeSource(enum.StrEnum):
    """Where the home location came from."""

    FLAG = "flag"
    ENV = "env"
    DEFAULT = "default"


@dataclasses.dataclass(frozen=True)
class ResolvedHome:
    """A resolved home location and the setting it came from.

    Attributes:
        path: Absolute path of the home folder.
        source: The setting that selected it.
    """

    path: pathlib.Path
    source: HomeSource


def resolve_stage(name: str) -> str:
    """Returns the canonical stage name for a stage name or alias.

    Args:
        name: A stage name such as `0-bootstrap` or an alias such as `0`.

    Returns:
        The stage name.

    Raises:
        ValueError: If the name is neither a stage nor an alias.
    """
    if name in STAGES:
        return name
    if name in STAGE_ALIASES:
        return STAGE_ALIASES[name]
    known = ", ".join([*STAGES, *STAGE_ALIASES])
    raise ValueError(f"Unknown stage {name!r}; expected one of {known}")


def stage_alias(name: str) -> str:
    """Returns the alias of a stage, the inverse of `resolve_stage`.

    Args:
        name: A stage name such as `1-resman` or an alias such as `1`.

    Returns:
        The alias, such as `1`.

    Raises:
        ValueError: If the name is neither a stage nor an alias.
    """
    stage = resolve_stage(name)
    return next(
        alias for alias, found in STAGE_ALIASES.items() if found == stage
    )


def stage_dir(root: pathlib.Path, stage: str) -> pathlib.Path:
    """Returns the directory of a stage under an engine or environment root.

    Args:
        root: Root of the engine checkout or of an environment.
        stage: A stage name or alias.

    Raises:
        ValueError: If the stage is unknown.
    """
    return pathlib.Path(root) / STAGES_DIR / resolve_stage(stage)


def resolve_home(
    flag: pathlib.Path | None,
    environ: Mapping[str, str],
    engine_root: pathlib.Path,
) -> ResolvedHome:
    """Resolves the home folder the same way for every command.

    The `--home` flag wins over the `STELLAR_HOME` environment variable,
    which wins over the default `<engine root>/.stellar`.

    Args:
        flag: Value of the `--home` flag, or None when not given.
        environ: Environment variables, usually `os.environ`.
        engine_root: Root of the engine checkout.

    Returns:
        The absolute home path, with `~` expanded, and its source.
    """
    from_env = environ.get(HOME_ENV_VAR, "").strip()
    if flag is not None:
        path, source = pathlib.Path(flag), HomeSource.FLAG
    elif from_env:
        path, source = pathlib.Path(from_env), HomeSource.ENV
    else:
        path = pathlib.Path(engine_root) / HOME_DIRNAME
        source = HomeSource.DEFAULT
    return ResolvedHome(path.expanduser().resolve(), source)


def make_private_dir(path: pathlib.Path) -> None:
    """Creates a directory and any missing parents with mode 0700.

    `pathlib.Path.mkdir` applies its mode to the leaf only, so this creates
    each missing level itself.

    Args:
        path: Directory to create. Existing directories keep their mode.
    """
    missing = []
    current = pathlib.Path(path)
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=_PRIVATE_DIR_MODE)
        # The umask may strip bits from the requested mode.
        directory.chmod(_PRIVATE_DIR_MODE)


@dataclasses.dataclass(frozen=True)
class EnvPaths:
    """Paths inside one environment of a home.

    Attributes:
        root: The environment directory, `<home>/envs/<prefix>`.
        prefix: The deployment prefix that names the environment.
    """

    root: pathlib.Path
    prefix: str

    @property
    def answers(self) -> pathlib.Path:
        """Returns the `answers.yaml` path."""
        return self.root / "answers.yaml"

    @property
    def run_state(self) -> pathlib.Path:
        """Returns the `run-state.json` path."""
        return self.root / "run-state.json"

    @property
    def deploy_lock(self) -> pathlib.Path:
        """Returns the lock file that `stellar deploy` holds while it runs."""
        return self.root / "deploy.lock"

    @property
    def logs(self) -> pathlib.Path:
        """Returns the log directory."""
        return self.root / "logs"

    @property
    def plans(self) -> pathlib.Path:
        """Returns the saved plan directory."""
        return self.root / "plans"

    @property
    def iam_snapshots(self) -> pathlib.Path:
        """Returns the organization IAM snapshot directory."""
        return self.root / "iam-snapshots"

    @property
    def generated(self) -> pathlib.Path:
        """Returns the directory of hashes of rendered tfvars files."""
        return self.root / "generated"

    @property
    def fast_config(self) -> pathlib.Path:
        """Returns the Stage 0 and Stage 1 `outputs_location` directory.

        Each environment has its own, because the sample default
        `~/fast-config` would collide across environments.
        """
        return self.root / "fast-config"

    @property
    def modules_link(self) -> pathlib.Path:
        """Returns the `modules` symlink of the environment.

        Stage code reaches it as `../../../modules` from a workspace.
        """
        return self.root / "modules"

    @property
    def stages_dir(self) -> pathlib.Path:
        """Returns the directory that holds the stage workspaces."""
        return self.root / STAGES_DIR

    def workspace(self, stage: str) -> pathlib.Path:
        """Returns the workspace directory of a stage.

        Args:
            stage: A stage name or alias.

        Raises:
            ValueError: If the stage is unknown.
        """
        return stage_dir(self.root, stage)

    def generated_hash(self, stage: str) -> pathlib.Path:
        """Returns the hash file of the last tfvars rendered for a stage.

        Args:
            stage: A stage name or alias.

        Raises:
            ValueError: If the stage is unknown.
        """
        return self.generated / f"{resolve_stage(stage)}.sha256"

    def ensure(self) -> None:
        """Creates the environment directories with mode 0700."""
        for directory in (
            self.root,
            self.logs,
            self.plans,
            self.iam_snapshots,
            self.generated,
            self.fast_config,
            self.stages_dir,
        ):
            make_private_dir(directory)


@dataclasses.dataclass(frozen=True)
class Home:
    """The stellar home folder that holds every environment.

    Attributes:
        root: Absolute path of the home folder.
    """

    root: pathlib.Path

    @property
    def envs_dir(self) -> pathlib.Path:
        """Returns the directory that holds one directory per prefix."""
        return self.root / "envs"

    @property
    def current_file(self) -> pathlib.Path:
        """Returns the file that names the active prefix."""
        return self.root / "current"

    @property
    def schema_path(self) -> pathlib.Path:
        """Returns the JSON schema path that `answers.yaml` files refer to."""
        return self.root / "answers.schema.json"

    @property
    def gitignore_path(self) -> pathlib.Path:
        """Returns the generated `.gitignore` path."""
        return self.root / ".gitignore"

    def ensure(self) -> None:
        """Creates the home with mode 0700 and its `.gitignore` if missing.

        An existing `.gitignore` is left alone, because the operator may
        have extended it.
        """
        make_private_dir(self.envs_dir)
        if not self.gitignore_path.exists():
            self.gitignore_path.write_text(GITIGNORE, encoding="utf-8")

    def current(self) -> str | None:
        """Returns the active prefix, or None when none is set."""
        try:
            text = self.current_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        return text.strip() or None

    def set_current(self, prefix: str) -> None:
        """Makes a prefix the active environment.

        Args:
            prefix: The environment prefix.

        Raises:
            ValueError: If the prefix is not a valid environment name.
        """
        _check_env_name(prefix)
        self.ensure()
        self.current_file.write_text(f"{prefix}\n", encoding="utf-8")

    def list_envs(self) -> list[str]:
        """Returns the sorted prefixes of environments with answers."""
        if not self.envs_dir.is_dir():
            return []
        return sorted(
            path.name
            for path in self.envs_dir.iterdir()
            if PREFIX_RE.match(path.name) and (path / "answers.yaml").is_file()
        )

    def env(self, prefix: str) -> EnvPaths:
        """Returns the paths of an environment, which may not exist yet.

        Args:
            prefix: The environment prefix.

        Raises:
            ValueError: If the prefix is not a valid environment name.
        """
        _check_env_name(prefix)
        return EnvPaths(self.envs_dir / prefix, prefix)

    def stale_current_message(self) -> str | None:
        """Returns why the current environment no longer exists, if it does not.

        `current` keeps naming an environment after someone deletes its
        directory by hand.

        Returns:
            The explanation, or None when no environment is current or the
            current one exists.
        """
        current = self.current()
        if current is None or current in self.list_envs():
            return None
        return (
            f"The current environment {current} no longer exists in "
            f"{self.root}. Run `stellar env list` to see the environments and "
            "`stellar env use PREFIX` to pick one, or pass --prefix."
        )

    def resolve_prefix(self, prefix: str | None) -> str:
        """Returns the given prefix, or the active one when none is given.

        Args:
            prefix: Value of the `--prefix` flag, or None.

        Raises:
            NoEnvironmentError: If no prefix is given and none is active,
                or the active one no longer exists.
        """
        if prefix:
            return prefix
        current = self.current()
        if current is None:
            raise NoEnvironmentError(
                f"No environment selected in {self.root}. Run `stellar init` "
                "to create one, `stellar env use PREFIX` to select one, or "
                "pass --prefix."
            )
        stale = self.stale_current_message()
        if stale is not None:
            raise NoEnvironmentError(stale)
        return current


def _check_env_name(prefix):
    """Rejects prefixes that are not a single safe directory name.

    Raises:
        ValueError: If the prefix does not match the environment name
            pattern.
    """
    if not PREFIX_RE.match(prefix):
        raise ValueError(
            f"Invalid prefix {prefix!r}: use lowercase letters and digits, "
            "starting with a letter"
        )
