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

"""Builds per-environment stage workspaces as symlink farms.

A workspace mirrors `fast/stages-aw/<stage>/` of the engine with absolute
symlinks, so the engine code stays shared while each environment keeps its
own real files: tfvars, provider files, import blocks, the Stage 0 phase
file, `.terraform/` and the local Stage 0 state. Stage code reaches modules
as `../../../modules`, which resolves to the environment's `modules`
symlink.

Sync never overwrites or deletes a real file, because every real file in a
workspace belongs to the environment.
"""

import dataclasses
import fnmatch
import os
import pathlib
import shutil

from stellar_engine import paths

# Engine entries that each environment owns or that Terraform never reads.
EXCLUDED_PATTERNS = (
    "terraform.tfvars",
    "terraform.tfvars.json",
    "*.tfvars.sample",
    "terraform.tfvars.backup.*",
    "*.md",
    "*.png",
    "*.svg",
    "*.gif",
    "*.tmp",
    ".terraform",
    ".terraform.lock.hcl",
    ".terraform.tfstate.lock.info",
    "terraform.tfstate*",
    "*providers.tf",
    "*.auto.tfvars",
    "*.auto.tfvars.json",
)

# The DDG copies this file before the first Stage 0 apply. It stays a real
# file because state migration later replaces it with the remote providers.
BOOTSTRAP_PROVIDERS_TEMPLATE = "providers.tf.tmp"
BOOTSTRAP_PROVIDERS = "0-bootstrap-providers.tf"

# Files under `outputs_location` that each stage links, mirroring
# `fast/stage-links.sh`; tests/test_workspace.py checks the two agree.
OUTPUT_LINKS: dict[str, tuple[str, ...]] = {
    paths.BOOTSTRAP: (),
    paths.RESMAN: (
        "providers/1-resman-providers.tf",
        "tfvars/0-globals.auto.tfvars.json",
        "tfvars/0-bootstrap.auto.tfvars.json",
    ),
}


class WorkspaceError(Exception):
    """Raised when a workspace cannot be built safely."""


@dataclasses.dataclass
class SyncReport:
    """What a workspace sync changed and what it could not do.

    Attributes:
        stage: The stage name.
        path: The workspace directory.
        linked: Names created or repointed as symlinks.
        removed: Stale symlinks removed.
        created: Real files created, such as `0-bootstrap-providers.tf`.
        conflicts: Real files that shadow an engine entry.
        pending: Stage outputs under `outputs_location` that do not exist
            yet, relative to it.
    """

    stage: str
    path: pathlib.Path
    linked: list[str] = dataclasses.field(default_factory=list)
    removed: list[str] = dataclasses.field(default_factory=list)
    created: list[str] = dataclasses.field(default_factory=list)
    conflicts: list[str] = dataclasses.field(default_factory=list)
    pending: list[str] = dataclasses.field(default_factory=list)


def is_excluded(name: str) -> bool:
    """Returns whether an engine stage entry stays out of workspaces.

    Args:
        name: File or directory name inside the engine stage directory.
    """
    return any(
        fnmatch.fnmatchcase(name, pattern) for pattern in EXCLUDED_PATTERNS
    )


def _link_target(link):
    """Returns the absolute target of a symlink."""
    target = pathlib.Path(os.readlink(link))
    if not target.is_absolute():
        target = link.parent / target
    return pathlib.Path(os.path.normpath(target))


def _ensure_link(link, target):
    """Points a symlink at a target, replacing a symlink elsewhere.

    Returns:
        True if the link was created or repointed, False if it was already
        correct.

    Raises:
        WorkspaceError: If a real file or directory occupies the link path.
    """
    if link.is_symlink():
        if _link_target(link) == target:
            return False
        link.unlink()
    elif link.exists():
        raise WorkspaceError(
            f"{link} is a real file or directory; move it away so it can "
            f"link to {target}"
        )
    link.symlink_to(target)
    return True


