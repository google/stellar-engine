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

"""Tests for the `stellar guide` command."""

import pytest
from rich import console as rich_console

import helpers
from stellar_engine.commands import common
from stellar_engine.deploy import catalog
from stellar_engine.gcp import live

pytestmark = pytest.mark.usefixtures("isolated_home")


@pytest.fixture
def offline(monkeypatch, fake_tools):
    """Prints on one line per paragraph and fails on any cloud client."""
    del fake_tools  # Only its patch matters.
    monkeypatch.setattr(
        common,
        "console",
        lambda stderr=False: rich_console.Console(
            width=10_000, color_system=None
        ),
    )

    def no_cloud():
        raise AssertionError("stellar guide must not build a cloud client")

    monkeypatch.setattr(live, "LiveCloudApi", no_cloud)


def _guide(cli_runner, home, *args):
    outcome = helpers.invoke(cli_runner, "guide", *args)
    return outcome, outcome.output.replace(str(home), "$STELLAR_HOME")


def test_guide_snapshot(cli_runner, isolated_home, offline, snapshot):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome, text = _guide(cli_runner, isolated_home)
    assert outcome.exit_code == 0, outcome.output
    assert text == snapshot


def test_guide_lists_every_step_once(cli_runner, isolated_home, offline):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome, text = _guide(cli_runner, isolated_home)
    assert outcome.exit_code == 0, outcome.output
    for step in catalog.catalog():
        assert text.count(f". {step.id}  {step.kind}  {step.title}") == 1
    assert text.rstrip().endswith("Next: stellar deploy")


def test_guide_one_stage(cli_runner, isolated_home, offline):
    assert helpers.init_env(cli_runner).exit_code == 0
    outcome, text = _guide(cli_runner, isolated_home, "--stage", "0")
    assert outcome.exit_code == 0, outcome.output
    assert "Stage 0 - Bootstrap" in text
    assert "pre.apis" not in text
    assert "s1.apply" not in text
    assert text.rstrip().endswith("Next: stellar deploy --stage 0")


def test_guide_one_step_and_its_condition(cli_runner, isolated_home, offline):
    assert (
        helpers.init_env(
            cli_runner,
            sets=("compliance.regime=COMPLIANCE_REGIME_UNSPECIFIED",),
        ).exit_code
        == 0
    )
    outcome, text = _guide(cli_runner, isolated_home, "--only", "s0.allow_bq")
    assert outcome.exit_code == 0, outcome.output
    assert " 1. s0.allow_bq  auto  Allow BigQuery" in text
    assert "Not applicable here: it applies only when the regime" in text
    assert text.rstrip().endswith("Next: stellar deploy --only s0.allow_bq")


def test_guide_writes_nothing(cli_runner, isolated_home, offline):
    assert helpers.init_env(cli_runner).exit_code == 0
    before = sorted(isolated_home.rglob("*"))
    outcome, _ = _guide(cli_runner, isolated_home)
    assert outcome.exit_code == 0, outcome.output
    assert sorted(isolated_home.rglob("*")) == before


def test_guide_rejects_an_unknown_stage_or_step(
    cli_runner, isolated_home, offline
):
    assert helpers.init_env(cli_runner).exit_code == 0
    assert helpers.invoke(cli_runner, "guide", "--stage", "9").exit_code == 2
    outcome = helpers.invoke(cli_runner, "guide", "--only", "s9.nothing")
    assert outcome.exit_code == 2
    assert "Unknown step s9.nothing" in outcome.output


def test_guide_needs_an_environment(cli_runner, offline):
    outcome = helpers.invoke(cli_runner, "guide")
    assert outcome.exit_code == 2
