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

from typing import Annotated

import typer

import stellar_engine
from stellar_engine.commands import env as env_cmd
from stellar_engine.commands import imports as imports_cmd
from stellar_engine.commands import init as init_cmd
from stellar_engine.commands import preflight as preflight_cmd
from stellar_engine.commands import render as render_cmd

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


# The registration order is the order of `stellar --help`.
app.command()(init_cmd.init)
env_app.command("list")(env_cmd.env_list)
env_app.command("use")(env_cmd.env_use)
env_app.command("show")(env_cmd.env_show)
imports_app.command("scan")(imports_cmd.imports_scan)
app.command()(render_cmd.render)
app.command()(preflight_cmd.preflight)
