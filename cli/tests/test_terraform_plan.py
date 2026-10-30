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

"""Tests for the `terraform show -json` plan parser and counts."""

import copy

import pytest

import helpers
from stellar_engine.terraform import plan as plan_lib

FIXTURE_NAMES = sorted(path.stem for path in helpers.PLANS_DIR.glob("*.json"))
BUCKET = (
    'module.log-export-logbucket["audit-logs"]'
    ".google_logging_project_bucket_config.bucket[0]"
)


def _plan(name):
    return plan_lib.parse(helpers.plan_fixture(name))


def _changes(plan):
    return {change.address: change for change in plan.changes}


def _entry(actions, **change):
    return {
        "address": "terraform_data.a",
        "mode": "managed",
        "type": "terraform_data",
        "name": "a",
        "provider_name": "terraform.io/builtin/terraform",
        "change": {"actions": actions, "before": None, "after": {}, **change},
    }


def _minimal(*entries, **top):
    return {
        "format_version": "1.2",
        "terraform_version": "1.13.3",
        "resource_changes": list(entries),
        **top,
    }


def test_fixtures_exist():
    assert FIXTURE_NAMES == [
        "stage0-bootstrap-after-final",
        "stage0-bootstrap-first",
        "stage0-final-imports",
        "stage0-no-changes",
        "stage0-org-policy-drift",
        "stage0-org-policy-update",
        "targeted-after-partial",
        "targeted-no-compliance",
        "targeted-workload",
    ]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_every_fixture_parses(name):
    plan = _plan(name)
    assert plan.format_version == "1.2"
    assert plan.terraform_version == "1.13.3"
    assert not plan.errored
    assert plan.complete is not name.startswith("targeted-")
    assert sum(plan_lib.summary(plan).values()) == len(plan.changes) + sum(
        change.importing for change in plan.changes
    )
    for entries in (plan.changes, plan.drift):
        addresses = [change.address for change in entries]
        assert len(addresses) == len(set(addresses))


def test_first_apply_has_no_drift_key():
    doc = helpers.plan_fixture("stage0-bootstrap-first")
    assert "resource_drift" not in doc
    plan = plan_lib.parse(doc)
    assert plan.drift == ()
    assert plan.variable("bootstrap_user") == "user@example.com"
    assert plan.variable("missing") is None
    assert plan_lib.summary(plan) == {
        "create": 8,
        "update": 2,
        "replace": 0,
        "delete": 0,
        "forget": 0,
        "import": 2,
        "read": 1,
        "no-op": 0,
    }


def test_importing_project_updates():
    changes = _changes(_plan("stage0-bootstrap-first"))
    project = changes["module.automation-project.google_project.project[0]"]
    assert project.importing
    assert project.importing_id == "abc-prod-iac-core-0"
    assert project.action == "update"
    assert project.module_address == "module.automation-project"
    assert project.index == 0
    assert project.type == "google_project"
    assert project.name == "project"


def test_dependency_pending_read():
    changes = _changes(_plan("stage0-bootstrap-first"))
    read = changes["data.google_logging_project_settings.log_export"]
    assert read.mode == "data"
    assert not read.managed
    assert read.action == "read"
    assert read.action_reason == "read_because_dependency_pending"
    assert read.module_address is None
    assert read.index is None
    assert not read.changes_something


def test_bucket_import_replace_shape():
    plan = _plan("stage0-bootstrap-after-final")
    bucket = _changes(plan)[BUCKET]
    assert bucket.actions == ("delete", "create")
    assert bucket.action == "replace"
    assert bucket.deletes
    assert bucket.destructive
    assert bucket.importing_id == (
        "projects/abc-prod-audit-logs-0/locations/us-east4/buckets/audit-logs"
    )
    assert bucket.replace_paths == (("project",),)
    assert bucket.action_reason == "replace_because_cannot_update"
    assert bucket.before["project"] == "projects/abc-prod-audit-logs-0"
    assert bucket.after["project"] == "abc-prod-audit-logs-0"
    assert bucket.unknown_attributes == (
        "cmek_settings",
        "description",
        "id",
        "lifecycle_state",
        "name",
    )
    assert plan.variable("bootstrap_user") == "user@example.com"


def test_unknown_member_forces_the_kms_replace():
    member = _changes(_plan("stage0-bootstrap-after-final"))[
        'module.logging-kms.google_kms_crypto_key_iam_member.members["'
        'logging-encrypter"]'
    ]
    assert member.replace_paths == (("member",),)
    assert "member" in member.unknown_attributes
    assert member.index == "logging-encrypter"


