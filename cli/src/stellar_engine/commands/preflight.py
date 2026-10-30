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

"""The `stellar preflight` command, which checks the prerequisites."""

import os
import pathlib
from typing import Annotated

import pydantic
import typer

from stellar_engine import repo as repo_lib
from stellar_engine import tools as tools_lib
from stellar_engine.commands import common
from stellar_engine.config import answers as answers_lib
from stellar_engine.gcp import live
from stellar_engine.preflight import checks
from stellar_engine.preflight import inputs as inputs_lib
from stellar_engine.preflight import report
from stellar_engine.preflight import runner


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
    # This --prefix also names the resources to check, so its help differs
    # from the shared PrefixOption.
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
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
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
    err_console = common.console(stderr=True)
    session = common.session(home, repo)
    answers = _preflight_answers(session, prefix)
    with common.ExitOn(
        pydantic.ValidationError, repo_lib.RepoError, ValueError
    ):
        resolved = inputs_lib.resolve(
            flags,
            config_env,
            None if answers is None else answers_lib.to_preflight(answers),
        )
        inputs_lib.validate_against_repo(resolved, session.repo)
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
        report.render_table(common.console(), results)
    raise typer.Exit(runner.exit_code(results, strict=strict))


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
    return common.load_answers(env, session.repo)
