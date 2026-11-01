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

"""The `stellar imports` commands, which find resources Stage 0 imports."""

from rich import table as rich_table
import typer

from stellar_engine import org_policies
from stellar_engine.commands import common
from stellar_engine.config import answers as answers_lib
from stellar_engine.gcp import api
from stellar_engine.gcp import live

_SCAN_RESULTS = {
    "kept": "import on the final Stage 0 apply",
    "custom": "skip, Stage 0 creates the custom constraint",
    "undeclared": "skip, Stage 0 does not set it for this regime",
}


def imports_scan(
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Record the existing organization policies that Stage 0 imports.

    The command lists the policies on the organization, keeps those that
    Stage 0 declares, and saves them to existing_org_policies in
    answers.yaml, so stellar render writes their import block. It only
    reads from Google Cloud.
    """
    session = common.session(home, repo)
    # The scan replaces existing_org_policies, so a stale list must not
    # stop it; `org_policies.record` validates the updated answers before
    # the save.
    env, answers = common.load_env(session, prefix, check_repo=False)
    org_id = answers.organization.id
    try:
        scanned = org_policies.scan(answers, session.repo, live.LiveCloudApi())
    except (api.CloudError, api.CredentialsError) as error:
        common.fail(
            f"Cannot list the policies of organization {org_id}: {error}",
            common.EXIT_CLOUD,
        )
    _print_scan(org_id, scanned)
    with common.ExitOn(answers_lib.AnswersError):
        changed = org_policies.record(
            env, scanned, session.repo, session.home.root
        )
    if changed:
        typer.echo(
            f"Saved {len(scanned.kept)} organization policies to "
            f"existing_org_policies in {env.answers}."
        )
    else:
        typer.echo(f"{env.answers} already lists these policies.")
    typer.echo("Next: stellar render")


def _print_scan(org_id, scan):
    """Prints what happens to each existing policy of the organization."""
    # The scan sorts every existing policy into exactly one of its lists.
    if not (scan.kept or scan.custom or scan.undeclared):
        typer.echo(f"Organization {org_id} has no organization policies.")
        return
    table = rich_table.Table("Constraint", "Result")
    for field, result in _SCAN_RESULTS.items():
        for name in getattr(scan, field):
            table.add_row(name, result)
    common.console().print(table)