def test_etag_only_drift_is_not_material():
    plan = _plan("stage0-no-changes")
    assert not plan.applyable
    assert plan.drift
    assert not any(change.material() for change in plan.drift)


def test_outside_policy_change_is_material():
    plan = _plan("stage0-org-policy-drift")
    assert len(plan.drift) == 11
    assert all(change.material() for change in plan.drift)


def test_material_ignores_noise_at_any_depth():
    def change(before, after):
        return plan_lib.parse(
            _minimal(_entry(["update"], before=before, after=after))
        ).changes[0]

    nested = {"spec": [{"etag": "1", "update_time": "t1", "rules": [1]}]}
    same = {"spec": [{"etag": "2", "update_time": "t2", "rules": [1]}]}
    other = {"spec": [{"etag": "2", "rules": [2]}]}
    assert not change(nested, same).material()
    assert change(nested, other).material()


def test_minor_format_versions_parse():
    plan = plan_lib.parse(_minimal(format_version="1.10"))
    assert plan.format_major == "1"
    assert plan.changes == ()
    assert (plan.applyable, plan.complete, plan.errored) == (True, True, False)
    assert plan.variables == {}


@pytest.mark.parametrize(
    ("doc", "message"),
    [
        ([], "not a JSON object"),
        ({"terraform_version": "1.13.3"}, "no string 'format_version'"),
        (_minimal(format_version="2.0"), "format 2.0"),
        (_minimal(format_version="0.2"), "format 0.2"),
        (_minimal(resource_changes={}), "not a list"),
        (_minimal(_entry(["create", "forget"])), "unknown actions"),
        (_minimal(_entry(["update", "update"])), "unknown actions"),
        (_minimal(_entry("create")), "no action list"),
        (_minimal("x"), "not an object"),
        (_minimal({"address": "a"}), "has no change object"),
        (_minimal(applyable="yes"), "applyable is not a boolean"),
        (_minimal(variables=[]), "is not an object"),
    ],
)
def test_parse_refuses(doc, message):
    with pytest.raises(plan_lib.PlanError, match=message):
        plan_lib.parse(doc)


def test_parse_reads_errored_and_incomplete_plans():
    plan = plan_lib.parse(_minimal(errored=True, complete=False))
    assert plan.errored
    assert not plan.complete


def test_create_before_destroy_is_a_replace():
    plan = plan_lib.parse(_minimal(_entry(["create", "delete"])))
    (change,) = plan.changes
    assert change.action == "replace"
    assert change.deletes
    assert plan_lib.summary(plan)["replace"] == 1


def test_forget_is_destructive_but_no_delete():
    plan = plan_lib.parse(_minimal(_entry(["forget"], after=None)))
    (change,) = plan.changes
    assert change.action == "forget"
    assert change.destructive
    assert not change.deletes
    assert plan_lib.summary(plan)["forget"] == 1


def test_import_by_identity_counts_as_import():
    entry = _entry(["no-op"], importing={"identity": {"name": "x"}})
    (change,) = plan_lib.parse(_minimal(entry)).changes
    assert change.importing
    assert change.importing_id == ""


def test_moved_and_deposed_entries():
    entry = _entry(["delete"], after=None)
    entry.update(previous_address="terraform_data.old", deposed="abcd1234")
    (change,) = plan_lib.parse(_minimal(entry)).changes
    assert change.previous_address == "terraform_data.old"
    assert change.deposed == "abcd1234"


def test_forced_paths_join_the_replace_paths():
    entry = _entry(["delete", "create"])
    entry["change"]["replace_paths"] = [["a", 0, "b"], ["c"]]
    (change,) = plan_lib.parse(_minimal(entry)).changes
    assert change.forced_paths == ("a.0.b", "c")


def test_summary_keys():
    plan = _plan("stage0-final-imports")
    assert tuple(plan_lib.summary(plan)) == plan_lib.SUMMARY_KEYS
    assert plan_lib.summary(plan) == {
        "create": 3,
        "update": 3,
        "replace": 0,
        "delete": 0,
        "forget": 0,
        "import": 8,
        "read": 0,
        "no-op": 5,
    }


def test_parse_does_not_change_the_document():
    doc = helpers.plan_fixture("stage0-bootstrap-after-final")
    before = copy.deepcopy(doc)
    plan_lib.parse(doc)
    assert doc == before
