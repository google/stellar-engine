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

"""Tests for recording the organization policies that Stage 0 imports."""

import pytest

import conftest
import helpers
from stellar_engine import org_policies
from stellar_engine import paths
from stellar_engine.config import answers as answers_lib
from stellar_engine.gcp import api

_KEPT = ("iam.allowedPolicyMemberDomains", "storage.uniformBucketLevelAccess")
_SCANNED = [*_KEPT, "custom.kmsRotation", "unmanaged.constraint"]
_GATED = "compute.managed.restrictProtocolForwardingCreationForTypes"


@pytest.fixture
def home(tmp_path):
    return tmp_path / "home"


@pytest.fixture
def env(home):
    return paths.Home(home).env("tst")


def _save(env, **overrides):
    """Saves minimal answers for the environment and returns them."""
    answers_lib.save(env.answers, helpers.minimal_answers(**overrides))
    return answers_lib.load(env.answers)


def test_scan_sorts_the_existing_policies(env, repo, cloud):
    answers = _save(env)
    cloud.org_policies = _SCANNED

    scanned = org_policies.scan(answers, repo, cloud)

    assert scanned.kept == _KEPT
    assert scanned.custom == ("custom.kmsRotation",)
    assert scanned.undeclared == ("unmanaged.constraint",)
    assert ("org_policies", conftest.ORG_ID) in cloud.calls


def test_scan_raises_cloud_errors(env, repo, cloud):
    answers = _save(env)
    cloud.org_policies = api.AccessDeniedError("no orgpolicy access")

    with pytest.raises(api.AccessDeniedError, match="no orgpolicy access"):
        org_policies.scan(answers, repo, cloud)


@pytest.mark.parametrize(
    ("regime", "kept"),
    [
        ("IL5", (_GATED,)),
        ("FEDRAMP_MODERATE", ()),
    ],
)
def test_scan_follows_the_regime(env, home, repo, cloud, regime, kept):
    answers = _save(env, compliance={"regime": regime})
    cloud.org_policies = [_GATED]

    scanned = org_policies.scan(answers, repo, cloud)

    assert scanned.kept == kept
    assert org_policies.record(env, scanned, repo, home) == bool(kept)
    assert answers_lib.load(env.answers).existing_org_policies == list(kept)


def test_keep_scanned_replaces_the_list(repo):
    scanned = repo.scan_org_policies(_SCANNED, "IL5")
    data = {"existing_org_policies": ["stale.constraint"]}
    org_policies.keep_scanned(scanned)(data)
    assert data["existing_org_policies"] == list(_KEPT)


def test_record_saves_the_kept_policies(env, home, repo):
    _save(env)
    env.answers.write_text(
        "# my note\n" + env.answers.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    scanned = repo.scan_org_policies(_SCANNED, "IL5")

    assert org_policies.record(env, scanned, repo, home)

    saved = answers_lib.load(env.answers)
    assert saved.existing_org_policies == list(_KEPT)
    assert "# my note" in env.answers.read_text(encoding="utf-8")
    assert conftest.mode(env.answers) == 0o600


def test_record_leaves_a_current_list_alone(env, home, repo):
    _save(env, existing_org_policies=list(_KEPT))
    before = env.answers.read_bytes()
    scanned = repo.scan_org_policies(_SCANNED, "IL5")

    assert not org_policies.record(env, scanned, repo, home)

    assert env.answers.read_bytes() == before


def test_record_replaces_a_stale_list(env, home, repo):
    # Stage 0 no longer declares the stored policy, which the scan fixes.
    _save(env, existing_org_policies=["unmanaged.constraint"])

    assert org_policies.record(env, repo.scan_org_policies([]), repo, home)

    assert answers_lib.load(env.answers).existing_org_policies == []


def test_record_raises_answer_problems(env, home, repo):
    _save(
        env,
        overrides={
            "0-bootstrap": {"org_policies_config": {"import_defaults": True}}
        },
    )
    before = env.answers.read_bytes()
    scanned = repo.scan_org_policies(list(_KEPT), "IL5")

    with pytest.raises(answers_lib.AnswersError, match="import_defaults"):
        org_policies.record(env, scanned, repo, home)
    assert env.answers.read_bytes() == before
