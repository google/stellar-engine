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
workspace belongs to the environment. The one exception is the module
manifest of `terraform init`, which records the absolute directory of each
local module. A plain init keeps a record whose source did not change, so
after a relink to another engine checkout the stage would still plan with
the old checkout's modules. Sync moves such a manifest under `plans/`, and
the next init records the modules that the links give.
"""

import dataclasses
import datetime
import fnmatch
import json
import os
import pathlib
import shutil

from stellar_engine import fsutil
from stellar_engine import paths
from stellar_engine.render import writer

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
# The remote providers file that the first Stage 0 apply writes under
# `outputs_location`, which declares the bootstrap bucket as the backend.
REMOTE_BOOTSTRAP_PROVIDERS = f"providers/{BOOTSTRAP_PROVIDERS}"
# The engine directory that the environment's `modules` link points at.
MODULES = "modules"
# The manifest where `terraform init` records the directory of each module.
MODULE_MANIFEST = pathlib.PurePosixPath(".terraform/modules/modules.json")
# Module sources that Terraform resolves as local directories.
_LOCAL_SOURCES = ("./", "../")

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
# Files under `outputs_location` that a Stage 1 apply writes for Stages 2
# and 3, which `fast/stage-links.sh` links into those stages beside the
# Stage 0 outputs; tests/test_workspace.py checks the two agree.
RESMAN_OUTPUTS: tuple[str, ...] = (
    "providers/2-networking-providers.tf",
    "providers/3-security-providers.tf",
    "tfvars/1-resman.auto.tfvars.json",
)


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
        reset: Terraform files moved away because they record modules
            that the links no longer give, such as `MODULE_MANIFEST`.
        backups: The copies of the `reset` files under `plans/`, in the
            same order; a dry run makes none.
    """

    stage: str
    path: pathlib.Path
    linked: list[str] = dataclasses.field(default_factory=list)
    removed: list[str] = dataclasses.field(default_factory=list)
    created: list[str] = dataclasses.field(default_factory=list)
    conflicts: list[str] = dataclasses.field(default_factory=list)
    pending: list[str] = dataclasses.field(default_factory=list)
    reset: list[str] = dataclasses.field(default_factory=list)
    backups: list[pathlib.Path] = dataclasses.field(default_factory=list)


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


def _ensure_link(link, target, *, dry_run=False):
    """Points a symlink at a target, replacing a symlink elsewhere.

    Args:
        link: The symlink path.
        target: The absolute path the link must point at.
        dry_run: Decide without touching disk.

    Returns:
        True if the link was or would be created or repointed, False if it
        was already correct.

    Raises:
        WorkspaceError: If a real file or directory occupies the link path.
    """
    if link.is_symlink():
        if _link_target(link) == target:
            return False
        if not dry_run:
            link.unlink()
    elif link.exists():
        raise WorkspaceError(
            f"{link} is a real file or directory; move it away so it can "
            f"link to {target}"
        )
    if not dry_run:
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


def _sync_engine_links(workspace, stage_dir, fast_config, report, dry_run):
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
        if _ensure_link(link, stage_dir / name, dry_run=dry_run):
            report.linked.append(name)
    if not workspace.is_dir():
        # Only a dry run reaches this before the workspace exists.
        return
    for link in sorted(workspace.iterdir()):
        if not link.is_symlink() or link.name in wanted:
            continue
        # Only links into an engine stage directory belong to sync, whether
        # into this engine or an earlier one; other links, such as the
        # Stage 1 output links, are managed separately.
        target = _link_target(link)
        if _is_engine_stage_link(target, stage_dir.name, fast_config):
            if not dry_run:
                link.unlink()
            report.removed.append(link.name)


def _sync_bootstrap_providers(workspace, stage_dir, report, dry_run):
    """Copies `providers.tf.tmp` once, as the DDG does before Stage 0."""
    providers = workspace / BOOTSTRAP_PROVIDERS
    if providers.exists() or providers.is_symlink():
        return
    if not dry_run:
        shutil.copyfile(stage_dir / BOOTSTRAP_PROVIDERS_TEMPLATE, providers)
    report.created.append(BOOTSTRAP_PROVIDERS)


def _sync_output_links(workspace, fast_config, outputs, report, dry_run):
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
                if not dry_run:
                    link.unlink()
                report.removed.append(link.name)
            report.pending.append(relative)
            continue
        if _ensure_link(link, source, dry_run=dry_run):
            report.linked.append(link.name)


def _manifest_records(path: pathlib.Path) -> list[dict]:
    """Returns the module records of a manifest; none when unreadable.

    Terraform reports a manifest it cannot parse on its own, so sync
    leaves such a file alone.
    """
    data = fsutil.read_bytes_or_none(path)
    if data is None:
        return []
    try:
        doc = json.loads(data)
    except ValueError:
        return []
    records = doc.get("Modules") if isinstance(doc, dict) else None
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def stale_modules(workspace: pathlib.Path) -> list[str]:
    """Returns the local modules whose recorded directory the links moved.

    Terraform joins a local source to the directory of the calling module,
    resolves symlinks, and records the absolute result. A record is stale
    when the same join through the current links resolves elsewhere, such
    as into another engine checkout after a render relinked the workspace,
    even one nested inside this checkout. Registry and Git modules record
    a directory under `.terraform/`, which no link changes.

    Args:
        workspace: The stage workspace.

    Returns:
        The keys of the stale records, such as `automation-project`.
    """
    records = _manifest_records(workspace / MODULE_MANIFEST)
    dirs = {
        str(record.get("Key", "")): str(record.get("Dir", ""))
        for record in records
    }
    stale = []
    for record in records:
        key = str(record.get("Key", ""))
        source = record.get("Source")
        recorded = dirs[key]
        if not (
            key
            and isinstance(source, str)
            and source.startswith(_LOCAL_SOURCES)
            and os.path.isabs(recorded)
        ):
            continue
        parent = workspace / dirs.get(key.rpartition(".")[0], ".")
        if os.path.realpath(parent / source) != os.path.realpath(recorded):
            stale.append(key)
    return stale


