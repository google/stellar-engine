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

"""Command line entry point for the `stellar` command.

Every command uses the same exit codes: 0 on success, 1 when preflight
checks fail or `imports scan` cannot read Google Cloud, 2 on usage or
validation errors, and 3 when `render` refuses to overwrite a manually
edited file.
"""

import dataclasses
import datetime
import os
import pathlib
import random
import shlex
import sys
from typing import Annotated, Any, NoReturn

import pydantic
from rich import console as rich_console
from rich import table as rich_table
import typer

import stellar_engine
from stellar_engine import fsutil
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import tools as tools_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import derive
from stellar_engine.config import models
from stellar_engine.config import seed as seed_lib
from stellar_engine.config import validate as validate_lib
from stellar_engine.gcp import api
from stellar_engine.gcp import live
from stellar_engine.preflight import checks
from stellar_engine.preflight import inputs as inputs_lib
from stellar_engine.preflight import report
from stellar_engine.preflight import runner
from stellar_engine.render import imports as imports_lib
from stellar_engine.render import phase as phase_lib
from stellar_engine.render import stages as stages_lib
from stellar_engine.render import writer
from stellar_engine.wizard import discovery
from stellar_engine.wizard import flow
from stellar_engine.wizard import prompts

app = typer.Typer(
    help="Validate and guide Stellar Engine deployments.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)
env_app = typer.Typer(
    help="List, select and inspect the environments of a home.",
    no_args_is_help=True,
)
app.add_typer(env_app, name="env")
imports_app = typer.Typer(
    help="Find resources that exist before Stage 0, so Stage 0 imports them.",
    no_args_is_help=True,
)
app.add_typer(imports_app, name="imports")

_EXIT_CLOUD = 1
_EXIT_USAGE = 2
_EXIT_OVERWRITE_REFUSED = 3

_TFVARS = "terraform.tfvars"
_STAGE0_PLAN = "s0.tfplan"
_HOME_SOURCES = {
    paths.HomeSource.FLAG: "from the --home flag",
    paths.HomeSource.ENV: f"from {paths.HOME_ENV_VAR}",
    paths.HomeSource.DEFAULT: "default inside the engine checkout",
}

# The shared options. `--home` deliberately has no envvar: Typer would copy
# STELLAR_HOME into the flag, and `env show` could no longer tell where the
# home came from. `paths.resolve_home` reads the variable itself.
HomeOption = Annotated[
    pathlib.Path | None,
    typer.Option(
        "--home",
        help=(
            "Home folder that holds the environments. Defaults to "
            f"${paths.HOME_ENV_VAR}, then <engine checkout>/"
            f"{paths.HOME_DIRNAME}."
        ),
        file_okay=False,
    ),
]
PrefixOption = Annotated[
    str | None,
    typer.Option(
        "--prefix",
        envvar="STELLAR_PREFIX",
        help="Environment prefix. Defaults to the current environment.",
    ),
]
RepoOption = Annotated[
    pathlib.Path | None,
    typer.Option(
        "--repo", help="Stellar Engine checkout to read. Auto-detected."
    ),
]


def _version_callback(value):
    if value:
        typer.echo(f"stellar {stellar_engine.__version__}")
        raise typer.Exit


@app.callback()
def main(
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
):
    """Validate and guide Stellar Engine deployments."""


def _error(message):
    """Prints an error to stderr without exiting."""
    typer.secho(f"Error: {message}", fg="red", err=True)


def _fail(message, code=_EXIT_USAGE) -> NoReturn:
    """Prints an error to stderr and exits with `code`."""
    _error(message)
    raise typer.Exit(code)


def _warn(message):
    typer.secho(f"Warning: {message}", fg="yellow", err=True)


def _stdin_is_tty():
    # A function so tests can make a CliRunner invocation interactive.
    return sys.stdin.isatty()


def _interactive(non_interactive):
    return not non_interactive and _stdin_is_tty()


@dataclasses.dataclass(frozen=True)
class _Session:
    """The engine checkout and home that one command works with."""

    repo: repo_lib.Repo
    resolved: paths.ResolvedHome

    @property
    def home(self):
        return paths.Home(self.resolved.path)


def _session(home_flag, repo_flag):
    """Resolves the engine checkout, then the home inside or beside it."""
    try:
        repository = repo_lib.Repo(repo_lib.find_root(repo_flag))
    except repo_lib.RepoError as error:
        _fail(str(error))
    resolved = paths.resolve_home(home_flag, os.environ, repository.root)
    return _Session(repository, resolved)


def _env(home, prefix):
    """Returns the paths of the selected environment, or exits 2."""
    try:
        return home.env(home.resolve_prefix(prefix))
    except (paths.NoEnvironmentError, ValueError) as error:
        _fail(str(error))


def _load_answers(env, repository, *, check_repo=True):
    """Loads and validates an environment's answers, or exits 2.

    Args:
        env: The environment paths.
        repository: The engine checkout.
        check_repo: Whether to also apply the repository rules of
            `validate.problems`.
    """
    if not env.answers.is_file():
        _fail(
            f"No answers for {env.prefix} at {env.answers}. Run `stellar "
            f"init --prefix {env.prefix}` first."
        )
    try:
        answers = answers_lib.load(env.answers)
    except answers_lib.AnswersError as error:
        _fail(str(error))
    if answers.prefix != env.prefix:
        _fail(
            f"{env.answers} sets prefix {answers.prefix}, but it belongs to "
            f"environment {env.prefix}. Set prefix back to {env.prefix}, or "
            f"run `stellar init --answers-from {env.prefix} --prefix "
            f"{answers.prefix}` to copy it into a new environment."
        )
    if check_repo:
        found = validate_lib.problems(answers, repository)
        if found:
            _fail(_bullets(f"{env.answers} has problems:", found))
    return answers


def _bullets(title, lines):
    return "\n".join([title, *(f"- {line}" for line in lines)])


def _domain_label(data):
    organization = data.get("organization")
    if isinstance(organization, dict):
        return str(organization.get("domain") or "").split(".")[0]
    return ""


@app.command()
def init(
    prefix: PrefixOption = None,
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
        typer.Option(
            "--non-interactive",
            help="Never prompt; fail on missing or invalid answers.",
        ),
    ] = False,
    home: HomeOption = None,
    repo: RepoOption = None,
):
    """Create or update an environment's answers.yaml.

    A rerun on an existing environment keeps its answers as defaults and
    keeps the comments in the file.
    """
    session = _session(home, repo)
    base = _init_base(
        session.home, prefix, answers_from, from_config_env, new_prefix
    )
    data = base.data
    if prefix:
        data["prefix"] = prefix
    try:
        data = answers_lib.apply_sets(data, assignments or [])
    except ValueError as error:
        _fail(str(error))
    if new_prefix and base.env is None and not data.get("prefix"):
        start = (base.source or {}).get("prefix") or _domain_label(data)
        data["prefix"] = seed_lib.suggest_prefix(
            str(start),
            session.repo.prefix_max_length(),
            random.SystemRandom(),
        )
        typer.echo(f"Suggested prefix {data['prefix']}.")
    if _interactive(non_interactive):
        data = _run_wizard(data, session.repo, offline, sections)
    elif sections:
        _fail("--section needs an interactive terminal.")
    origin = " and ".join(
        part for part in (base.origin, "--set" if assignments else None) if part
    )
    answers, env = _save_answers(session, data, base, origin or None)

    if base.source is not None:
        notes = seed_lib.review_notes(base.source, answers.compliance.regime)
        if notes:
            typer.echo(_bullets("Review these carried answers:", notes))
    for stage in paths.STAGES:
        for line in imports_lib.warnings(answers, stage, session.repo):
            _warn(line)
    typer.echo(f"Saved {env.answers}.")
    typer.echo(f"Current environment: {env.prefix}.")
    typer.echo("Next: stellar render")


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
            _warn(f"{stale} init now creates {target} from scratch.")
    if target:
        try:
            env = home_obj.env(target)
        except ValueError as error:
            _fail(str(error))
        if env.answers.is_file():
            try:
                previous = answers_lib.load_data(env.answers)
            except answers_lib.AnswersError as error:
                _fail(str(error))
            if seeded:
                _warn(
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
        try:
            source_path = seed_lib.resolve_source(answers_from, home_obj)
            source = answers_lib.plain(answers_lib.load_data(source_path))
        except (FileNotFoundError, answers_lib.AnswersError) as error:
            _fail(str(error))
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
    try:
        answers = answers_lib.parse(data, origin)
    except answers_lib.AnswersError as error:
        _fail(str(error))
    if base.env is not None and answers.prefix != base.env.prefix:
        # A copy must drop the imports, overrides and engine of the source,
        # which only the seed rules of --answers-from do.
        _fail(
            f"Changing the prefix of {base.env.prefix} to {answers.prefix} "
            "would copy its imports and overrides. Run `stellar init "
            f"--answers-from {base.env.prefix} --prefix {answers.prefix}` "
            "to start a new environment from it."
        )
    found = validate_lib.problems(answers, session.repo)
    if found:
        _fail(_bullets("The answers have problems:", found))
    home_obj = session.home
    env = home_obj.env(answers.prefix)
    # A new prefix must not silently replace another environment.
    is_update = base.env is not None and base.env.prefix == env.prefix
    if not is_update and env.answers.is_file():
        _fail(
            f"Environment {env.prefix} already exists at {env.answers}. "
            f"Run `stellar init --prefix {env.prefix}` to update it."
        )
    home_obj.ensure()
    env.ensure()
    try:
        answers_lib.save(
            env.answers,
            answers,
            home=home_obj.root,
            previous=base.previous,
        )
    except answers_lib.AnswersError as error:
        _fail(str(error))
    home_obj.set_current(env.prefix)
    return answers, env


def _run_wizard(data, repository, offline, sections):
    """Runs the interactive wizard, exiting 2 when answers stay invalid."""
    cloud = None if offline else live.LiveCloudApi()
    found = discovery.discover(cloud, tools_lib.SystemTools())
    prompter = prompts.QuestionaryPrompter()
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
        _fail(_bullets("The answers still have problems:", error.problems))
    except ValueError as error:
        _fail(str(error))


@env_app.command("list")
def env_list(home: HomeOption = None, repo: RepoOption = None):
    """List the environments of the home."""
    session = _session(home, repo)
    home_obj = session.home
    prefixes = home_obj.list_envs()
    if not prefixes:
        typer.echo(f"No environments in {home_obj.root}. Run stellar init.")
        return
    current = home_obj.current()
    table = rich_table.Table("", "Prefix", "Regime", "Region", "Organization")
    for name in prefixes:
        marker = "*" if name == current else ""
        try:
            answers = answers_lib.load(home_obj.env(name).answers)
        except answers_lib.AnswersError:
            table.add_row(marker, name, "invalid answers", "", "")
            continue
        if answers.prefix != name:
            table.add_row(
                marker, name, f"answers set prefix {answers.prefix}", "", ""
            )
            continue
        table.add_row(
            marker,
            name,
            answers.compliance.regime,
            answers.region,
            answers.organization.id,
        )
    rich_console.Console().print(table)
    typer.echo(f"Home: {home_obj.root}")
    stale = home_obj.stale_current_message()
    if stale is not None:
        _warn(stale)


@env_app.command("use")
def env_use(
    prefix: Annotated[str, typer.Argument(help="Environment prefix.")],
    home: HomeOption = None,
    repo: RepoOption = None,
):
    """Make an environment the current one."""
    home_obj = _session(home, repo).home
    if prefix not in home_obj.list_envs():
        _fail(f"No environment {prefix} in {home_obj.root}.")
    home_obj.set_current(prefix)
    typer.echo(f"Current environment: {prefix}.")


@env_app.command("show")
def env_show(
    prefix: PrefixOption = None,
    home: HomeOption = None,
    repo: RepoOption = None,
):
    """Show where an environment lives and the values derived from it."""
    session = _session(home, repo)
    home_obj = session.home
    source = _HOME_SOURCES[session.resolved.source]
    typer.echo(f"Home: {home_obj.root} ({source})")
    env = _env(home_obj, prefix)
    answers = _load_answers(env, session.repo)
    current = " (current)" if home_obj.current() == env.prefix else ""
    typer.echo(f"Environment: {env.prefix}{current}")
    typer.echo(f"Answers: {env.answers}")
    engine = answers.engine.path if answers.engine else "not recorded"
    typer.echo(f"Engine: {engine}")
    typer.echo(f"Outputs location: {env.fast_config}")
    typer.echo(f"Stage 0 phase: {answers.stage0_phase}")
    typer.echo("Workspaces:")
    for stage in paths.STAGES:
        typer.echo(f"  {stage}: {env.workspace(stage)}")
    typer.echo("Derived values:")
    typer.echo(
        f"  KMS protection level: {derive.kms_protection_level(answers)}"
    )
    typer.echo(
        f"  Assured Workloads location: {derive.compliance_location(answers)}"
    )
    typer.echo("  Stage 0 project IDs and deletion policies:")
    policies = derive.stage0_deletion_policies(answers, session.repo)
    for project_id, policy in policies.items():
        typer.echo(f"    {project_id}  {policy}")
    for tenant, project_ids in derive.tenant_project_ids(answers).items():
        typer.echo(f"  Tenant {tenant} project IDs:")
        for project_id in project_ids:
            typer.echo(f"    {project_id}")
    for stage, entries in answers.imports.items():
        typer.echo(f"Imports for {stage}:")
        for address, import_id in sorted(entries.items()):
            typer.echo(f"  {address} = {import_id}")
    if answers.existing_org_policies:
        typer.echo("Existing organization policies that Stage 0 imports:")
        for name in answers.existing_org_policies:
            typer.echo(f"  {name}")


_SCAN_RESULTS = {
    "kept": "import on the final Stage 0 apply",
    "custom": "skip, Stage 0 creates the custom constraint",
    "undeclared": "skip, Stage 0 does not set it for this regime",
}


@imports_app.command("scan")
def imports_scan(
    prefix: PrefixOption = None,
    home: HomeOption = None,
    repo: RepoOption = None,
):
    """Record the existing organization policies that Stage 0 imports.

    The command lists the policies on the organization, keeps those that
    Stage 0 declares, and saves them to existing_org_policies in
    answers.yaml, so stellar render writes their import block. It only
    reads from Google Cloud.
    """
    session = _session(home, repo)
    env = _env(session.home, prefix)
    # The scan replaces existing_org_policies, so a stale list must not
    # stop it; the updated answers are validated before the save.
    answers = _load_answers(env, session.repo, check_repo=False)
    org_id = answers.organization.id
    try:
        existing = live.LiveCloudApi().list_org_policies(org_id)
    except (api.CloudError, api.CredentialsError) as error:
        _fail(
            f"Cannot list the policies of organization {org_id}: {error}",
            _EXIT_CLOUD,
        )
    scan = session.repo.scan_org_policies(existing, answers.compliance.regime)
    if existing:
        table = rich_table.Table("Constraint", "Result")
        for field, result in _SCAN_RESULTS.items():
            for name in getattr(scan, field):
                table.add_row(name, result)
        rich_console.Console().print(table)
    else:
        typer.echo(f"Organization {org_id} has no organization policies.")
    data = answers.model_dump(mode="json", exclude_none=True)
    data["existing_org_policies"] = list(scan.kept)
    updated = models.Answers.model_validate(data)
    found = validate_lib.problems(updated, session.repo)
    if found:
        _fail(_bullets("The answers have problems:", found))
    if updated.existing_org_policies == answers.existing_org_policies:
        typer.echo(f"{env.answers} already lists these policies.")
    else:
        try:
            answers_lib.save(
                env.answers,
                updated,
                home=session.home.root,
                previous=answers_lib.load_data(env.answers),
            )
        except answers_lib.AnswersError as error:
            _fail(str(error))
        typer.echo(
            f"Saved {len(scan.kept)} organization policies to "
            f"existing_org_policies in {env.answers}."
        )
    typer.echo("Next: stellar render")


def _confirm_replace(target):
    def confirm(changes):
        typer.echo(changes)
        return typer.confirm(
            f"{target} has manual edits. Back it up and replace it?",
            default=False,
        )

    return confirm


def _write_imports(workspace, stage, answers):
    """Writes the import file and returns its path and what happened."""
    try:
        outcome = imports_lib.write(workspace, stage, answers)
    except imports_lib.ImportBlockError as error:
        _fail(str(error))
    return workspace / imports_lib.filename(stage), outcome


def _planned_phase(workspace, answers, repository):
    """Returns the planned Stage 0 phase file text or exits on an error."""
    try:
        return phase_lib.planned(workspace, answers, repository)
    except phase_lib.PhaseFileError as error:
        _fail(str(error))


def _write_phase(workspace, answers, repository):
    """Writes or removes the Stage 0 phase file and returns what happened."""
    try:
        return phase_lib.write(workspace, answers, repository)
    except phase_lib.PhaseFileError as error:
        _fail(str(error))


def _render_text(stage, answers, session, env, local_tools):
    try:
        rendered = stages_lib.build(stage, answers, session.repo, env)
    except stages_lib.RenderError as error:
        _fail(str(error))
    # The emitter is already canonical; fmt is only a safety net.
    return local_tools.terraform_fmt(rendered.text) or rendered.text


def _print_next_steps(stage, workspace, answers, reports):
    chdir = f"terraform -chdir={shlex.quote(str(workspace))}"
    sync = reports.get(stage)
    if sync is not None and sync.pending:
        typer.echo(
            f"{stage} waits for Stage 0 outputs: {', '.join(sync.pending)}. "
            "Apply Stage 0, then rerun stellar render."
        )
        return
    typer.echo(f"Next steps for {stage}:")
    typer.echo(f"  {chdir} init")
    if stage != paths.BOOTSTRAP:
        typer.echo(f"  {chdir} plan")
        return
    # The phase file sets bootstrap_user, so no command passes -var.
    typer.echo(f"  {chdir} plan -out={_STAGE0_PLAN}")
    typer.echo(f"  {chdir} apply {_STAGE0_PLAN}")
    if answers.stage0_phase == models.STAGE0_BOOTSTRAP:
        typer.echo(
            "After this first apply and the state migration, run stellar "
            f"init --set stage0_phase={models.STAGE0_FINAL} and stellar "
            "render, then run the same commands for the final apply."
        )


@dataclasses.dataclass(frozen=True)
class _WriteOptions:
    """How `render` treats files that hold manual edits."""

    force: bool
    interactive: bool
    now: datetime.datetime


def _selected_stages(names):
    """Returns the canonical stages to render in deployment order."""
    try:
        selected = {paths.resolve_stage(name) for name in names or []}
    except ValueError as error:
        _fail(str(error))
    return [stage for stage in paths.STAGES if stage in selected] or list(
        paths.STAGES
    )


def _render_stage(name, answers, session, env, local_tools, options):
    """Syncs one workspace and writes its tfvars, imports and phase file.

    Returns:
        The sync report, summary rows, and False when an edited tfvars file
        was left in place.
    """
    try:
        sync = workspace_lib.sync(env, session.repo.root, name)
    except workspace_lib.WorkspaceError as error:
        _fail(str(error))
    for conflict in sync.conflicts:
        _warn(
            f"{sync.path / conflict} is a real file that shadows the "
            "engine's file of the same name."
        )
    if name == paths.BOOTSTRAP:
        # Refuse a foreign phase file before any write, so a refused render
        # leaves the tfvars and imports files as they were.
        _planned_phase(sync.path, answers, session.repo)
    text = _render_text(name, answers, session, env, local_tools)
    target = sync.path / _TFVARS
    ok = True
    try:
        result = writer.write(
            target,
            text,
            env.generated_hash(name),
            force=options.force,
            interactive=options.interactive,
            confirm=_confirm_replace(target),
            now=options.now,
        )
    except writer.OverwriteRefusedError as error:
        _error(error)
        ok = False
        rows = [(name, target, "refused", None)]
    else:
        rows = [(name, target, result.outcome.value, result.backup)]
    imports_target, imports_outcome = _write_imports(sync.path, name, answers)
    if imports_outcome is not None:
        rows.append((name, imports_target, imports_outcome.value, None))
    if name == paths.BOOTSTRAP:
        phase_outcome = _write_phase(sync.path, answers, session.repo)
        if phase_outcome is not None:
            rows.append(
                (
                    name,
                    sync.path / phase_lib.FILENAME,
                    phase_outcome.value,
                    None,
                )
            )
    return sync, rows, ok


@app.command()
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
        typer.Option(
            "--non-interactive",
            help="Never prompt; refuse to replace manually edited files.",
        ),
    ] = False,
    prefix: PrefixOption = None,
    home: HomeOption = None,
    repo: RepoOption = None,
):
    """Render the stage workspaces, tfvars, import blocks and phase file.

    Each workspace links the engine's stage code and holds the files the
    environment owns, so Terraform runs from it with `-chdir`.
    """
    session = _session(home, repo)
    env = _env(session.home, prefix)
    answers = _load_answers(env, session.repo)
    selected = _selected_stages(stage)
    if answers.engine and answers.engine.path != str(session.repo.root):
        _warn(
            f"answers.yaml records the engine {answers.engine.path}, but "
            f"this render uses {session.repo.root}."
        )
    _render_warnings(selected, answers, session, env)
    local_tools = tools_lib.SystemTools()
    if show_diff:
        _render_diff(selected, answers, session, env, local_tools)
        return
    options = _WriteOptions(
        force=force,
        interactive=_interactive(non_interactive),
        now=datetime.datetime.now(datetime.UTC),
    )
    rows = []
    reports = {}
    refused = []
    for name in selected:
        sync, stage_rows, ok = _render_stage(
            name, answers, session, env, local_tools, options
        )
        reports[name] = sync
        rows.extend(stage_rows)
        if not ok:
            refused.append(name)
    typer.echo(f"Rendered {env.prefix} in {env.root}:")
    for name, target, outcome, backup in rows:
        line = f"  {name:<11}  {outcome:<9}  {target}"
        if backup is not None:
            line += f"  backup {backup}"
        typer.echo(line)
    if refused:
        raise typer.Exit(_EXIT_OVERWRITE_REFUSED)
    for name in selected:
        _print_next_steps(name, env.workspace(name), answers, reports)


