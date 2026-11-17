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

"""Tests for the plan summary that the deploy prints before an apply."""

import io

from rich import console as rich_console

import helpers
from stellar_engine.terraform import guards
from stellar_engine.terraform import plan as plan_lib
from stellar_engine.terraform import summary as summary_lib

BUCKET = (
    'module.log-export-logbucket["audit-logs"]'
    ".google_logging_project_bucket_config.bucket[0]"
)


def _plan(name):
    return plan_lib.parse(helpers.plan_fixture(name))


def _render(plan, findings=(), **kwargs):
    buffer = io.StringIO()
    console = rich_console.Console(file=buffer, width=300)
    summary_lib.render(console, plan, findings, **kwargs)
    return buffer.getvalue()


def test_render_lists_changes_to_review():
    plan = _plan("stage0-bootstrap-first")
    text = _render(plan)
    assert "Plan summary" in text
    assert "module.automation-project.google_project.project[0]" in text
    assert "import abc-prod-iac-core-0" in text
    # Plain creates are only counted.
    assert "google_assured_workloads_workload.primary[0]" not in text
    assert "Plan checks" not in text


def test_render_orders_destructive_changes_first():
    text = _render(_plan("stage0-bootstrap-after-final"), limit=3)
    assert "delete_because_each_key" in text
    assert "and 12 more" in text
    assert BUCKET not in text


def test_render_lists_imports_without_changes():
    text = _render(_plan("stage0-final-imports"))
    assert 'default["compute.restrictVpcPeering"]' in text
    assert "no-op" in text


def test_render_without_changes():
    text = _render(_plan("stage0-no-changes"))
    assert "changes nothing" in text
    assert "Changes to review" not in text
    assert "outside Terraform" not in text


def test_render_counts_material_drift():
    text = _render(_plan("stage0-org-policy-drift"))
    assert "11 resources changed outside Terraform" in text


def test_render_prints_findings():
    finding = guards.Finding(
        guards.Level.BLOCK,
        guards.PROTECTED_DELETE,
        "google_folder.x",
        "Stage 0 would delete a google_folder.",
    )
    text = _render(_plan("stage0-no-changes"), [finding])
    assert "Plan checks" in text
    assert "BLOCK" in text
    assert "protected_delete" in text
    assert "google_folder.x" in text