def _sync_module_manifest(env, stage, report, dry_run, now):
    """Moves a module manifest that the links no longer match to `plans/`.

    It runs after the links changed, so it compares the manifest with the
    links that the next init reads. Only the manifest goes: the backend
    configuration and the providers under `.terraform/` stay.
    """
    workspace = env.workspace(stage)
    if not stale_modules(workspace):
        return
    report.reset.append(str(MODULE_MANIFEST))
    if dry_run:
        return
    manifest = workspace / MODULE_MANIFEST
    stamp = writer.stamp(now or datetime.datetime.now(datetime.UTC))
    backup = env.plans / f"{MODULE_MANIFEST.name}.{stage}.{stamp}"
    fsutil.write_private(backup, manifest.read_bytes())
    manifest.unlink()
    report.backups.append(backup)


def _stage_dir(engine_root: pathlib.Path, stage: str) -> pathlib.Path:
    """Returns the engine directory of a resolved stage.

    Raises:
        WorkspaceError: If the engine lacks the stage.
    """
    stage_dir = paths.stage_dir(engine_root, stage)
    if not stage_dir.is_dir():
        raise WorkspaceError(f"The engine has no stage directory {stage_dir}")
    return stage_dir


def sync(
    env: paths.EnvPaths,
    engine_root: pathlib.Path,
    stage: str,
    *,
    dry_run: bool = False,
    now: datetime.datetime | None = None,
) -> SyncReport:
    """Creates or refreshes the workspace of a stage.

    The sync is idempotent: a second run links and removes nothing. After
    the links, it moves a module manifest that records modules the links
    no longer give under `plans/`; see `stale_modules`.

    Args:
        env: The environment that owns the workspace.
        engine_root: Root of the engine checkout.
        stage: A stage name or alias.
        dry_run: Fill the report with what the sync would do, without
            touching disk or the `modules` link.
        now: The current time, which names the manifest backup; the clock
            when None.

    Returns:
        The changes made, or that a dry run would make, and the problems
        found.

    Raises:
        ValueError: If the stage is unknown.
        WorkspaceError: If the engine lacks the stage, or a real file or
            directory occupies the `modules` link.
    """
    stage = paths.resolve_stage(stage)
    engine_root = pathlib.Path(engine_root).resolve()
    stage_dir = _stage_dir(engine_root, stage)
    workspace = env.workspace(stage)
    report = SyncReport(stage, workspace)
    if not dry_run:
        env.ensure()
        paths.make_private_dir(workspace)
        _ensure_link(env.modules_link, engine_root / MODULES)
    fast_config = pathlib.Path(env.fast_config)
    _sync_engine_links(workspace, stage_dir, fast_config, report, dry_run)
    if stage == paths.BOOTSTRAP:
        _sync_bootstrap_providers(workspace, stage_dir, report, dry_run)
    _sync_output_links(
        workspace, fast_config, OUTPUT_LINKS[stage], report, dry_run
    )
    _sync_module_manifest(env, stage, report, dry_run, now)
    return report


def stale_links(
    env: paths.EnvPaths, engine_root: pathlib.Path, stage: str
) -> list[str]:
    """Returns what `sync` would create, change or remove in a workspace.

    A dry run of `sync`, so the two never disagree: the `modules` link, the
    engine stage links, the Stage 0 providers copy, the links to earlier
    stage outputs, and `MODULE_MANIFEST` when it records modules that the
    current links no longer give. A real file that occupies a link path
    stays out, because sync keeps it too. An output that does not exist
    yet is listed by its path under `outputs_location`, because the stage
    cannot plan without it. The manifest is compared with the current
    links, so while a link is stale the list names the link, and sync
    moves the manifest once it relinked.

    Args:
        env: The environment that owns the workspace.
        engine_root: Root of the engine checkout.
        stage: A stage name or alias.

    Returns:
        The names in sync order; empty when sync changes nothing.

    Raises:
        ValueError: If the stage is unknown.
        WorkspaceError: If the engine lacks the stage.
    """
    report = sync(env, engine_root, stage, dry_run=True)
    modules = pathlib.Path(engine_root).resolve() / MODULES
    link = env.modules_link
    found = (
        [] if link.is_symlink() and _link_target(link) == modules else [MODULES]
    )
    return [
        *found,
        *report.linked,
        *report.removed,
        *report.created,
        *report.pending,
        *report.reset,
    ]


def remote_bootstrap_providers(env: paths.EnvPaths) -> pathlib.Path:
    """Returns the remote Stage 0 providers file under `outputs_location`.

    Args:
        env: The environment.
    """
    return env.fast_config / REMOTE_BOOTSTRAP_PROVIDERS
