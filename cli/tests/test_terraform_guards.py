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

"""Tests for the plan guards, over the plan fixtures."""

import dataclasses

import pytest

import helpers
from stellar_engine import iam_diff
from stellar_engine import repo as repo_lib
from stellar_engine.terraform import guards
from stellar_engine.terraform import plan as plan_lib

WORKLOAD = "google_assured_workloads_workload.primary[0]"
NO_COMPLIANCE = "module.no-compliance-folder[0]"
BLOCK = guards.Level.BLOCK
CONFIRM = guards.Level.CONFIRM
INFO = guards.Level.INFO
FINAL = guards.HistoryView(final_applied=True)
SAME_INPUTS = guards.HistoryView(
    last_tfvars_sha256="abc123",
    tfvars_sha256="abc123",
    last_engine_sha256="e1",
    engine_sha256="e1",
)
NEW_INPUTS = dataclasses.replace(SAME_INPUTS, tfvars_sha256="def456")
# A new engine commit or new provider versions are operator changes too.
NEW_ENGINE = dataclasses.replace(SAME_INPUTS, engine_sha256="e2")
# A dirty checkout leaves the code unknown.
DIRTY_ENGINE = dataclasses.replace(SAME_INPUTS, engine_sha256=None)


def _plan(name):
    return plan_lib.parse(helpers.plan_fixture(name))


def _evaluate(plan, repo, stage="0", run_state=None, targeted_to=None):
    if isinstance(plan, str):
        plan = _plan(plan)
    return guards.evaluate(
        plan,
        stage=stage,
        run_state=run_state,
        repo=repo,
        targeted_to=targeted_to,
    )


def _keys(findings):
    return [(finding.level, finding.key) for finding in findings]


def _change(address, rtype, actions, **fields):
    values = {
        "address": address,
        "module_address": None,
        "type": rtype,
        "name": "x",
        "index": None,
        "mode": plan_lib.MANAGED,
        "actions": tuple(actions),
        "action_reason": None,
        "importing_id": None,
        "replace_paths": (),
        "before": {},
        "after": {},
        "after_unknown": {},
    }
    values.update(fields)
    return plan_lib.Change(**values)


def _synthetic(*changes, bootstrap_user=None, **fields):
    values = {
        "format_version": "1.2",
        "terraform_version": "1.13.3",
        "applyable": True,
        "complete": True,
        "errored": False,
        "variables": {"bootstrap_user": bootstrap_user},
        "changes": changes,
    }
    values.update(fields)
    return plan_lib.Plan(**values)


@pytest.mark.parametrize(
    ("name", "kwargs", "expected"),
    [
        (
            "stage0-bootstrap-first",
            {},
            [(CONFIRM, guards.IAM_MEMBER_REMOVAL)] * 2,
        ),
        ("stage0-final-imports", {}, []),
        ("stage0-final-imports", {"run_state": FINAL}, []),
        ("stage0-org-policy-update", {}, []),
        ("stage0-org-policy-update", {"run_state": NEW_INPUTS}, []),
        ("stage0-org-policy-update", {"run_state": NEW_ENGINE}, []),
        ("stage0-org-policy-update", {"run_state": DIRTY_ENGINE}, []),
        (
            "stage0-org-policy-update",
            {"run_state": SAME_INPUTS},
            [(CONFIRM, guards.ORG_POLICY_DRIFT_REVERT)] * 12,
        ),
        (
            "stage0-org-policy-drift",
            {},
            [(CONFIRM, guards.ORG_POLICY_DRIFT_REVERT)] * 11,
        ),
        ("stage0-no-changes", {}, [(INFO, guards.NO_CHANGES)]),
        (
            "stage0-no-changes",
            {"run_state": SAME_INPUTS},
            [(INFO, guards.NO_CHANGES)],
        ),
        (
            "targeted-workload",
            {"targeted_to": WORKLOAD},
            [(INFO, guards.TARGETED_SCOPE)],
        ),
        (
            "targeted-no-compliance",
            {"targeted_to": NO_COMPLIANCE},
            [(INFO, guards.TARGETED_SCOPE)],
        ),
        ("targeted-after-partial", {"targeted_to": (WORKLOAD,)}, []),
    ],
)
def test_fixture_findings(repo, name, kwargs, expected):
    assert _keys(_evaluate(name, repo, **kwargs)) == expected