def _render_warnings(selected, answers, session, env):
    """Prints the non-fatal findings about the selected stages."""
    for name in selected:
        found = [
            *imports_lib.warnings(answers, name, session.repo),
            *stages_lib.warnings(answers, name, session.repo),
        ]
        if name == paths.BOOTSTRAP:
            found += phase_lib.warnings(env.workspace(name), answers)
        for line in found:
            _warn(line)


def _render_diff(selected, answers, session, env, local_tools):
    """Prints what a render would change, writing nothing."""
    changed = False
    for name in selected:
        workspace = env.workspace(name)
        text = _render_text(name, answers, session, env, local_tools)
        try:
            imports_text = imports_lib.text(answers, name)
        except imports_lib.ImportBlockError as error:
            _fail(str(error))
        imports_target = workspace / imports_lib.filename(name)
        targets = [
            (workspace / _TFVARS, text),
            (imports_target, imports_text),
        ]
        if name == paths.BOOTSTRAP:
            phase_text = _planned_phase(workspace, answers, session.repo)
            targets.append((workspace / phase_lib.FILENAME, phase_text))
        for target, content in targets:
            if not content and fsutil.read_text_or_none(target) is None:
                continue
            changes = writer.diff(target, content)
            if changes:
                changed = True
                typer.echo(changes, nl=not changes.endswith("\n"))
    if not changed:
        typer.echo("No changes.")


