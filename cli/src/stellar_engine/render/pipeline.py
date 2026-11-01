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

"""Renders the stage workspaces, tfvars, import blocks and phase file.

These functions hold the steps of `stellar render`, so other commands can
run them too. They never print or prompt: they return the warnings, the
summary rows and the diff text, and `render_stage` reports and asks
through the callbacks of `WriteOptions`. Errors surface as the exceptions
of the modules called: `workspace.WorkspaceError`, `stages.RenderError`,
`imports.ImportBlockError` and `phase.PhaseFileError`.
"""

from collections.abc import Callable, Iterable
import dataclasses
import datetime
import functools
import pathlib

from stellar_engine import fsutil
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import tools as tools_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import models
from stellar_engine.render import imports as imports_lib
from stellar_engine.render import phase as phase_lib
from stellar_engine.render import stages as stages_lib
from stellar_engine.render import writer

_TFVARS = "terraform.tfvars"
_REFUSED = "refused"

# The errors that stop a render; each message tells the operator what to fix.
ERRORS = (
    workspace_lib.WorkspaceError,
    stages_lib.RenderError,
    imports_lib.ImportBlockError,
    phase_lib.PhaseFileError,
)

# A summary row: stage, file path, outcome and backup path or None.
Row = tuple[str, pathlib.Path, str, pathlib.Path | None]


@dataclasses.dataclass(frozen=True)
class WriteOptions:
    """How `render_stage` treats edited files and reports its findings.

    `render_stage` calls `warn` and `error` as soon as it finds something,
    so the operator sees the finding even when a later step fails.

    Attributes:
        force: Replaces an edited tfvars file without asking, after a
            backup.
        interactive: Asks through `confirm` before replacing the file.
        confirm: Called with the tfvars path and the diff; returns True to
            back up and replace the file.
        now: Current time, used to name backups.
        warn: Called with each finding that does not stop the render,
            such as a real file that shadows an engine file.
        error: Called with the refusal message when the tfvars file holds
            manual edits that these options do not allow to replace.
    """

    force: bool
    interactive: bool
    confirm: Callable[[pathlib.Path, str], bool]
    now: datetime.datetime
    warn: Callable[[str], None]
    error: Callable[[str], None]


@dataclasses.dataclass(frozen=True)
class StageRender:
    """What `render_stage` did in one stage workspace.

    Attributes:
        sync: The workspace sync, with its conflicts and pending outputs.
        rows: One row per file written, removed or refused, in write order.
        refused: Whether the tfvars file holds manual edits that
            `WriteOptions` does not allow to replace.
    """

    sync: workspace_lib.SyncReport
    rows: list[Row]
    refused: bool


def replace_question(target: pathlib.Path) -> str:
    """Returns the question that asks to replace an edited tfvars file.

    Args:
        target: The tfvars file that holds manual edits.
    """
    return f"{target} has manual edits. Back it up and replace it?"


def select_stages(names: Iterable[str] | None) -> list[str]:
    """Returns the stages to render in deployment order.

    Args:
        names: Stage names or aliases, such as `0` or `1-resman`. None or
            no names select every stage.

    Returns:
        The canonical stage names, each once, in `paths.STAGES` order.

    Raises:
        ValueError: If a name is not a known stage.
    """
    selected = {paths.resolve_stage(name) for name in names or []}
    return [stage for stage in paths.STAGES if stage in selected] or list(
        paths.STAGES
    )


def warnings(
    stages: Iterable[str],
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
) -> list[str]:
    """Returns the non-fatal findings about the stages to render.

    Args:
        stages: Stage names or aliases, in the order to report them.
        answers: The environment answers.
        repo: The engine checkout.
        env: The environment, whose Stage 0 workspace shows the phase.

    Returns:
        Readable sentences. For each stage, those of `imports.warnings`,
        then `stages.warnings`, then `phase.warnings` for Stage 0.

    Raises:
        ValueError: If a stage name is unknown.
    """
    found = []
    for stage in map(paths.resolve_stage, stages):
        found += imports_lib.warnings(answers, stage, repo)
        found += stages_lib.warnings(answers, stage, repo)
        if stage == paths.BOOTSTRAP:
            found += phase_lib.warnings(env.workspace(stage), answers)
    return found


def render_text(
    stage: str,
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
    tools: tools_lib.LocalTools,
) -> str:
    """Returns the `terraform.tfvars` text of a stage.

    Args:
        stage: Stage name or alias.
        answers: The environment answers.
        repo: The engine checkout.
        env: The environment.
        tools: Local tools, whose `terraform fmt` formats the text.

    Raises:
        stages.RenderError: If the answers cannot be rendered.
        ValueError: If the stage name is unknown.
    """
    rendered = stages_lib.build(stage, answers, repo, env)
    # The emitter is already canonical; fmt is only a safety net.
    return tools.terraform_fmt(rendered.text) or rendered.text


