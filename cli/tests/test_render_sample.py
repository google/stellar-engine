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

"""Tests for the tfvars sample reader.

The stage 0 and stage 1 tests read the real samples, so they also fail when
a sample changes in a way the renderer must follow.
"""

import hcl2

import conftest
from stellar_engine import paths
from stellar_engine.render import sample


def _sample_path(stage):
    return (
        paths.stage_dir(conftest.REPO_ROOT, stage) / "terraform.tfvars.sample"
    )


def _load(stage):
    return sample.load(_sample_path(stage))


def test_bootstrap_order_includes_commented_keys():
    parsed = _load("0-bootstrap")
    assert parsed.order == [
        "billing_account",
        "billing_budget_amount",
        "regions",
        "organization",
        "outputs_location",
        "logging_bucket_retention",
        "prefix",
        "log_sinks",
        "org_policies_config",
        "fast_features",
        "assured_workloads",
        "bootstrap_project",
        "alert_email",
        "kms_protection_level",
    ]
    commented = {"billing_budget_amount", "logging_bucket_retention"}
    commented.add("kms_protection_level")
    assert set(parsed.order) - set(parsed.values) == commented
    assert set(parsed.comments) == set(parsed.order)


def test_bootstrap_comment_blocks():
    comments = _load("0-bootstrap").comments
    assert comments["billing_account"] == [
        "# use `gcloud billing accounts list`"
    ]
    assert comments["billing_budget_amount"] == [
        "# Optional Billing budget for the Assured Workload folder. If not "
        "set, no budget will be created."
    ]
    # The commented-out `amount = 1000` and `}` body lines belong to
    # billing_budget_amount, not to the regions block below them.
    assert comments["regions"][0].startswith("# region configuration")
    assert len(comments["regions"]) == 2
    assert comments["logging_bucket_retention"] == [
        "# Retention period (in days) for organization logging buckets "
        "(defaults to 365 days for compliance)"
    ]
    assert len(comments["prefix"]) == 2
    assert len(comments["log_sinks"]) == 4
    assert comments["log_sinks"][1] == (
        "# logging_bucket_retention days; the default is 365)"
    )
    assert comments["assured_workloads"] == ["# Regime must be in all caps"]
    assert len(comments["kms_protection_level"]) == 3
    assert comments["kms_protection_level"][0].startswith("# KMS protection")
    for key in ("outputs_location", "fast_features", "bootstrap_project"):
        assert comments[key] == []
    for block in comments.values():
        assert all(line.startswith("#") for line in block)
        assert not any("= {" in line or line == "# }" for line in block)


def test_bootstrap_values_are_plain():
    values = _load("0-bootstrap").values
    assert values["prefix"] == "<prefix>"
    assert values["billing_account"] == {"id": "<billing_account_id>"}
    assert values["org_policies_config"]["import_defaults"] is False
    assert values["fast_features"] == {"envs": True}
    sinks = values["log_sinks"]
    assert list(sinks) == [
        "audit-logs",
        "vpc-sc",
        "workspace-audit-logs",
        "empty-audit-logs",
    ]
    assert sinks["vpc-sc"]["filter"] == (
        'protoPayload.metadata.@type="type.googleapis.com/google.cloud.audit.'
        'VpcServiceControlAuditMetadata"'
    )
    assert sinks["empty-audit-logs"] == {"filter": "", "type": "logging"}
    assert "__comments__" not in values


def test_resman_sample():
    parsed = _load("1-resman")
    assert parsed.order == ["tenants", "fast_features", "envs_folders"]
    assert set(parsed.values) == set(parsed.order)
    assert parsed.comments == {key: [] for key in parsed.order}
    tenant = parsed.values["tenants"]["ten-1"]
    assert tenant["admin_principal"] == "group:gcp-devops@<domain>"
    assert tenant["locations"] == {"gcs": "<region>", "kms": "<region>"}
    assert list(parsed.values["envs_folders"]) == ["Prod", "Int", "Test"]


def test_values_match_python_hcl2_keys():
    for stage in paths.STAGES:
        path = _sample_path(stage)
        with path.open(encoding="utf-8") as handle:
            raw = hcl2.load(handle)
        raw.pop("__comments__", None)
        raw.pop("__inline_comments__", None)
        assert list(_load(stage).values) == list(raw)


def test_parse_ignores_nested_and_string_content():
    parsed = sample.parse(
        "# About a.\n"
        "a = {\n"
        "  # nested = 1\n"
        '  b = "{ text = 1"\n'
        "  c = 2 # } brace in a comment\n"
        "}\n"
        "/* block\n"
        "z = 1\n"
        "*/\n"
        "\n"
        "# Unrelated note.\n"
        "\n"
        "// About d.\n"
        "d = [\n"
        "  1,\n"
        "]\n"
    )
    assert parsed.order == ["a", "d"]
    assert parsed.comments == {"a": ["# About a."], "d": ["// About d."]}
    assert parsed.values == {"a": {"b": "{ text = 1", "c": 2}, "d": [1]}


def test_parse_commented_out_blocks():
    parsed = sample.parse(
        "# First option.\n"
        "# first = {\n"
        "#   nested = {\n"
        "#     x = 1\n"
        "#   }\n"
        "# }\n"
        "# Second option.\n"
        '# second = "x"\n'
        "# Third note.\n"
        "third = 3\n"
        "# Prose mentions first and second values.\n"
        "fourth = 4\n"
    )
    assert parsed.order == ["first", "second", "third", "fourth"]
    assert parsed.comments == {
        "first": ["# First option."],
        "second": ["# Second option."],
        "third": ["# Third note."],
        "fourth": ["# Prose mentions first and second values."],
    }
    assert parsed.values == {"third": 3, "fourth": 4}


def test_parse_keeps_first_position_of_duplicate_key():
    parsed = sample.parse('# a = "commented"\na = "real"\n')
    assert parsed.order == ["a"]
    assert parsed.values == {"a": "real"}