def _parse_groups(values):
    groups = {}
    for value in values or []:
        key, sep, name = value.partition("=")
        if not sep or not key or not name:
            raise typer.BadParameter(
                f"Expected KEY=NAME, got {value!r}.", param_hint="--group"
            )
        groups[key] = name
    return groups


def _preflight_answers(session, prefix):
    """Returns the selected environment's answers, or None without one.

    Preflight works from flags alone, so a missing environment is not an
    error; an environment with broken answers is.
    """
    home_obj = session.home
    selected = prefix or home_obj.current()
    if not selected:
        return None
    try:
        env = home_obj.env(selected)
    except ValueError:
        return None
    if not env.answers.is_file():
        return None
    typer.echo(f"Reading answers from {env.answers}.", err=True)
    return _load_answers(env, session.repo)


@app.command()
def preflight(
    org: Annotated[
        str | None,
        typer.Option(envvar="STELLAR_ORG_ID", help="Organization ID."),
    ] = None,
    billing_account: Annotated[
        str | None,
        typer.Option(
            envvar="STELLAR_BILLING_ACCOUNT", help="Billing account ID."
        ),
    ] = None,
    billing_no_iam: Annotated[
        bool,
        typer.Option(
            "--billing-no-iam",
            envvar="STELLAR_BILLING_NO_IAM",
            help=(
                "Match a Stage 0 billing_account.no_iam of true: require "
                "only the permission to link projects to the billing account."
            ),
        ),
    ] = False,
    project: Annotated[
        str | None,
        typer.Option(
            envvar="STELLAR_BOOTSTRAP_PROJECT", help="Bootstrap project ID."
        ),
    ] = None,
    prefix: Annotated[
        str | None,
        typer.Option(
            envvar="STELLAR_PREFIX",
            help=(
                "Resource name prefix. Also selects the environment whose "
                "answers fill unset values."
            ),
        ),
    ] = None,
    regime: Annotated[
        str | None,
        typer.Option(
            envvar="STELLAR_REGIME",
            help="Compliance regime, for example IL5 or FEDRAMP_HIGH.",
        ),
    ] = None,
    region: Annotated[
        str | None,
        typer.Option(envvar="STELLAR_REGION", help="Primary region."),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option(envvar="STELLAR_DOMAIN", help="Organization domain."),
    ] = None,
    customer_id: Annotated[
        str | None,
        typer.Option(
            envvar="STELLAR_CUSTOMER_ID", help="Directory customer ID."
        ),
    ] = None,
    bootstrap_user: Annotated[
        str | None,
        typer.Option(
            envvar="STELLAR_BOOTSTRAP_USER",
            help=(
                "User account email for the first Stage 0 apply's "
                "bootstrap_user. Defaults to the signed-in user."
            ),
        ),
    ] = None,
    group: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "Override a Stage 0 group as KEY=NAME, for example "
                "gcp-devops=platform-devops. Repeatable."
            ),
        ),
    ] = None,
    config_env: Annotated[
        pathlib.Path | None,
        typer.Option(
            help="Read unset values from a scripts/config.env file.",
            exists=True,
            dir_okay=False,
        ),
    ] = None,
    redeploy: Annotated[
        bool,
        typer.Option(
            "--redeploy",
            help="Report resources that already use the prefix as WARN.",
        ),
    ] = False,
    output_json: Annotated[
        bool, typer.Option("--json", help="Print results as JSON.")
    ] = False,
    strict: Annotated[
        bool, typer.Option("--strict", help="Exit non-zero on warnings too.")
    ] = False,
    home: HomeOption = None,
    repo: RepoOption = None,
):
    """Check the deployment prerequisites from docs/ddg.md.

    Preflight only reads. It validates local tools, the signed-in identity,
    organization roles, billing, the bootstrap project, administrative groups,
    the prefix and region, and risks in a shared organization. Values come
    from flags, then the environment's answers.yaml, then --config-env.
    """
    flags = {
        "org_id": org,
        "billing_account": billing_account,
        "billing_no_iam": billing_no_iam,
        "bootstrap_project": project,
        "prefix": prefix,
        "regime": regime,
        "region": region,
        "domain": domain,
        "customer_id": customer_id,
        "groups": _parse_groups(group),
        "bootstrap_user": bootstrap_user,
        "redeploy": redeploy,
    }
    err_console = rich_console.Console(stderr=True)
    session = _session(home, repo)
    answers = _preflight_answers(session, prefix)
    try:
        resolved = inputs_lib.resolve(
            flags,
            config_env,
            None if answers is None else answers_lib.to_preflight(answers),
        )
        inputs_lib.validate_against_repo(resolved, session.repo)
    except (pydantic.ValidationError, repo_lib.RepoError, ValueError) as error:
        _fail(str(error))
    ctx = checks.Context(
        inputs=resolved,
        cloud=live.LiveCloudApi(),
        tools=tools_lib.SystemTools(),
        repo=session.repo,
        environ=os.environ,
    )
    if output_json:
        results = runner.run(ctx)
        typer.echo(report.render_json(results, resolved))
    else:
        with err_console.status("Running preflight checks..."):
            results = runner.run(ctx)
        report.render_table(rich_console.Console(), results)
    raise typer.Exit(runner.exit_code(results, strict=strict))