def _is_engine_stage_link(target, stage, fast_config):
    """Returns whether a link target is an entry of any engine's stage dir.

    The link may point into another engine checkout, after a render with a
    different `--repo`. Links into `outputs_location` are the Stage 1 output
    links, which `_sync_output_links` manages.
    """
    if target == fast_config or target.is_relative_to(fast_config):
        return False
    parent = target.parent
    depth = len(paths.STAGES_DIR.parts)
    return (
        parent.name == stage
        and parent.parent.parts[-depth:] == paths.STAGES_DIR.parts
    )


def _sync_engine_links(workspace, stage_dir, fast_config, report):
    """Links the engine stage entries and removes stale engine links."""
    wanted = {
        entry.name
        for entry in stage_dir.iterdir()
        if not is_excluded(entry.name)
    }
    for name in sorted(wanted):
        link = workspace / name
        if link.exists() and not link.is_symlink():
            report.conflicts.append(name)
            continue
        if _ensure_link(link, stage_dir / name):
            report.linked.append(name)
    for link in sorted(workspace.iterdir()):
        if not link.is_symlink() or link.name in wanted:
            continue
        # Only links into an engine stage directory belong to sync, whether
        # into this engine or an earlier one; other links, such as the
        # Stage 1 output links, are managed separately.
        target = _link_target(link)
        if _is_engine_stage_link(target, stage_dir.name, fast_config):
            link.unlink()
            report.removed.append(link.name)


def _sync_bootstrap_providers(workspace, stage_dir, report):
    """Copies `providers.tf.tmp` once, as the DDG does before Stage 0."""
    providers = workspace / BOOTSTRAP_PROVIDERS
    if providers.exists() or providers.is_symlink():
        return
    shutil.copyfile(stage_dir / BOOTSTRAP_PROVIDERS_TEMPLATE, providers)
    report.created.append(BOOTSTRAP_PROVIDERS)


def _sync_output_links(workspace, fast_config, outputs, report):
    """Links the earlier stage outputs a stage reads, when they exist."""
    for relative in outputs:
        source = fast_config / relative
        link = workspace / pathlib.PurePosixPath(relative).name
        if link.exists() and not link.is_symlink():
            # The operator placed the file by hand; it wins.
            continue
        if not source.is_file():
            # A dangling link would make Terraform fail on a missing file.
            if link.is_symlink() and _link_target(link) == source:
                link.unlink()
                report.removed.append(link.name)
            report.pending.append(relative)
            continue
        if _ensure_link(link, source):
            report.linked.append(link.name)


def sync(
    env: paths.EnvPaths, engine_root: pathlib.Path, stage: str
) -> SyncReport:
    """Creates or refreshes the workspace of a stage.

    The sync is idempotent: a second run links and removes nothing.

    Args:
        env: The environment that owns the workspace.
        engine_root: Root of the engine checkout.
        stage: A stage name or alias.

    Returns:
        The changes made and the problems found.

    Raises:
        ValueError: If the stage is unknown.
        WorkspaceError: If the engine lacks the stage, or a real file or
            directory occupies the `modules` link.
    """
    stage = paths.resolve_stage(stage)
    engine_root = pathlib.Path(engine_root).resolve()
    stage_dir = paths.stage_dir(engine_root, stage)
    if not stage_dir.is_dir():
        raise WorkspaceError(f"The engine has no stage directory {stage_dir}")
    workspace = env.workspace(stage)
    report = SyncReport(stage, workspace)
    env.ensure()
    paths.make_private_dir(workspace)
    _ensure_link(env.modules_link, engine_root / "modules")
    _sync_engine_links(
        workspace, stage_dir, pathlib.Path(env.fast_config), report
    )
    if stage == paths.BOOTSTRAP:
        _sync_bootstrap_providers(workspace, stage_dir, report)
    _sync_output_links(workspace, env.fast_config, OUTPUT_LINKS[stage], report)
    return report