def test_bootstrap_plan_after_final_is_blocked(repo):
    findings = _evaluate("stage0-bootstrap-after-final", repo)
    assert _keys(findings) == [
        (BLOCK, guards.PHASE_BOOTSTRAP_AFTER_FINAL),
        *[(BLOCK, guards.IMPORT_REPLACE_15725)] * 4,
        *[(CONFIRM, guards.DELETE_CONFIRM)] * 3,
        (CONFIRM, guards.IAM_MEMBER_REMOVAL),
    ]
    phase = findings[0]
    assert "deletes 6 organization policies" in phase.detail
    assert "stage0_phase=final" in phase.detail
    assert phase.address is not None
    assert "google_org_policy_policy" in phase.address
    buckets = findings[1:5]
    assert {finding.remedy_key for finding in buckets} == {
        guards.IMPORT_REPLACE_15725
    }
    assert all("issue 15725" in finding.detail for finding in buckets)
    confirmed = {finding.address for finding in findings[5:8]}
    assert confirmed == {
        'module.logging-kms.google_kms_crypto_key_iam_member.members["'
        'logging-encrypter"]',
        'module.automation-project.google_project_iam_member.bindings["'
        'bootstrap-user"]',
        'module.automation-project.google_project_service.project_services["'
        'orgpolicy.googleapis.com"]',
    }
    kms = next(f for f in findings if "kms" in (f.address or ""))
    assert "forced by member" in kms.detail
    assert "member known only after apply" in kms.detail
    removal = findings[-1]
    assert "user:former-admin@example.com" in removal.detail
    assert "organizationAdmin" in removal.detail


def test_final_apply_record_blocks_any_bootstrap_plan(repo):
    findings = _evaluate(
        "targeted-workload", repo, run_state=FINAL, targeted_to=WORKLOAD
    )
    assert _keys(findings) == [
        (BLOCK, guards.PHASE_BOOTSTRAP_AFTER_FINAL),
        (INFO, guards.TARGETED_SCOPE),
    ]
    assert findings[0].address is None
    assert "run-state records a final apply" in findings[0].detail


def test_phase_guard_is_stage0_only(repo):
    findings = _evaluate("stage0-bootstrap-after-final", repo, stage="1")
    keys = _keys(findings)
    assert (BLOCK, guards.PHASE_BOOTSTRAP_AFTER_FINAL) not in keys
    assert keys.count((BLOCK, guards.IMPORT_REPLACE_15725)) == 4
    # Outside Stage 0 every other delete needs a confirmation.
    assert keys.count((CONFIRM, guards.DELETE_CONFIRM)) == 9


def test_drift_outside_terraform_needs_confirmation(repo):
    findings = _evaluate("stage0-org-policy-drift", repo, run_state=NEW_INPUTS)
    assert len(findings) == 11
    assert all("outside Terraform" in f.detail for f in findings)
    assert all("Answer no" in f.detail for f in findings)
    no_ops = {
        change.address
        for change in _plan("stage0-org-policy-drift").changes
        if change.actions == ("no-op",)
    }
    assert no_ops.isdisjoint(f.address for f in findings)


def test_unchanged_inputs_count_only_without_other_changes(repo):
    plan = _plan("stage0-org-policy-update")
    extra = _change(
        "google_storage_bucket.x", "google_storage_bucket", ["create"]
    )
    plan = dataclasses.replace(plan, changes=(*plan.changes, extra))
    assert _evaluate(plan, repo, run_state=SAME_INPUTS) == []


def test_importing_policy_updates_are_no_drift(repo):
    plan = _plan("stage0-final-imports")
    assert _evaluate(plan, repo, run_state=SAME_INPUTS) == []


def test_targeted_scope_blocks_other_changes(repo):
    findings = _evaluate("targeted-workload", repo, targeted_to=NO_COMPLIANCE)
    assert _keys(findings) == [
        (BLOCK, guards.TARGETED_SCOPE),
        (INFO, guards.TARGETED_SCOPE),
    ]
    assert findings[0].address == WORKLOAD
    assert NO_COMPLIANCE in findings[0].detail


def test_targeted_scope_over_a_full_plan(repo):
    findings = _evaluate("stage0-bootstrap-first", repo, targeted_to=WORKLOAD)
    blocked = guards.blocks(findings)
    assert len(blocked) == 8
    assert {f.key for f in blocked} == {guards.TARGETED_SCOPE}
    assert WORKLOAD not in {f.address for f in blocked}


