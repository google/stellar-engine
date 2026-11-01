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

"""The `stellar env` commands, which list, select and show environments."""

from typing import Annotated

from rich import table as rich_table
import typer

from stellar_engine import paths
from stellar_engine.commands import common
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import derive


def env_list(home: common.HomeOption = None, repo: common.RepoOption = None):
    """List the environments of the home."""
    session = common.session(home, repo)
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
    common.console().print(table)
    typer.echo(f"Home: {home_obj.root}")
    stale = home_obj.stale_current_message()
    if stale is not None:
        common.warn(stale)


def env_use(
    prefix: Annotated[str, typer.Argument(help="Environment prefix.")],
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Make an environment the current one."""
    home_obj = common.session(home, repo).home
    if prefix not in home_obj.list_envs():
        common.fail(f"No environment {prefix} in {home_obj.root}.")
    home_obj.set_current(prefix)
    typer.echo(f"Current environment: {prefix}.")


def env_show(
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Show where an environment lives and the values derived from it."""
    session = common.session(home, repo)
    home_obj = session.home
    source = common.HOME_SOURCES[session.resolved.source]
    # The home prints before the environment is selected, so a missing
    # environment still shows which home was searched.
    typer.echo(f"Home: {home_obj.root} ({source})")
    env = common.env(home_obj, prefix)
    answers = common.load_answers(env, session.repo)
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
    _print_derived(answers, session.repo)
    _print_imports(answers)


def _print_derived(answers, repository):
    """Prints the values that stellar derives from the answers."""
    typer.echo("Derived values:")
    typer.echo(
        f"  KMS protection level: {derive.kms_protection_level(answers)}"
    )
    typer.echo(
        f"  Assured Workloads location: {derive.compliance_location(answers)}"
    )
    typer.echo("  Stage 0 project IDs and deletion policies:")
    policies = derive.stage0_deletion_policies(answers, repository)
    for project_id, policy in policies.items():
        typer.echo(f"    {project_id}  {policy}")
    for tenant, project_ids in derive.tenant_project_ids(answers).items():
        typer.echo(f"  Tenant {tenant} project IDs:")
        for project_id in project_ids:
            typer.echo(f"    {project_id}")


def _print_imports(answers):
    """Prints the import IDs and the organization policies to import."""
    for stage, entries in answers.imports.items():
        typer.echo(f"Imports for {stage}:")
        for address, import_id in sorted(entries.items()):
            typer.echo(f"  {address} = {import_id}")
    if answers.existing_org_policies:
        typer.echo("Existing organization policies that Stage 0 imports:")
        for name in answers.existing_org_policies:
            typer.echo(f"  {name}")
