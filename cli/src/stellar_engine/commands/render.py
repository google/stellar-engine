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

"""The `stellar render` command, which writes the stage workspaces."""

from typing import Annotated

import typer

from stellar_engine import paths
from stellar_engine import tools as tools_lib
from stellar_engine.commands import common
from stellar_engine.config import models
from stellar_engine.render import pipeline


def render(
    stage: Annotated[
        list[str] | None,
        typer.Option(
            "--stage",
            help="Render only this stage, such as 0 or 1-resman. Repeatable.",
        ),
    ] = None,
    show_diff: Annotated[
        bool,
        typer.Option("--diff", help="Print the changes without writing."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Replace manually edited files after backing them up.",
        ),
    ] = False,
    non_interactive: Annotated[
        bool,
        common.non_interactive_option(
            "Never prompt; refuse to replace manually edited files."
        ),
    ] = False,
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Render the stage workspaces, tfvars, import blocks and phase file.

    Each workspace links the engine's stage code and holds the files the
    environment owns, so Terraform runs from it with `-chdir`.
    """
    session = common.session(home, repo)
    env, answers = common.load_env(session, prefix)
    with common.ExitOn(ValueError):
        selected = pipeline.select_stages(stage)
    if answers.engine and answers.engine.path != str(session.repo.root):
        common.warn(
            f"answers.yaml records the engine {answers.engine.path}, but "
            f"this render uses {session.repo.root}."
        )
    for line in pipeline.warnings(selected, answers, session.repo, env):
        common.warn(line)
    local_tools = tools_lib.SystemTools()
    if show_diff:
        _print_diff(selected, answers, session, env, local_tools)
        return
    options = pipeline.WriteOptions(
        force=force,
        interactive=common.interactive(non_interactive),
        confirm=_confirm_replace,
        now=common.now(),
        warn=common.warn,
        error=common.error,
    )
    renders = {}
    for name in selected:
        renders[name] = _render_stage(
            name, answers, session, env, local_tools, options
        )
    _print_rows(env, renders.values())
    if any(result.refused for result in renders.values()):
        raise typer.Exit(common.EXIT_OVERWRITE_REFUSED)
    _print_next_steps(renders, answers)


def _print_diff(selected, answers, session, env, local_tools):
    """Prints what a render would change, stage by stage, writing nothing."""
    changed = False
    for name in selected:
        with common.ExitOn(*pipeline.ERRORS):
            changes = pipeline.diff(
                name, answers, session.repo, env, local_tools
            )
        if changes:
            changed = True
            # Every change in the text already ends with a newline.
            typer.echo(changes, nl=False)
    if not changed:
        typer.echo("No changes.")


def _confirm_replace(target, changes):
    """Shows the manual edits of a tfvars file and asks to replace it."""
    typer.echo(changes)
    return typer.confirm(pipeline.replace_question(target), default=False)


def _render_stage(name, answers, session, env, local_tools, options):
    """Renders one stage, or exits 2 on an error the operator can fix."""
    with common.ExitOn(*pipeline.ERRORS):
        return pipeline.render_stage(
            name, answers, session.repo, env, local_tools, options
        )


def _print_rows(env, renders):
    """Prints one line per file that the render wrote, removed or refused."""
    typer.echo(f"Rendered {env.prefix} in {env.root}:")
    for result in renders:
        for name, target, outcome, backup in result.rows:
            line = f"  {name:<11}  {outcome:<9}  {target}"
            if backup is not None:
                line += f"  backup {backup}"
            typer.echo(line)


def _print_next_steps(renders, answers):
    """Points at the deploy of the first rendered stage that can run.

    A stage whose Stage 0 inputs are missing says so instead.
    """
    ready = []
    for name, result in renders.items():
        if result.sync.pending:
            typer.echo(
                f"{name} waits for Stage 0 outputs: "
                f"{', '.join(result.sync.pending)}. Run stellar deploy "
                "--stage 0 first; stellar deploy --stage 1 then fetches "
                "them and renders the stage again."
            )
        else:
            ready.append(name)
    if not ready:
        return
    typer.echo(f"Next: stellar deploy --stage {paths.stage_alias(ready[0])}")
    if ready[0] == paths.BOOTSTRAP and (
        answers.stage0_phase == models.STAGE0_BOOTSTRAP
    ):
        typer.echo(
            "stellar deploy runs the first apply in the bootstrap phase, "
            "moves the state to the bootstrap bucket, switches "
            f"stage0_phase to {models.STAGE0_FINAL} and runs the final "
            "apply. stellar guide --stage 0 lists the manual commands."
        )