def test_targeted_plans_may_be_incomplete(repo):
    plan = _plan("targeted-workload")
    assert not plan.complete
    assert _keys(_evaluate(plan, repo)) == [(BLOCK, guards.PLAN_INTEGRITY)]


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"errored": True}, "Planning failed"),
        ({"errored": True, "applyable": False}, "Planning failed"),
        ({"complete": False}, "defers changes"),
    ],
)
def test_plan_integrity_blocks_alone(repo, fields, message):
    delete = _change("google_folder.x", "google_folder", ["delete"])
    findings = _evaluate(_synthetic(delete, **fields), repo)
    (finding,) = findings
    assert (finding.level, finding.key) == (BLOCK, guards.PLAN_INTEGRITY)
    assert message in finding.detail


def test_errored_targeted_plan_is_blocked(repo):
    plan = _synthetic(errored=True, complete=False)
    assert _keys(_evaluate(plan, repo, targeted_to=WORKLOAD)) == [
        (BLOCK, guards.PLAN_INTEGRITY)
    ]


def test_integrity_finding_for_a_parse_error():
    error = plan_lib.PlanError("The plan uses JSON format 2.0")
    finding = guards.integrity_finding(error)
    assert (finding.level, finding.key) == (BLOCK, guards.PLAN_INTEGRITY)
    assert "format 2.0" in finding.detail


@pytest.mark.parametrize("rtype", sorted(guards.PROTECTED_TYPES))
@pytest.mark.parametrize("actions", [["delete"], ["delete", "create"]])
def test_protected_types_block_in_stage0(repo, rtype, actions):
    change = _change(f"{rtype}.x", rtype, actions)
    stage0 = _evaluate(_synthetic(change), repo)
    assert _keys(stage0) == [(BLOCK, guards.PROTECTED_DELETE)]
    stage1 = _evaluate(_synthetic(change), repo, stage="1-resman")
    assert _keys(stage1) == [(CONFIRM, guards.DELETE_CONFIRM)]


def test_forget_needs_confirmation(repo):
    change = _change("google_folder.x", "google_folder", ["forget"])
    (finding,) = _evaluate(_synthetic(change), repo)
    assert (finding.level, finding.key) == (CONFIRM, guards.DELETE_CONFIRM)
    assert "without destroying" in finding.detail


def test_workload_import_replace(repo):
    change = _change(
        WORKLOAD,
        repo_lib.WORKLOAD_RESOURCE,
        ["delete", "create"],
        importing_id="organizations/123456789012/locations/us-east4/"
        "workloads/my-workload",
        replace_paths=(("billing_account",), ("resource_settings",)),
    )
    (finding,) = _evaluate(_synthetic(change), repo)
    assert (finding.level, finding.key) == (BLOCK, guards.WORKLOAD_INPUT_ONLY)
    assert "billing_account, resource_settings" in finding.detail


def test_workload_import_replace_falls_back_to_the_repo(repo):
    change = _change(
        WORKLOAD,
        repo_lib.WORKLOAD_RESOURCE,
        ["delete", "create"],
        importing_id="w",
        replace_paths=(("display_name",),),
    )
    (finding,) = _evaluate(_synthetic(change), repo)
    assert finding.key == guards.WORKLOAD_INPUT_ONLY
    try:
        expected = repo.assured_workload().replaced_on_import
    except repo_lib.RepoError:
        expected = repo_lib.WORKLOAD_INPUT_ONLY
    assert f"sets {', '.join(expected)} without" in finding.detail


@pytest.mark.parametrize(
    ("rtype", "replace_paths", "before", "after"),
    [
        ("google_project", (("folder_id",),), {}, {}),
        (
            guards.LOG_BUCKET_TYPE,
            (("location",),),
            {"project": "projects/p"},
            {"project": "p"},
        ),
        (
            guards.LOG_BUCKET_TYPE,
            (("project",),),
            {"project": "other"},
            {"project": "p"},
        ),
    ],
)
def test_other_import_replaces(repo, rtype, replace_paths, before, after):
    change = _change(
        f"{rtype}.x",
        rtype,
        ["delete", "create"],
        importing_id="x",
        replace_paths=replace_paths,
        before=before,
        after=after,
    )
    findings = _evaluate(_synthetic(change), repo)
    assert _keys(findings) == [(BLOCK, guards.IMPORT_REPLACE)]
    assert findings[0].remedy_key is None


