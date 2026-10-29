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

"""Tests for seeding environments and suggesting prefixes."""

import random
import re

import pytest

import helpers
from stellar_engine import paths
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.config import seed


def _source(**overrides):
    return helpers.minimal_data(
        engine={"path": "/opt/engine"},
        groups={"gcp-devops": "platform"},
        resman={"tenants": {"ten1": {"descriptive_name": "Tenant"}}},
        imports={"0-bootstrap": {"google_project.project": "tst-prod-x"}},
        **overrides,
    )


def test_seed_drops_environment_specific_keys():
    source = _source()
    seeded = seed.seed(source)
    assert not set(seed.NEVER_CARRIED) & set(seeded)
    assert seeded["organization"] == source["organization"]
    assert seeded["groups"] == {"gcp-devops": "platform"}
    assert seeded["resman"] == source["resman"]
    seeded["resman"]["tenants"]["ten2"] = {}
    assert "ten2" not in source["resman"]["tenants"]


def test_seed_plus_new_prefix_validates():
    seeded = seed.seed(_source())
    seeded["prefix"] = "new"
    answers = answers_lib.parse(seeded)
    assert answers.imports == {}
    assert answers.engine is None


def test_review_notes_same_regime_only_lists_dropped_keys():
    notes = seed.review_notes(_source(kms_protection_level="HSM"), None)
    assert notes == [
        "the copy drops the imports, because they name resources of the "
        "source environment; add the imports for this one."
    ]
    assert seed.review_notes(_source(), "IL5") == notes


def test_seed_drops_existing_org_policies():
    source = _source(existing_org_policies=["iam.allowedPolicyMemberDomains"])
    assert "existing_org_policies" not in seed.seed(source)
    notes = seed.review_notes(source, None)
    assert any(
        "drops existing_org_policies" in note and "stellar imports scan" in note
        for note in notes
    )


def test_review_notes_on_regime_change():
    source = _source(
        kms_protection_level="HSM",
        region="us-south1",
        compliance={
            "regime": "FEDRAMP_MODERATE",
            "location": "us-south1",
            "allow_unlisted_region": True,
        },
        overrides={"0-bootstrap": {"iam": {}}},
    )
    notes = seed.review_notes(source, "IL4")[1:]
    assert len(notes) == 5
    assert notes[0].startswith("kms_protection_level HSM is explicit; the")
    assert "from FEDRAMP_MODERATE to IL4" in notes[0]
    assert notes[1].startswith("compliance.location us-south1 is explicit")
    assert notes[2].startswith("compliance.allow_unlisted_region is set")
    assert notes[3] == (
        "region us-south1 is not an Assured Workloads region for IL4; "
        "choose another."
    )
    assert notes[4].startswith("the copy keeps the overrides as written")


def test_review_notes_quiet_when_nothing_is_explicit():
    source = helpers.minimal_data(compliance={"regime": "FEDRAMP_MODERATE"})
    assert seed.review_notes(source, "IL4") == []


@pytest.mark.parametrize(
    ("base", "limit", "head"),
    [
        ("lab", 7, "lab"),
        ("example", 7, "exa"),
        ("Lab-Env_1", 7, "lab"),
        ("", 7, ""),
        ("123", 7, ""),
        ("lab", 4, ""),
        ("lab", 2, ""),
    ],
)
def test_suggest_prefix(base, limit, head):
    for value in range(50):
        prefix = seed.suggest_prefix(base, limit, random.Random(value))
        assert len(prefix) <= limit
        assert prefix.startswith(head)
        assert re.match(models.PREFIX_PATTERN, prefix), prefix
        assert len(prefix) == min(len(head) + seed.SUFFIX_LENGTH, limit)


def test_suggest_prefix_is_deterministic_for_a_seed():
    first = seed.suggest_prefix("lab", 7, random.Random(1))
    assert first == seed.suggest_prefix("lab", 7, random.Random(1))
    suggestions = {
        seed.suggest_prefix("lab", 7, random.Random(value))
        for value in range(20)
    }
    assert len(suggestions) > 1


def test_suggest_prefix_rejects_zero_limit():
    with pytest.raises(ValueError):
        seed.suggest_prefix("lab", 0, random.Random(0))


def test_resolve_source(tmp_path):
    home = paths.Home(tmp_path / "home")
    env = home.env("old")
    env.root.mkdir(parents=True)
    env.answers.write_text("prefix: old\n", encoding="utf-8")
    assert seed.resolve_source("old", home) == env.answers

    other = tmp_path / "other"
    other.mkdir()
    (other / "answers.yaml").write_text("prefix: x\n", encoding="utf-8")
    assert seed.resolve_source(str(other), home) == other / "answers.yaml"
    assert (
        seed.resolve_source(str(other / "answers.yaml"), home)
        == other / "answers.yaml"
    )


def test_resolve_source_missing(tmp_path):
    home = paths.Home(tmp_path / "home")
    with pytest.raises(FileNotFoundError, match="No environment"):
        seed.resolve_source("nope", home)
    with pytest.raises(FileNotFoundError):
        seed.resolve_source(str(tmp_path / "missing.yaml"), home)


def test_seed_drops_the_stage0_phase():
    source = _source(stage0_phase="final")
    seeded = seed.seed(source)
    assert "stage0_phase" not in seeded
    seeded["prefix"] = "new"
    assert answers_lib.parse(seeded).stage0_phase == models.STAGE0_BOOTSTRAP
    notes = seed.review_notes(source, None)
    assert any(
        "bootstrap stage0_phase" in note and "final Stage 0 apply" in note
        for note in notes
    )


def test_review_notes_quiet_for_a_bootstrap_source():
    notes = seed.review_notes(_source(stage0_phase="bootstrap"), None)
    assert not any("stage0_phase" in note for note in notes)
