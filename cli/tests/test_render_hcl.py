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

"""Tests for the HCL emitter."""

import subprocess

import hcl2
import pytest

import conftest
from stellar_engine import paths
from stellar_engine.render import hcl
from stellar_engine.render import sample

SAMPLES = [
    paths.stage_dir(conftest.REPO_ROOT, stage) / "terraform.tfvars.sample"
    for stage in paths.STAGES
]

CASES = {
    "scalars": {
        "text": "plain",
        "empty": "",
        "count": 3,
        "negative": -42,
        "ratio": 0.25,
        "enabled": True,
        "disabled": False,
        "nothing": None,
    },
    "escapes": {
        "value": 'quote " back \\ tab \t newline \n return \r end',
        "templates": "${var.x} %{if true}y%{endif} $${already} %%{also}",
        "control": "bell \x07 delete \x7f",
        "unicode": "café “n”",
        "dollar": "$5 and 100%",
    },
    "nested": {
        "billing_account": {"id": conftest.BILLING, "no_iam": True},
        "org_policies_config": {
            "import_defaults": False,
            "constraints": {
                "allowed_policy_member_domains": [
                    "C01234567",
                    "is:C01234568",
                    "is:principalSet://iam.googleapis.com/organizations/"
                    + conftest.ORG_ID,
                ],
            },
        },
        "tenants": {
            "ten1": {
                "admin_principal": "group:gcp-devops@example.com",
                "descriptive_name": "tenant-1",
                "locations": {"gcs": "us-east4", "kms": "us-east4"},
            },
            "ten-2": {"descriptive_name": "tenant-2", "locations": {}},
        },
    },
    "keys": {
        "iam": {
            "roles/owner": ["user:admin@example.com"],
            "roles/billing.admin": [],
            "plain_key": "x",
            "dash-key": "y",
            "1starts_with_digit": "z",
            "for": "keyword",
            "null": "keyword",
            "with space": 'a "quoted" key',
        },
    },
    "lists": {
        "empty_list": [],
        "empty_map": {},
        "short": ["a", "b", 1, True, None],
        "long": [
            f"serviceAccount:sa-{n}@example.iam.gserviceaccount.com"
            for n in range(3)
        ],
        "maps": [{"name": "a", "value": 1}, {"name": "bb"}, {}],
        "nested_lists": [[1, 2], [], ["x"]],
        "mixed": ["s", {"k": "v"}, [1]],
    },
    "alignment": {
        "outer": {
            "a": 1,
            "long_name": "v",
            "block": {"x": 1},
            "b": 2,
            "longer_name": [],
            "list": ["much longer value " * 5],
            "c": 3,
        },
    },
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_round_trip(case):
    values = CASES[case]
    assert hcl.loads(hcl.dumps(values)) == values


def test_round_trip_log_sink_filters(repo):
    parsed = sample.load(repo.bootstrap_dir / "terraform.tfvars.sample")
    sinks = parsed.values["log_sinks"]
    assert (
        '"/logs/cloudaudit.googleapis.com%2Factivity"'
        in (sinks["audit-logs"]["filter"])
    )
    assert hcl.loads(hcl.dumps({"log_sinks": sinks})) == {"log_sinks": sinks}


def test_quote_escapes():
    assert hcl.quote('a"b\\c') == r'"a\"b\\c"'
    assert hcl.quote("${x}") == '"$${x}"'
    assert hcl.quote("%{x}") == '"%%{x}"'
    assert hcl.quote("line\nnext\ttab") == r'"line\nnext\ttab"'
    assert hcl.quote("\x01") == r'"\u0001"'
    assert hcl.quote("$x %x") == '"$x %x"'


def test_unquote_leaves_non_literals():
    assert hcl.unquote(3) == 3
    assert hcl.unquote("${var.x}") == "${var.x}"
    assert hcl.unquote('"$${x} %%{y}"') == "${x} %{y}"


def test_normalize_strips_comment_metadata():
    raw = hcl2.loads('# top\nx = { a = 1 # inline\n}\ny = ["s"] # tail\n')
    assert hcl.normalize(raw) == {"x": {"a": 1}, "y": ["s"]}


def test_key_quoting():
    text = hcl.dumps(CASES["keys"])
    assert '  "roles/owner"' in text
    assert "  plain_key " in text
    assert "  dash-key " in text
    assert '  "1starts_with_digit" ' in text
    assert '  "for" ' in text
    assert '  "with space" ' in text


def test_layout():
    text = hcl.dumps(
        {"first": {"a": 1, "bbb": "x"}, "second": ["a", "b"]},
        comments={"second": ["# About second.", "#   indented  "], "gone": []},
        header=["# Generated.", "# Edit answers."],
    )
    assert text == (
        "# Generated.\n"
        "# Edit answers.\n"
        "\n"
        "first = {\n"
        "  a   = 1\n"
        '  bbb = "x"\n'
        "}\n"
        "\n"
        "# About second.\n"
        "#   indented\n"
        'second = ["a", "b"]\n'
    )


def test_alignment_runs_break_at_multiline_values():
    text = hcl.dumps(CASES["alignment"])
    assert text == (
        "outer = {\n"
        "  a         = 1\n"
        '  long_name = "v"\n'
        "  block = {\n"
        "    x = 1\n"
        "  }\n"
        "  b           = 2\n"
        "  longer_name = []\n"
        "  list = [\n"
        f'    "{"much longer value " * 5}",\n'
        "  ]\n"
        "  c = 3\n"
        "}\n"
    )


def test_list_of_maps_layout():
    text = hcl.dumps({"x": [{"a": 1}, {}]})
    assert text == "x = [\n  {\n    a = 1\n  },\n  {},\n]\n"


def test_empty_values():
    assert hcl.dumps({}) == ""
    assert hcl.dumps({}, header=["# Only a header."]) == "# Only a header.\n"


@pytest.mark.parametrize(
    "values",
    [
        {"not-valid!": 1},
        {"1abc": 1},
        {"x": float("nan")},
        {"x": float("inf")},
    ],
)
def test_rejects_invalid_values(values):
    with pytest.raises(ValueError):
        hcl.dumps(values)


@pytest.mark.parametrize("value", [object(), b"bytes", {1: "int key"}])
def test_rejects_unsupported_types(value):
    with pytest.raises(TypeError):
        hcl.dumps({"x": value})


def test_rejects_non_comment_lines():
    with pytest.raises(ValueError, match="not a comment"):
        hcl.dumps({"x": 1}, comments={"x": ["no hash"]})
    with pytest.raises(ValueError, match="not a comment"):
        hcl.dumps({"x": 1}, header=["# two\nlines"])


def _fmt_check(text, tmp_path):
    """Runs `terraform fmt -check` on text; returns (rc, formatted)."""
    path = tmp_path / "check.tfvars"
    path.write_text(text, encoding="utf-8")
    check = subprocess.run(
        ["terraform", "fmt", "-check", "-diff", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return check.returncode, check.stdout + check.stderr


@pytest.mark.terraform
@pytest.mark.parametrize("case", sorted(CASES))
def test_output_is_terraform_fmt_canonical(case, tmp_path):
    text = hcl.dumps(
        CASES[case],
        comments={key: [f"# About {key}."] for key in CASES[case]},
        header=["# Generated for a test."],
    )
    returncode, output = _fmt_check(text, tmp_path)
    assert returncode == 0, output


@pytest.mark.terraform
@pytest.mark.parametrize("path", SAMPLES, ids=lambda path: path.parent.name)
def test_samples_reemit_canonical(path, tmp_path):
    parsed = sample.load(path)
    values = {
        key: parsed.values[key] for key in parsed.order if key in parsed.values
    }
    text = hcl.dumps(values, comments=parsed.comments, header=["# Test."])
    returncode, output = _fmt_check(text, tmp_path)
    assert returncode == 0, output
    assert hcl.loads(text) == parsed.values
