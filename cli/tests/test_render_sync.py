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

"""Checks that the renderer stays in sync with the stage code.

Each test reads the stage files directly with python-hcl2 or a regular
expression, independently of the code under test, so a change to a
variable, a validation block or a sample fails here first.
"""

import json
import re

import hcl2
import pytest

import conftest
import helpers
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace
from stellar_engine.config import models
from stellar_engine.config import validate
from stellar_engine.render import imports
from stellar_engine.render import sample as sample_lib
from stellar_engine.render import stages


def _declared(repo, stage):
    path = paths.stage_dir(repo.root, stage) / "variables.tf"
    parsed = hcl2.loads(path.read_text(encoding="utf-8"))
    return {
        json.loads(name) if name.startswith('"') else name
        for block in parsed["variable"]
        for name in block
    }


@pytest.mark.parametrize("stage", paths.STAGES)
@pytest.mark.parametrize("name", helpers.ALL_FIXTURES)
def test_written_keys_are_declared_variables(name, stage, repo):
    assert set(helpers.render(repo, name, stage).values) <= _declared(
        repo, stage
    )


def test_variable_names_match_hcl(repo):
    for stage in paths.STAGES:
        assert repo.stage_variable_names(stage) == _declared(repo, stage)


@pytest.mark.parametrize("name", helpers.ALL_FIXTURES)
def test_auto_keys_are_never_written(name, repo):
    written = set(helpers.render(repo, name, "1-resman").values)
    assert not written & repo.auto_tfvars_keys("1-resman")


def test_auto_keys_match_stage_outputs(repo):
    # The stage 1 harness fixtures model the files Stage 0 writes, so their
    # keys must be exactly the keys the renderer treats as auto-provided.
    fixture_keys = set()
    for path in helpers.STAGE_OUTPUTS_DIR.glob("*.auto.tfvars.json"):
        fixture_keys |= set(json.loads(path.read_text(encoding="utf-8")))
    assert fixture_keys == repo.auto_tfvars_keys("1-resman")


def test_auto_keys_come_from_output_files(repo):
    # Stage 0 writes exactly these two locals to the files stage 1 links.
    text = (repo.bootstrap_dir / "outputs-files.tf").read_text(encoding="utf-8")
    pairs = re.findall(
        r'tfvars/([\w.-]+)"\n\s+content\s+=\s+jsonencode\(local\.(\w+)\)', text
    )
    assert dict(pairs) == {
        "0-bootstrap.auto.tfvars.json": "tfvars",
        "0-globals.auto.tfvars.json": "tfvars_globals",
    }


def test_auto_keys_bootstrap_and_unknown_stage(repo):
    assert repo.auto_tfvars_keys("0-bootstrap") == frozenset()
    with pytest.raises(repo_lib.RepoError, match="Unknown stage"):
        repo.auto_tfvars_keys("2-networking")


@pytest.mark.parametrize(
    "key",
    sorted(repo_lib.Repo(conftest.REPO_ROOT).auto_tfvars_keys("1-resman")),
)
def test_override_of_any_auto_key_is_rejected(key, repo):
    answers = helpers.load_fixture(
        "fedramp_high", overrides={"1-resman": {key: 1}}
    )
    with pytest.raises(stages.RenderError, match=key):
        stages.build("1-resman", answers, repo, helpers.env_paths(answers))


@pytest.mark.parametrize("stage", paths.STAGES)
def test_every_sample_placeholder_is_replaced(stage, repo):
    sample = sample_lib.load(stages.sample_path(repo, stage))
    with_placeholders = {
        key
        for key, value in sample.values.items()
        if stages.PLACEHOLDER_RE.search(json.dumps(value))
    }
    assert with_placeholders, "the sample has no placeholders to check"
    for name in helpers.ALL_FIXTURES:
        rendered = helpers.render(repo, name, stage)
        assert not stages.PLACEHOLDER_RE.search(rendered.text)
        auto = repo.auto_tfvars_keys(stage)
        # Every sample key with a placeholder is either rendered from the
        # answers or provided by Stage 0 outputs.
        assert with_placeholders <= set(rendered.values) | auto


def test_prefix_limit_matches_validation_blocks(repo):
    limit = repo.prefix_max_length()
    stage1 = (
        paths.stage_dir(repo.root, paths.RESMAN) / "variables.tf"
    ).read_text(encoding="utf-8")
    match = re.search(r"length\(var\.prefix\), 0\) < (\d+)", stage1)
    assert match is not None
    assert int(match.group(1)) - 1 == limit
    for prefix, ok in (("a" * limit, True), ("a" * (limit + 1), False)):
        assert re.fullmatch(models.PREFIX_PATTERN, prefix)
        answers = helpers.load_fixture("fedramp_high", prefix=prefix)
        found = [
            p
            for p in validate.problems(answers, repo)
            if p.startswith("prefix")
        ]
        assert (found == []) is ok


def test_tenant_key_limit_matches_validation_block(repo):
    text = (
        paths.stage_dir(repo.root, paths.RESMAN) / "variables.tf"
    ).read_text(encoding="utf-8")
    match = re.search(r"length\(k\) < (\d+)", text)
    assert match is not None
    limit = int(match.group(1)) - 1
    assert repo.tenant_key_max_length() == limit
    for key, ok in (("a" * limit, True), ("a" * (limit + 1), False)):
        answers = helpers.load_fixture(
            "fedramp_high",
            prefix="t",
            resman={
                "envs": {"P": {}},
                "tenants": {key: {"descriptive_name": "x"}},
            },
        )
        found = [p for p in validate.problems(answers, repo) if "key" in p]
        assert (found == []) is ok


def test_kms_comment_contradicts_no_default(repo):
    # The renderer replaces the sample comment because Stage 0 declares the
    # variable without a default; fail if that changes.
    text = (repo.bootstrap_dir / "variables.tf").read_text(encoding="utf-8")
    block = re.search(
        r'variable "kms_protection_level" \{(.*?)\n\}', text, re.DOTALL
    )
    assert block is not None
    assert "default" not in block.group(1)


def test_billing_export_count_matches_import_warning(repo):
    text = (repo.bootstrap_dir / "billing.tf").read_text(encoding="utf-8")
    assert re.search(
        r'module "billing-export-project" \{\n.*\n\s+count\s+= '
        r'local\.billing_mode == "org" \? 1 : 0',
        text,
    )
    assert re.search(
        r"var\.billing_account\.no_iam\s*\n\s*\? null\s*\n\s*: "
        r'var\.billing_account\.is_org_level \? "org"',
        text,
    )
    answers = helpers.load_fixture(
        "lab",
        imports={
            "0-bootstrap": {
                conftest.BILLING_EXPORT_ADDRESS: ("lab1-prod-billing-exp-0")
            }
        },
    )
    assert imports.warnings(answers, "0-bootstrap", repo)


@pytest.mark.terraform
def test_import_file_is_fmt_canonical():
    answers = helpers.load_fixture("lab")
    text = imports.dumps(
        answers.imports["0-bootstrap"], imports.header("0", answers.prefix)
    )
    result = helpers.terraform_fmt(text)
    assert result.returncode == 0, result.stderr
    assert result.stdout == text


def test_per_stage_tables_cover_every_stage():
    # A new stage must get an entry in every table keyed by stage.
    tables = (
        workspace.OUTPUT_LINKS,
        repo_lib._AUTO_TFVARS_LOCALS,
        validate._CLI_OWNED_KEYS,
        stages._BUILDERS,
    )
    for table in tables:
        assert set(table) == set(paths.STAGES)
