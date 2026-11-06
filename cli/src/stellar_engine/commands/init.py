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

"""The `stellar init` command, which writes an environment's answers."""

import dataclasses
import pathlib
import random
from typing import Annotated, Any

import typer

from stellar_engine import paths
from stellar_engine import tools as tools_lib
from stellar_engine.commands import common
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import seed as seed_lib
from stellar_engine.config import validate as validate_lib
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import live
from stellar_engine.render import imports as imports_lib
from stellar_engine.wizard import discovery
from stellar_engine.wizard import flow


def init(
    prefix: common.PrefixOption = None,
    answers_from: Annotated[
        str | None,
        typer.Option(
            "--answers-from",
            help=(
                "Seed a new environment from another environment's prefix "
                "or an answers.yaml path."
            ),
        ),
    ] = None,
    assignments: Annotated[
        list[str] | None,
        typer.Option(
            "--set",
            help=(
                "Set an answer as KEY=VALUE, for example billing.no_iam=true. "
                "VALUE is YAML, so lists and maps work. Repeatable."
            ),
        ),
    ] = None,
    from_config_env: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--from-config-env",
            help="Seed a new environment from a scripts/config.env file.",
            exists=True,
            dir_okay=False,
        ),
    ] = None,
    sections: Annotated[
        list[str] | None,
        typer.Option(
            "--section",
            help="Ask only this wizard section. Repeatable.",
        ),
    ] = None,
    new_prefix: Annotated[
        bool,
        typer.Option(
            "--new-prefix",
            help="Suggest a fresh prefix with a random suffix.",
        ),
    ] = False,
    offline: Annotated[
        bool,
        typer.Option(
            "--offline", help="Skip Google Cloud lookups for defaults."
        ),
    ] = False,
    non_interactive: Annotated[
        bool,
        common.non_interactive_option(
            "Never prompt; fail on missing or invalid answers."
        ),
    ] = False,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Create or update an environment's answers.yaml.

    A rerun on an existing environment keeps its answers as defaults and
    keeps the comments in the file.
    """
    session = common.session(home, repo)
    base = _init_base(
        session.home, prefix, answers_from, from_config_env, new_prefix
    )
    data = base.data
    if prefix:
        data["prefix"] = prefix
    with common.ExitOn(ValueError):
        data = answers_lib.apply_sets(data, assignments or [])
    if new_prefix and base.env is None and not data.get("prefix"):
        start = (base.source or {}).get("prefix") or _domain_label(data)
        data["prefix"] = seed_lib.suggest_prefix(
            str(start),
            session.repo.prefix_max_length(),
            random.SystemRandom(),
        )
        typer.echo(f"Suggested prefix {data['prefix']}.")
    if common.interactive(non_interactive):
        data = _run_wizard(data, session.repo, offline, sections)
    elif sections:
        common.fail("--section needs an interactive terminal.")
    origin = " and ".join(
        part for part in (base.origin, "--set" if assignments else None) if part
    )
    answers, env = _save_answers(session, data, base, origin or None)

    if base.source is not None:
        notes = seed_lib.review_notes(base.source, answers.compliance.regime)
        if notes:
            typer.echo(common.bullets("Review these carried answers:", notes))
    for stage in paths.STAGES:
        for line in imports_lib.warnings(answers, stage, session.repo):
            common.warn(line)
    typer.echo(f"Saved {env.answers}.")
    typer.echo(f"Current environment: {env.prefix}.")
    typer.echo("Next: stellar render")


def _domain_label(data):
    organization = data.get("organization")
    if isinstance(organization, dict):
        return str(organization.get("domain") or "").split(".")[0]
    return ""


@dataclasses.dataclass
class _InitBase:
    """Where `init` starts from.

    Attributes:
        data: Answer data to start from.
        env: The existing environment being updated, or None for a new one.
        previous: The round-trip map of the existing answers, whose
            comments survive the save.
        source: Answer data of the `--answers-from` source, for the review
            notes.
        origin: The input the data comes from, for error messages, such as
            the existing answers file or `--from-config-env PATH`.
    """

    data: dict
    env: paths.EnvPaths | None = None
    previous: Any = None
    source: dict | None = None
    origin: str | None = None


def _init_base(home_obj, prefix, answers_from, from_config_env, new_prefix):
    """Picks the starting data: existing answers, a seed, or nothing.

    Without `--prefix`, a plain `init` updates the current environment,
    while a seeding option starts a new one.
    """
    seeded = bool(answers_from or from_config_env or new_prefix)
    target = prefix or (None if seeded else home_obj.current())
    if target and not prefix:
        stale = home_obj.stale_current_message()
        if stale is not None:
            common.warn(f"{stale} init now creates {target} from scratch.")
    if target:
        with common.ExitOn(ValueError):
            env = home_obj.env(target)
        if env.answers.is_file():
            with common.ExitOn(answers_lib.AnswersError):
                previous = answers_lib.load_data(env.answers)
            if seeded:
                common.warn(
                    f"Environment {env.prefix} exists, so its answers are "
                    "used and --answers-from, --from-config-env and "
                    "--new-prefix are ignored."
                )
            return _InitBase(
                answers_lib.plain(previous),
                env,
                previous,
                origin=str(env.answers),
            )
    if answers_from:
        with common.ExitOn(FileNotFoundError, answers_lib.AnswersError):
            source_path = seed_lib.resolve_source(answers_from, home_obj)
            source = answers_lib.plain(answers_lib.load_data(source_path))
        typer.echo(f"Seeding from {source_path}.")
        return _InitBase(
            seed_lib.seed(source),
            source=source,
            origin=f"--answers-from {source_path}",
        )
    if from_config_env:
        return _InitBase(
            answers_lib.from_config_env(from_config_env),
            origin=f"--from-config-env {from_config_env}",
        )
    # A new environment starts from its prefix, so a sparse `--set` names
    # only the fields still missing.
    return _InitBase({"prefix": target} if target else {})


def _save_answers(session, data, base, origin=None):
    """Validates the answers, records the engine and saves them, or exits 2.

    Args:
        session: The engine checkout and home.
        data: The answer data to save.
        base: Where `init` started from.
        origin: The inputs that supplied the data, for error messages.

    Returns:
        The saved answers and their environment paths.
    """
    data["engine"] = {"path": str(session.repo.root)}
    with common.ExitOn(answers_lib.AnswersError):
        answers = answers_lib.parse(data, origin)
    if base.env is not None and answers.prefix != base.env.prefix:
        # A copy must drop the imports, overrides and engine of the source,
        # which only the seed rules of --answers-from do.
        common.fail(
            f"Changing the prefix of {base.env.prefix} to {answers.prefix} "
            "would copy its imports and overrides. Run `stellar init "
            f"--answers-from {base.env.prefix} --prefix {answers.prefix}` "
            "to start a new environment from it."
        )
    found = validate_lib.problems(answers, session.repo)
    if base.env is not None:
        found += _phase_problems(base, answers)
    if found:
        common.fail(common.bullets("The answers have problems:", found))
    home_obj = session.home
    env = home_obj.env(answers.prefix)
    # A new prefix must not silently replace another environment.
    is_update = base.env is not None and base.env.prefix == env.prefix
    if not is_update and env.answers.is_file():
        common.fail(
            f"Environment {env.prefix} already exists at {env.answers}. "
            f"Run `stellar init --prefix {env.prefix}` to update it."
        )
    home_obj.ensure()
    env.ensure()
    with common.ExitOn(answers_lib.AnswersError):
        answers_lib.save(
            env.answers,
            answers,
            home=home_obj.root,
            previous=base.previous,
        )
    home_obj.set_current(env.prefix)
    return answers, env


def _phase_problems(base, answers):
    """Refuses `stage0_phase` from final back to bootstrap after a final apply.

    The guard reads `stage0.final_applied` from the run-state of the
    environment, which `stellar deploy` sets after the final Stage 0
    apply, so a change before that apply stays possible.

    The previous answers stay unparsed, so `init` can still repair a
    file that fails the model.

    Args:
        base: Where `init` started from, an existing environment.
        answers: The answers about to be saved.

    Returns:
        The problems, empty when the phase does not regress.
    """
    previous_phase = answers_lib.plain(base.previous).get("stage0_phase")
    found = validate_lib.phase_change_problems(
        previous_phase, answers.stage0_phase
    )
    if not found:
        return []
    try:
        state = run_state_lib.load(base.env)
    except run_state_lib.RunStateError as error:
        # Without readable history, keep the deployed phase.
        return [*found, str(error)]
    return found if state.stage0.final_applied else []


def _run_wizard(data, repository, offline, sections):
    """Runs the interactive wizard, exiting 2 when answers stay invalid."""
    cloud = None if offline else live.LiveCloudApi()
    found = discovery.discover(cloud, tools_lib.SystemTools())
    prompter = common.prompter()
    for problem in found.problems:
        prompter.note(problem)
    try:
        return flow.run(
            data,
            prompter=prompter,
            repo=repository,
            discovered=found,
            sections=sections or None,
        )
    except flow.WizardError as error:
        common.fail(
            common.bullets("The answers still have problems:", error.problems)
        )
    except ValueError as error:
        common.fail(str(error))