def test_import_replace_blocks_in_every_stage(repo):
    change = _change(
        "google_project.x",
        "google_project",
        ["delete", "create"],
        importing_id="x",
    )
    findings = _evaluate(_synthetic(change), repo, stage="1")
    assert _keys(findings) == [(BLOCK, guards.IMPORT_REPLACE)]


@pytest.mark.parametrize(
    ("actions", "before", "after", "unknown", "message"),
    [
        (
            ["create"],
            None,
            {"role": "roles/x"},
            {},
            "creates the authoritative",
        ),
        (["delete"], {"role": "roles/x"}, None, {}, "every member loses"),
        (
            ["update"],
            {"role": "roles/x", "members": ["user:a@example.com"]},
            {"role": "roles/x"},
            {"members": True},
            "known only after apply",
        ),
        (
            ["update"],
            {"role": "roles/x", "members": ["user:a@example.com"]},
            {"role": "roles/x", "members": []},
            {},
            "removes user:a@example.com from roles/x",
        ),
    ],
)
def test_org_iam_binding_changes(
    repo, actions, before, after, unknown, message
):
    change = _change(
        'module.organization.google_organization_iam_binding.authoritative["'
        'roles/x"]',
        iam_diff.BINDING_TYPE,
        actions,
        before=before,
        after=after,
        after_unknown=unknown,
    )
    findings = _evaluate(_synthetic(change), repo)
    removal = [f for f in findings if f.key == guards.IAM_MEMBER_REMOVAL]
    (finding,) = removal
    assert finding.level == CONFIRM
    assert message in finding.detail
    assert "organization IAM review" in finding.detail


def test_org_iam_additions_pass(repo):
    change = _change(
        "google_organization_iam_binding.x",
        iam_diff.BINDING_TYPE,
        ["update"],
        before={"role": "roles/x", "members": ["user:a@example.com"]},
        after={
            "role": "roles/x",
            "members": ["user:a@example.com", "user:b@example.com"],
        },
    )
    assert _evaluate(_synthetic(change), repo) == []


def test_org_iam_policy_needs_a_confirmation(repo):
    change = _change(
        "google_organization_iam_policy.x",
        guards.ORG_IAM_POLICY_TYPE,
        ["update"],
    )
    (finding,) = _evaluate(_synthetic(change), repo)
    assert (finding.level, finding.key) == (CONFIRM, guards.IAM_POLICY_REPLACE)
    assert "whole organization IAM policy" in finding.detail
    assert "by hand" in finding.detail


def test_data_reads_and_no_ops_never_count(repo):
    read = _change("data.google_x.y", "google_x", ["read"], mode="data")
    no_op = _change("google_folder.x", "google_folder", ["no-op"])
    plan = _synthetic(read, no_op, complete=False)
    assert _evaluate(plan, repo, targeted_to="google_y.z") == []


def test_unknown_stage(repo):
    with pytest.raises(ValueError, match="Unknown stage"):
        _evaluate(_synthetic(), repo, stage="9")


def test_blocks_and_confirmations():
    findings = [
        guards.Finding(INFO, guards.NO_CHANGES, None, "a"),
        guards.Finding(CONFIRM, guards.DELETE_CONFIRM, "x", "b"),
        guards.Finding(BLOCK, guards.PROTECTED_DELETE, "y", "c"),
    ]
    assert guards.blocks(findings) == [findings[2]]
    assert guards.confirmations(findings) == [findings[1]]


def test_history_view_satisfies_the_protocol():
    history: guards.History = guards.HistoryView()
    assert not history.final_applied
    assert history.tfvars_sha256 is None
    assert history.engine_sha256 is None


def test_unchanged_inputs_name_the_engine(repo):
    plan = "stage0-org-policy-update"
    findings = _evaluate(plan, repo, run_state=SAME_INPUTS)
    assert findings
    assert all("engine commit" in finding.detail for finding in findings)


def test_finding_line():
    finding = guards.Finding(
        guards.Level.BLOCK, guards.PROTECTED_DELETE, "google_folder.x", "Why."
    )
    assert finding.line() == "BLOCK protected_delete google_folder.x: Why."
    bare = guards.Finding(guards.Level.INFO, guards.NO_CHANGES, None, "None.")
    assert bare.line() == "INFO no_changes: None."