def render_stage(
    stage: str,
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
    tools: tools_lib.LocalTools,
    options: WriteOptions,
) -> StageRender:
    """Syncs a stage workspace and writes its tfvars, imports and phase file.

    An edited tfvars file that `options` does not allow to replace stays
    in place, `options.error` reports it, and the render still writes the
    import and phase files. `options.warn` reports each real file that
    shadows an engine file right after the sync.

    Args:
        stage: Stage name or alias.
        answers: The environment answers.
        repo: The engine checkout that the workspace links.
        env: The environment that owns the workspace.
        tools: Local tools, whose `terraform fmt` formats the tfvars.
        options: How to treat an edited tfvars file.

    Returns:
        The sync report, the summary rows and whether the render refused
        the tfvars file.

    Raises:
        workspace.WorkspaceError: If the workspace cannot be synced.
        stages.RenderError: If the tfvars cannot be rendered.
        imports.ImportBlockError: If the import file cannot be written.
        phase.PhaseFileError: If the phase file cannot be written.
        ValueError: If the stage name is unknown.
    """
    stage = paths.resolve_stage(stage)
    sync = workspace_lib.sync(env, repo.root, stage)
    for conflict in sync.conflicts:
        options.warn(
            f"{sync.path / conflict} is a real file that shadows the "
            "engine's file of the same name."
        )
    if stage == paths.BOOTSTRAP:
        # Refuse a foreign phase file before any write, so a refused render
        # leaves the tfvars and imports files as they were.
        phase_lib.planned(sync.path, answers, repo)
    text = render_text(stage, answers, repo, env, tools)
    row, refused = _write_tfvars(stage, sync.path / _TFVARS, text, env, options)
    rows = [row]
    imports_outcome = imports_lib.write(sync.path, stage, answers)
    if imports_outcome is not None:
        imports_target = sync.path / imports_lib.filename(stage)
        rows.append((stage, imports_target, imports_outcome.value, None))
    if stage == paths.BOOTSTRAP:
        phase_outcome = phase_lib.write(sync.path, answers, repo)
        if phase_outcome is not None:
            phase_target = sync.path / phase_lib.FILENAME
            rows.append((stage, phase_target, phase_outcome.value, None))
    return StageRender(sync, rows, refused)


def _write_tfvars(
    stage: str,
    target: pathlib.Path,
    text: str,
    env: paths.EnvPaths,
    options: WriteOptions,
) -> tuple[Row, bool]:
    """Writes the tfvars file and returns its row and whether it refused."""
    try:
        result = writer.write(
            target,
            text,
            env.generated_hash(stage),
            force=options.force,
            interactive=options.interactive,
            confirm=functools.partial(options.confirm, target),
            now=options.now,
        )
    except writer.OverwriteRefusedError as error:
        options.error(str(error))
        return (stage, target, _REFUSED, None), True
    return (stage, target, result.outcome.value, result.backup), False


def diff(
    stage: str,
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
    tools: tools_lib.LocalTools,
) -> str:
    """Returns what rendering a stage would change, writing nothing.

    The diff covers the tfvars, import and phase files. It does not sync
    the workspace, so it shows no link changes or pending outputs.

    Args:
        stage: Stage name or alias.
        answers: The environment answers.
        repo: The engine checkout.
        env: The environment whose workspace holds the current files.
        tools: Local tools, whose `terraform fmt` formats the tfvars.

    Returns:
        The unified diff of each file that would change, every one ending
        with a newline, or an empty string when nothing would change.

    Raises:
        stages.RenderError: If the tfvars file cannot be rendered.
        imports.ImportBlockError: If the import file cannot be rendered.
        phase.PhaseFileError: If the phase file cannot be rendered, or a
            phase file exists that stellar did not write.
        ValueError: If the stage name is unknown.
    """
    stage = paths.resolve_stage(stage)
    chunks = []
    for target, content in _planned(stage, answers, repo, env, tools):
        if not content and fsutil.read_text_or_none(target) is None:
            continue
        changes = writer.diff(target, content)
        if changes:
            chunks.append(changes if changes.endswith("\n") else f"{changes}\n")
    return "".join(chunks)


def _planned(
    stage: str,
    answers: models.Answers,
    repo: repo_lib.Repo,
    env: paths.EnvPaths,
    tools: tools_lib.LocalTools,
) -> list[tuple[pathlib.Path, str]]:
    """Returns each file that a render of the stage writes, with content."""
    workspace = env.workspace(stage)
    text = render_text(stage, answers, repo, env, tools)
    imports_text = imports_lib.text(answers, stage)
    planned = [
        (workspace / _TFVARS, text),
        (workspace / imports_lib.filename(stage), imports_text),
    ]
    if stage == paths.BOOTSTRAP:
        phase_text = phase_lib.planned(workspace, answers, repo)
        planned.append((workspace / phase_lib.FILENAME, phase_text))
    return planned
