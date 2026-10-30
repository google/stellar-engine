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

"""Tests for the deploy step catalog: its shape and each step's check."""

import json
import re
import shlex

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine import paths
from stellar_engine import workspace as workspace_lib
from stellar_engine.commands import common
from stellar_engine.commands import deploy as deploy_cmd
from stellar_engine.config import answers as answers_lib
from stellar_engine.deploy import apply
from stellar_engine.deploy import catalog
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import remedies
from stellar_engine.deploy.catalog import common as catalog_common
from stellar_engine.deploy.catalog import pre
from stellar_engine.deploy.catalog import stage0
from stellar_engine.deploy.catalog import stage1
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.render import phase
from stellar_engine.wizard import prompts

_S = model.StepStatus
_STEPS = catalog.catalog()
_BY_ID = {step.id: step for step in _STEPS}
_BUCKET = "tst-prod-iac-core-bootstrap-0"
_REMOTE_PROVIDERS = (
    f'terraform {{\n  backend "gcs" {{\n    bucket = "{_BUCKET}"\n  }}\n}}\n'
)
_CACHED = {
    "version": 3,
    "backend": {"type": "gcs", "config": {"bucket": _BUCKET}, "hash": 1},
}
_WORKLOAD = "google_assured_workloads_workload.primary[0]"
_RESMAN_SA = "tst-prod-resman-0@tst-prod-iac-core-0.iam.gserviceaccount.com"
# Stage 0 creates the billing export project, which uses data transfers.
_BQ = (*cloud_ops.BQ_SERVICES, cloud_ops.BQ_TRANSFER_SERVICE)


_ctx = helpers_deploy.scripted_ctx


def _check(ctx, step_id):
    return engine.check(ctx, _BY_ID[step_id])


def _run(step, ctx):
    assert step.run is not None
    step.run(ctx)


def _fake(ctx) -> conftest.FakeCloud:
    """Returns the FakeCloud of a context, so a test can change it."""
    assert isinstance(ctx.cloud, conftest.FakeCloud)
    return ctx.cloud


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data)


def _local_state(ctx, doc):
    _write(ctx.workspace("0") / probe_lib.STATE_FILE, _bytes(doc))
    ctx.invalidate()


def _bytes(doc):
    return helpers_deploy.state_bytes(doc)


def _workload_state(serial=5):
    workload = helpers_deploy.resource(
        None,
        "google_assured_workloads_workload",
        "primary",
        [
            helpers_deploy.instance(
                {
                    "name": helpers_deploy.WORKLOAD,
                    "resources": [
                        {
                            "resource_id": "222",
                            "resource_type": "CONSUMER_FOLDER",
                        }
                    ],
                },
                0,
            )
        ],
    )
    return helpers_deploy.state_doc([workload], serial=serial)


def _migrated(ctx, serial=298, generation=17):
    """Makes the Stage 0 workspace use the remote state in the bucket."""
    ws = ctx.workspace("0")
    _write(ws / workspace_lib.BOOTSTRAP_PROVIDERS, _REMOTE_PROVIDERS)
    _write(
        ctx.env.fast_config / "providers" / workspace_lib.BOOTSTRAP_PROVIDERS,
        _REMOTE_PROVIDERS,
    )
    _write(ws / probe_lib.CACHED_BACKEND, json.dumps(_CACHED))
    _write(ws / probe_lib.STATE_FILE, b"")
    _fake(ctx).objects[(_BUCKET, probe_lib.REMOTE_OBJECT)] = api.ObjectData(
        _bytes(helpers_deploy.project_state(serial)), generation
    )
    ctx.invalidate()


def _record_apply(ctx, step_id, stage="0"):
    """Records an apply at the current state, as the pipeline does."""
    record = ctx.record(step_id)
    record.state = apply.current_state(ctx, stage)
    record.tfvars_sha256 = apply.inputs_sha256(ctx, stage)
    ctx.save()


# The catalog shape.


def test_ids_are_unique_and_prefixed_by_their_stage():
    ids = [step.id for step in _STEPS]
    assert len(ids) == len(set(ids))
    prefixes = {"pre": "pre.", "0": "s0.", "1": "s1."}
    for step in _STEPS:
        assert step.id.startswith(prefixes[step.stage]), step.id
    assert list(catalog.STAGE_TITLES) == ["pre", "0", "1"]


def test_stages_follow_the_deployment_order():
    order = list(catalog.STAGE_TITLES)
    ranks = [order.index(step.stage) for step in _STEPS]
    assert ranks == sorted(ranks)


def test_requires_name_earlier_steps():
    """Every prerequisite comes before its step, so `requires` is acyclic."""
    seen = set()
    for step in _STEPS:
        assert set(step.requires) <= seen, step.id
        seen.add(step.id)


@pytest.mark.parametrize("step", _STEPS, ids=lambda step: step.id)
def test_doc_anchor_resolves(step):
    assert helpers.doc_resolves(step.doc_anchor), step.doc_anchor


def test_stage1_anchor_resolves():
    assert helpers.doc_resolves(stage1.DDG)


@pytest.mark.parametrize(
    "key",
    sorted({key for step in _STEPS for key in step.remedies}),
)
def test_remedies_exist_and_their_docs_resolve(key):
    assert helpers.doc_resolves(remedies.REMEDIES[key].doc)


def test_conditional_steps_say_when_they_apply():
    conditional = {
        step.id for step in _STEPS if step.applies_when is not model.always
    }
    assert {step.id for step in _STEPS if step.when} == conditional


@pytest.mark.parametrize(
    "step",
    [step for step in _STEPS if step.run or step.kind == model.StepKind.MANUAL],
    ids=lambda step: step.id,
)
def test_explanations_name_a_fallback(tmp_path, step):
    text = step.explain(_ctx(tmp_path))
    assert "Fallback" in text or step.kind == model.StepKind.MANUAL, text


@pytest.mark.parametrize("step", _STEPS, ids=lambda step: step.id)
def test_explanations_follow_the_prose_rules(tmp_path, step):
    text = step.explain(_ctx(tmp_path))
    assert not re.search(r"[—&]|\b(we|our|I)\b", text), text


# Prerequisites.


def test_apis_done_and_pending(tmp_path, repo):
    required = checks.required_services(repo)
    cloud = conftest.FakeCloud(services=set(required[1:]))
    ctx = _ctx(tmp_path, cloud=cloud)
    verdict = _check(ctx, "pre.apis")
    assert verdict.status == _S.PENDING
    assert required[0] in (verdict.remedy or "")
    _run(pre.APIS, ctx)
    assert _check(ctx, "pre.apis").status == _S.DONE


def test_apis_denied_hand_over_the_commands(tmp_path, repo):
    required = checks.required_services(repo)
    cloud = conftest.FakeCloud(
        services=set(required[1:]),
        write_errors={"enable_services": api.AccessDeniedError("no")},
    )
    with pytest.raises(model.BlockedError) as raised:
        _run(pre.APIS, _ctx(tmp_path, cloud=cloud))
    assert "enableServices.sh" in (raised.value.remedy or "")


def test_iam_roles_follow_preflight(tmp_path, repo):
    assert _check(_ctx(tmp_path), "pre.iam_roles").status == _S.DONE
    role = repo.required_roles()[0]
    cloud = conftest.FakeCloud(denied_org_perms={f"{role}.permission"})
    verdict = _check(_ctx(tmp_path / "b", cloud=cloud), "pre.iam_roles")
    assert verdict.status == _S.PENDING
    assert f"iam.{role}" in verdict.detail


def _lacking_role(repo):
    """Returns a role and a FakeCloud on which preflight finds it missing."""
    role = repo.required_roles()[0]
    return role, conftest.FakeCloud(denied_org_perms={f"{role}.permission"})


def test_iam_roles_run_grants_and_waits_for_iam(tmp_path, repo):
    role, cloud = _lacking_role(repo)
    slept = []

    def sleep(seconds):
        # IAM applies the grant during the second wait.
        slept.append(seconds)
        if len(slept) == 2:
            cloud.denied_org_perms.clear()

    ctx = _ctx(tmp_path, [True], cloud=cloud, sleep=sleep)
    _run(pre.IAM_ROLES, ctx)
    (write,) = cloud.writes
    assert write[0] == "set_org_iam_policy"
    assert ctx.run_state.iam.snapshots[0].reason == "grant"
    assert slept == [pre.GRANT_POLL_SECONDS] * 2
    assert f"Granted {role}." in helpers_deploy.output(ctx)
    assert _check(ctx, "pre.iam_roles").status == _S.DONE


def test_iam_roles_stop_when_iam_is_slow(tmp_path, repo):
    _, cloud = _lacking_role(repo)
    slept = []
    ctx = _ctx(tmp_path, [True], cloud=cloud, sleep=slept.append)
    with pytest.raises(model.StoppedError) as raised:
        _run(pre.IAM_ROLES, ctx)
    assert str(raised.value) == "IAM has not applied the grants yet."
    assert raised.value.remedy == "Rerun stellar deploy in a few minutes."
    assert sum(slept) == pre.GRANT_WAIT_SECONDS
    assert set(slept) == {pre.GRANT_POLL_SECONDS}
    assert len(cloud.writes) == 1


def test_iam_roles_held_directly_wait_then_block(tmp_path, repo):
    # The deployer holds the role directly, yet preflight keeps failing
    # it, as while an earlier grant propagates or under a deny policy.
    role, cloud = _lacking_role(repo)
    cloud.policy = {
        **conftest.empty_policy(),
        "bindings": [{"role": role, "members": [f"user:{conftest.USER}"]}],
    }
    slept = []
    ctx = _ctx(tmp_path, cloud=cloud, sleep=slept.append)
    with pytest.raises(model.BlockedError) as raised:
        _run(pre.IAM_ROLES, ctx)
    assert cloud.writes == []
    assert helpers_deploy.asked(ctx) == []
    assert (
        "The deployer holds the failing roles directly. Waiting up to "
        f"{pre.GRANT_WAIT_SECONDS} seconds for IAM to apply them."
    ) in helpers_deploy.output(ctx)
    assert sum(slept) == pre.GRANT_WAIT_SECONDS
    assert f"Preflight still fails iam.{role}," in raised.value.reason
    assert "granted none" in raised.value.reason
    remedy = raised.value.remedy or ""
    assert "earlier grant" in remedy
    assert "deny policy" in remedy


def test_iam_roles_grant_exits_0_once_iam_applies_it(tmp_path, repo):
    _, cloud = _lacking_role(repo)
    ctx = _ctx(
        tmp_path,
        [True],
        cloud=cloud,
        sleep=lambda seconds: cloud.denied_org_perms.clear(),
    )
    report = engine.run(ctx, [pre.IAM_ROLES])
    assert deploy_cmd.exit_code(report) == 0
    assert report.results[0].status == _S.DONE


def test_prerequisites_stop_after_the_first_apply(tmp_path):
    ctx = _ctx(tmp_path)
    assert catalog_common.first_apply_pending(ctx)
    _local_state(ctx, helpers_deploy.project_state())
    assert not catalog_common.first_apply_pending(ctx)
    for step_id in ("pre.iam_roles", "pre.preflight", "pre.super_admin"):
        assert not _BY_ID[step_id].applies_when(ctx)
    assert _BY_ID["pre.apis"].applies_when(ctx)


def _unreadable_remote(ctx):
    """Makes both identities fail to read the remote Stage 0 state."""
    _fake(ctx).objects[(_BUCKET, probe_lib.REMOTE_OBJECT)] = (
        api.AccessDeniedError("denied")
    )
    ctx.invalidate()


def test_prerequisites_stay_off_without_the_remote_state(tmp_path):
    # Disabled stage service accounts or expired credentials must never
    # turn the organization role grant back on after Stage 0 ran.
    ctx = _ctx(tmp_path)
    _migrated(ctx)
    _unreadable_remote(ctx)
    assert ctx.stage0().migrated is None
    assert not catalog_common.first_apply_pending(ctx)
    for step_id in ("pre.iam_roles", "pre.preflight", "pre.super_admin"):
        assert not engine.applies(ctx, _BY_ID[step_id])
    # The policies that the state may hold are unknown, not missing.
    assert _check(ctx, "pre.org_policies").status == _S.UNKNOWN


def test_prerequisites_stop_once_the_remote_providers_exist(tmp_path):
    ctx = _ctx(tmp_path)
    _write(
        ctx.env.fast_config / "providers" / workspace_lib.BOOTSTRAP_PROVIDERS,
        _REMOTE_PROVIDERS,
    )
    ctx.invalidate()
    assert not catalog_common.first_apply_pending(ctx)


def test_org_policies_record_the_existing_policies(tmp_path, repo):
    kept = repo.scan_org_policies(
        sorted(repo.declared_org_policies("IL5")), "IL5"
    ).kept
    cloud = conftest.FakeCloud(org_policies=list(kept[:2]))
    ctx = _ctx(tmp_path, cloud=cloud)
    verdict = _check(ctx, "pre.org_policies")
    assert verdict.status == _S.PENDING
    assert kept[0] in verdict.detail
    _run(pre.ORG_POLICIES, ctx)
    assert ctx.answers.existing_org_policies == sorted(kept[:2])
    assert helpers.load_answers(ctx.home).existing_org_policies == sorted(
        kept[:2]
    )
    assert _check(ctx, "pre.org_policies").status == _S.DONE


def test_org_policies_in_the_state_count_as_recorded(tmp_path, repo):
    kept = repo.scan_org_policies(
        sorted(repo.declared_org_policies("IL5")), "IL5"
    ).kept
    cloud = conftest.FakeCloud(org_policies=[kept[0]])
    ctx = _ctx(tmp_path, cloud=cloud)
    policy = helpers_deploy.resource(
        "module.organization",
        "google_org_policy_policy",
        "default",
        [helpers_deploy.instance({"name": kept[0]}, kept[0])],
    )
    _local_state(ctx, helpers_deploy.state_doc([policy]))
    assert _check(ctx, "pre.org_policies").status == _S.DONE


def test_preflight_fails_on_a_failed_check(tmp_path):
    assert _check(_ctx(tmp_path), "pre.preflight").status == _S.DONE
    cloud = conftest.FakeCloud(projects={})
    verdict = _check(_ctx(tmp_path / "b", cloud=cloud), "pre.preflight")
    assert verdict.status == _S.PENDING
    assert "project.state" in verdict.detail
    assert verdict.results


def test_manual_steps_count_a_recorded_confirmation(tmp_path):
    ctx = _ctx(tmp_path)
    verdict = _check(ctx, "pre.super_admin")
    assert verdict.status == _S.UNKNOWN
    assert "Super Admin" in verdict.detail
    ctx.confirmed("pre.super_admin", "manual", verdict.detail)
    assert _check(ctx, "pre.super_admin").status == _S.DONE
    assert _check(ctx, "pre.project_quota").status == _S.UNKNOWN


# Stage 0.


def test_render_pending_then_done(tmp_path):
    ctx = _ctx(tmp_path)
    verdict = _check(ctx, "s0.render")
    assert verdict.status == _S.PENDING
    assert "terraform.tfvars" in verdict.detail
    _run(stage0.RENDER, ctx)
    assert _check(ctx, "s0.render").status == _S.DONE
    ctx.answers = helpers.minimal_answers(region="us-central1")
    assert _check(ctx, "s0.render").status == _S.PENDING


def test_render_blocks_on_a_foreign_phase_file(tmp_path):
    ctx = _ctx(tmp_path)
    _write(ctx.workspace("0") / phase.FILENAME, 'bootstrap_user = "x"\n')
    ctx.invalidate()
    assert _check(ctx, "s0.render").status == _S.BLOCKED


def test_render_notices_another_engine(tmp_path):
    ctx = _ctx(tmp_path)
    _run(stage0.RENDER, ctx)
    link = ctx.workspace("0") / "variables.tf"
    link.unlink()
    link.symlink_to(tmp_path / "elsewhere.tf")
    verdict = _check(ctx, "s0.render")
    assert verdict.status == _S.PENDING
    assert "variables.tf" in verdict.detail


def test_ready_blocks_on_environment_problems(tmp_path):
    ctx = _ctx(tmp_path, environ={"CLOUDSDK_CONFIG": str(tmp_path / "gc")})
    verdict = _check(ctx, "s0.ready")
    assert verdict.status == _S.BLOCKED
    assert verdict.detail == " ".join(ctx.terraform.child_env.problems)


def test_ready_accepts_an_imported_workload(tmp_path, repo):
    answers = helpers.minimal_answers(
        imports={"0-bootstrap": {_WORKLOAD: helpers_deploy.WORKLOAD}}
    )
    verdict = _check(_ctx(tmp_path, answers=answers), "s0.ready")
    assert verdict.status == _S.DONE
    assert helpers_deploy.WORKLOAD in verdict.detail


def test_ready_needs_billing_or_a_pre_created_workload(tmp_path):
    ctx = _ctx(tmp_path)
    ctx._preflight = model.Preflight((), billing_access=False)
    verdict = _check(ctx, "s0.ready")
    assert verdict.status == _S.PENDING
    assert "StellarEngine-tst" in (verdict.remedy or "")
    ctx._preflight = model.Preflight((), billing_access=None)
    assert _check(ctx, "s0.ready").status == _S.UNKNOWN


def test_ready_records_the_workload_name(tmp_path):
    name = helpers_deploy.WORKLOAD
    ctx = _ctx(
        tmp_path, ["organizations/999/locations/us-east4/workloads/x", name]
    )
    _run(stage0.READY, ctx)
    assert ctx.answers.imports["0-bootstrap"][_WORKLOAD] == name
    saved = helpers.load_answers(ctx.home)
    assert saved.imports["0-bootstrap"][_WORKLOAD] == name
    imports = ctx.workspace("0") / "0-bootstrap-imports.tf"
    assert name in imports.read_text()
    # The first answer names another organization, so the prompt asks again.
    assert isinstance(ctx.prompter, prompts.ScriptedPrompter)
    assert len(ctx.prompter.notes) == 1


def test_ready_blocks_a_final_phase_before_the_first_apply(tmp_path):
    # The lab's first apply ran in final mode by accident; a fresh
    # environment in the final phase has no step that runs the first apply.
    answers = helpers.minimal_answers(
        stage0_phase="final",
        imports={"0-bootstrap": {_WORKLOAD: helpers_deploy.WORKLOAD}},
    )
    ctx = _ctx(tmp_path, answers=answers)
    _run(stage0.RENDER, ctx)
    back = "stellar init --prefix tst --set stage0_phase=bootstrap"
    verdict = _check(ctx, "s0.ready")
    assert verdict.status == _S.BLOCKED
    assert "first Stage 0 apply has not run" in verdict.detail
    assert back in (verdict.remedy or "")
    verdict = _check(ctx, "s0.remote_providers")
    assert verdict.status == _S.PENDING
    assert back in (verdict.remedy or "")
    assert "s0.apply_bootstrap" not in (verdict.remedy or "")
    # Once the first apply wrote the remote providers file, the phase holds.
    _write(
        ctx.env.fast_config / "providers" / workspace_lib.BOOTSTRAP_PROVIDERS,
        _REMOTE_PROVIDERS,
    )
    ctx.invalidate()
    assert _check(ctx, "s0.ready").status == _S.DONE
    assert "s0.apply_bootstrap" not in (
        _check(ctx, "s0.remote_providers").remedy or ""
    )


def test_ready_never_sends_an_applied_stage0_back_to_bootstrap(tmp_path):
    # A new home with the same answers lacks fast-config, while the bucket
    # holds the state of earlier applies, or cannot be read.
    answers = helpers.minimal_answers(
        stage0_phase="final",
        imports={"0-bootstrap": {_WORKLOAD: helpers_deploy.WORKLOAD}},
    )
    ctx = _ctx(tmp_path, answers=answers)
    _run(stage0.RENDER, ctx)
    _fake(ctx).objects[(_BUCKET, probe_lib.REMOTE_OBJECT)] = api.ObjectData(
        _bytes(helpers_deploy.project_state(298)), 17
    )
    ctx.invalidate()
    assert _check(ctx, "s0.ready").status == _S.DONE
    _unreadable_remote(ctx)
    assert _check(ctx, "s0.ready").status == _S.DONE


def test_apply_workload_refuses_a_workspace_rendered_again(tmp_path):
    # The workspace was deleted and rendered again: the local backend and
    # no state, while the bucket holds the Stage 0 state with the workload.
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, runner=runner, yes=True)
    _run(stage0.RENDER, ctx)
    _fake(ctx).objects[(_BUCKET, probe_lib.REMOTE_OBJECT)] = api.ObjectData(
        _bytes(_workload_state(298)), 17
    )
    ctx.invalidate()
    assert _check(ctx, "s0.apply_workload").status == _S.PENDING
    with pytest.raises(model.BlockedError, match="local backend") as raised:
        _run(stage0.APPLY_WORKLOAD, ctx)
    assert f"gs://{_BUCKET}" in raised.value.reason
    assert "--only s0.remote_providers" in (raised.value.remedy or "")
    assert runner.calls == []


def test_ready_accepts_a_final_phase_after_the_migration(tmp_path):
    answers = helpers.minimal_answers(
        stage0_phase="final",
        imports={"0-bootstrap": {_WORKLOAD: helpers_deploy.WORKLOAD}},
    )
    ctx = _ctx(tmp_path, answers=answers)
    _migrated(ctx)
    assert _check(ctx, "s0.ready").status == _S.DONE


def test_ready_cannot_tell_without_the_remote_state(tmp_path):
    ctx = _ctx(tmp_path)
    _migrated(ctx)
    _unreadable_remote(ctx)
    verdict = _check(ctx, "s0.ready")
    assert verdict.status == _S.UNKNOWN
    assert "denied" in verdict.detail


def test_ready_stops_without_a_name_or_a_terminal(tmp_path):
    with pytest.raises(model.StoppedError):
        _run(stage0.READY, _ctx(tmp_path, [""]))
    with pytest.raises(model.InputRequiredError) as raised:
        _run(stage0.READY, _ctx(tmp_path / "b", interactive=False))
    assert "stellar init --prefix tst --set" in (raised.value.remedy or "")


def test_apply_workload_targets_the_workload(tmp_path):
    runner = conftest.FakeTerraform()
    helpers_deploy.script_plan(
        runner, helpers.plan_fixture("targeted-workload")
    )
    ctx = _ctx(tmp_path, [True], runner=runner)
    assert _check(ctx, "s0.apply_workload").status == _S.PENDING
    _run(stage0.RENDER, ctx)
    _run(stage0.APPLY_WORKLOAD, ctx)
    plans = [args for args, _ in runner.calls if args[0] == "plan"]
    assert f"-target={_WORKLOAD}" in plans[0]
    assert any(args[0] == "apply" for args, _ in runner.calls)
    _local_state(ctx, _workload_state())
    assert _check(ctx, "s0.apply_workload").status == _S.DONE


def test_apply_workload_targets_the_folder_without_a_regime(tmp_path, repo):
    answers = helpers.minimal_answers(
        compliance={"regime": "COMPLIANCE_REGIME_UNSPECIFIED"}
    )
    ctx = _ctx(tmp_path, answers=answers)
    folder = repo.no_compliance_folder_address()
    assert folder in _check(ctx, "s0.apply_workload").detail
    assert not _BY_ID["s0.allow_bq"].applies_when(ctx)
    folder_state = helpers_deploy.resource(
        folder,
        "google_folder",
        "folder",
        [helpers_deploy.instance({"name": "folders/1"}, 0)],
    )
    _local_state(ctx, helpers_deploy.state_doc([folder_state]))
    assert _check(ctx, "s0.apply_workload").status == _S.DONE


def test_allow_bq_checks_the_folder_policy(tmp_path):
    ctx = _ctx(tmp_path)
    _local_state(ctx, _workload_state())
    assert _check(ctx, "s0.allow_bq").status == _S.DONE
    _fake(ctx).restriction = api.ServiceRestriction(
        allowed=("compute.googleapis.com",)
    )
    verdict = _check(ctx, "s0.allow_bq")
    assert verdict.status == _S.PENDING
    assert "bigquery.googleapis.com" in verdict.detail


def test_allow_bq_is_done_once_the_state_enables_the_services(tmp_path):
    ctx = _ctx(tmp_path)
    services = helpers_deploy.resource(
        "module.automation-project",
        "google_project_service",
        "project_services",
        [helpers_deploy.instance({}, service) for service in _BQ],
    )
    workload = _workload_state()
    doc = helpers_deploy.state_doc([*workload["resources"], services])
    _local_state(ctx, doc)
    _fake(ctx).restriction = api.ServiceRestriction(
        allowed=("compute.googleapis.com",)
    )
    verdict = _check(ctx, "s0.allow_bq")
    assert verdict.status == _S.DONE
    assert "already enables" in verdict.detail


def test_allow_bq_stays_pending_when_the_state_lacks_a_service(tmp_path):
    ctx = _ctx(tmp_path)
    services = helpers_deploy.resource(
        "module.automation-project",
        "google_project_service",
        "project_services",
        [helpers_deploy.instance({}, _BQ[0])],
    )
    workload = _workload_state()
    doc = helpers_deploy.state_doc([*workload["resources"], services])
    _local_state(ctx, doc)
    _fake(ctx).restriction = api.ServiceRestriction(
        allowed=("compute.googleapis.com",)
    )
    assert _check(ctx, "s0.allow_bq").status == _S.PENDING


def _blocked_bq(ctx, **restriction):
    _local_state(ctx, _workload_state())
    _fake(ctx).restriction = api.ServiceRestriction(
        allowed=("compute.googleapis.com",), **restriction
    )
    _fake(ctx).workloads[helpers_deploy.WORKLOAD] = api.WorkloadInfo(
        helpers_deploy.WORKLOAD, "IL5", "folders/222", _BQ
    )


def test_allow_bq_run_allows_the_services(tmp_path):
    ctx = _ctx(tmp_path, yes=True)
    _blocked_bq(ctx)
    _run(stage0.ALLOW_BQ, ctx)
    assert _fake(ctx).writes == [
        ("restrict_allowed_resources", helpers_deploy.WORKLOAD)
    ]
    assert _check(ctx, "s0.allow_bq").status == _S.DONE


def test_allow_bq_stops_when_the_policy_lags(tmp_path):
    ctx = _ctx(tmp_path, yes=True)
    _blocked_bq(ctx, denied=_BQ)
    with pytest.raises(model.StoppedError, match="has not applied"):
        _run(stage0.ALLOW_BQ, ctx)


def test_apply_bootstrap_resumes_from_run_state(tmp_path):
    ctx = _ctx(tmp_path)
    assert _check(ctx, "s0.apply_bootstrap").status == _S.PENDING
    _run(stage0.RENDER, ctx)
    _local_state(ctx, helpers_deploy.project_state(3))
    assert _check(ctx, "s0.apply_bootstrap").status == _S.UNKNOWN
    _record_apply(ctx, "s0.apply_bootstrap")
    assert _check(ctx, "s0.apply_bootstrap").status == _S.DONE
    # Later Stage 0 steps raise the serial, which keeps the step done.
    _local_state(ctx, helpers_deploy.project_state(4))
    assert _check(ctx, "s0.apply_bootstrap").status == _S.DONE
    (ctx.workspace("0") / "terraform.tfvars").write_text("# changed\n")
    verdict = _check(ctx, "s0.apply_bootstrap")
    assert verdict.status == _S.PENDING
    assert "inputs changed" in verdict.detail


def test_apply_bootstrap_ends_with_the_migration(tmp_path):
    ctx = _ctx(tmp_path)
    assert _BY_ID["s0.apply_bootstrap"].applies_when(ctx)
    _migrated(ctx)
    assert not _BY_ID["s0.apply_bootstrap"].applies_when(ctx)


def test_remote_providers_copy_after_a_backup(tmp_path):
    ctx = _ctx(tmp_path)
    _run(stage0.RENDER, ctx)
    verdict = _check(ctx, "s0.remote_providers")
    assert verdict.status == _S.PENDING
    assert "s0.apply_bootstrap" in (verdict.remedy or "")
    source = (
        ctx.env.fast_config / "providers" / workspace_lib.BOOTSTRAP_PROVIDERS
    )
    _write(source, _REMOTE_PROVIDERS)
    ctx.invalidate()
    _run(stage0.REMOTE_PROVIDERS, ctx)
    target = ctx.workspace("0") / workspace_lib.BOOTSTRAP_PROVIDERS
    assert target.read_text() == _REMOTE_PROVIDERS
    assert not target.is_symlink()
    assert conftest.mode(target) == 0o600
    (backup,) = ctx.env.plans.glob("0-bootstrap-providers.tf.local.*")
    assert "backend" not in backup.read_text()
    ctx.invalidate()
    assert _check(ctx, "s0.remote_providers").status == _S.DONE


def test_quota_project_of_user_credentials(tmp_path):
    ctx = _ctx(tmp_path)
    assert _BY_ID["s0.quota_project"].applies_when(ctx)
    verdict = _check(ctx, "s0.quota_project")
    assert verdict.status == _S.PENDING
    assert verdict.remedy == (
        "gcloud auth application-default set-quota-project tst-prod-iac-core-0"
    )
    _fake(ctx).adc = api.AdcInfo(api.PrincipalKind.USER, "tst-prod-iac-core-0")
    assert _check(ctx, "s0.quota_project").status == _S.DONE
    _fake(ctx).adc = api.AdcInfo(api.PrincipalKind.SERVICE_ACCOUNT, None)
    assert not _BY_ID["s0.quota_project"].applies_when(ctx)


def test_migrate_state_follows_the_probe(tmp_path):
    ctx = _ctx(tmp_path)
    verdict = _check(ctx, "s0.migrate_state")
    assert verdict.status == _S.PENDING
    assert "s0.remote_providers" in (verdict.remedy or "")
    _migrated(ctx)
    assert _check(ctx, "s0.migrate_state").status == _S.DONE
    _fake(ctx).objects[(_BUCKET, probe_lib.REMOTE_OBJECT)] = api.CloudError(
        "boom"
    )
    ctx.invalidate()
    assert _check(ctx, "s0.migrate_state").status == _S.UNKNOWN


def test_migrate_state_refuses_another_lineage(tmp_path):
    ctx = _ctx(tmp_path)
    _migrated(ctx)
    other = helpers_deploy.project_state(5, "99999999-9999-9999-9999-9999")
    ws = ctx.workspace("0")
    (ws / probe_lib.CACHED_BACKEND).unlink()
    _local_state(ctx, other)
    verdict = _check(ctx, "s0.migrate_state")
    assert verdict.status == _S.BLOCKED
    assert "different lineages" in verdict.detail


def test_migrate_state_runs_the_init(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, runner=runner)
    _run(stage0.RENDER, ctx)
    _run(stage0.MIGRATE_STATE, ctx)
    assert [args[0] for args, _ in runner.calls] == ["init"]


def test_migrate_state_archives_a_stale_local_state(tmp_path):
    # A configured backend ignores the local file, so a plain init would
    # leave it, and the check could never turn done.
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, runner=runner)
    _run(stage0.RENDER, ctx)
    _migrated(ctx, serial=7)
    _local_state(ctx, helpers_deploy.project_state(5))
    verdict = _check(ctx, "s0.migrate_state")
    assert verdict.status == _S.PENDING
    assert "archived" in verdict.detail
    _run(stage0.MIGRATE_STATE, ctx)
    ctx.invalidate()
    assert _check(ctx, "s0.migrate_state").status == _S.DONE
    assert helpers_deploy.subcommands(runner) == ["init"]
    (archive,) = ctx.env.plans.glob("terraform.tfstate.before-archive.*")
    assert json.loads(archive.read_text())["serial"] == 5


def test_migrate_state_refuses_a_newer_stale_local_state(tmp_path):
    ctx = _ctx(tmp_path)
    _migrated(ctx, serial=7)
    _local_state(ctx, helpers_deploy.project_state(9))
    verdict = _check(ctx, "s0.migrate_state")
    assert verdict.status == _S.BLOCKED
    assert "local serial 9" in verdict.detail


def test_migrate_state_asks_about_another_engine_commit(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, runner=runner, interactive=False)
    _run(stage0.RENDER, ctx)
    ctx.record(stage0.REMOTE_PROVIDERS.id).status = _S.DONE
    ctx.run_state.engine.path = str(ctx.repo.root)
    ctx.run_state.engine.commit = "f" * 40
    report = engine.run(ctx, [stage0.MIGRATE_STATE])
    assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
    assert "Plan and apply with this engine?" in (report.reason or "")
    assert runner.calls == []
    # The init never ran, so run-state keeps the earlier engine.
    assert ctx.run_state.engine.commit == "f" * 40


def test_phase_final_updates_the_answers_and_the_workspace(tmp_path):
    ctx = _ctx(tmp_path)
    _run(stage0.RENDER, ctx)
    phase_file = ctx.workspace("0") / phase.FILENAME
    assert phase_file.is_file()
    assert _check(ctx, "s0.phase_final").status == _S.PENDING
    _run(stage0.PHASE_FINAL, ctx)
    assert ctx.answers.stage0_phase == "final"
    assert helpers.load_answers(ctx.home).stage0_phase == "final"
    assert not phase_file.exists()
    ctx.invalidate()
    assert _check(ctx, "s0.phase_final").status == _S.DONE


def test_apply_final_needs_the_exact_recorded_state(tmp_path):
    answers = helpers.minimal_answers(stage0_phase="final")
    ctx = _ctx(tmp_path, answers=answers)
    _run(stage0.RENDER, ctx)
    _migrated(ctx, serial=298, generation=17)
    assert _check(ctx, "s0.apply_final").status == _S.UNKNOWN
    # A saved run-state that never saw the lineage still cannot tell, as
    # during a deploy, which saves run-state before its first step.
    ctx.save()
    assert _check(ctx, "s0.apply_final").status == _S.UNKNOWN
    # The bootstrap apply recorded the lineage, so stellar wrote the state.
    _record_apply(ctx, "s0.apply_bootstrap")
    assert _check(ctx, "s0.apply_final").status == _S.PENDING
    _record_apply(ctx, "s0.apply_final")
    verdict = _check(ctx, "s0.apply_final")
    assert verdict.status == _S.DONE
    assert "serial 298" in verdict.detail
    # Another write of the remote state makes the step unknown.
    _migrated(ctx, serial=298, generation=18)
    assert _check(ctx, "s0.apply_final").status == _S.UNKNOWN


def test_deploy_asks_before_planning_a_state_it_did_not_write(tmp_path):
    # A final Stage 0 state that someone applied by hand, with no
    # run-state: `--yes --non-interactive` must stop instead of planning.
    answers = helpers.minimal_answers(stage0_phase="final")
    runner = conftest.FakeTerraform()
    ctx = _ctx(
        tmp_path, answers=answers, runner=runner, yes=True, interactive=False
    )
    _run(stage0.RENDER, ctx)
    _migrated(ctx)
    report = engine.run(ctx, [stage0.APPLY_FINAL], catalog=_STEPS)
    assert isinstance(report.stop, model.InputRequiredError)
    assert "s0.apply_final cannot tell" in report.stop.reason
    assert deploy_cmd.exit_code(report) == 4
    assert runner.calls == []
    assert ctx.run_state.updated is not None


def test_apply_bootstrap_follows_the_workload_lineage(tmp_path):
    # The targeted workload apply starts the lineage of a fresh Stage 0
    # state, so the first full apply is pending, not unknown.
    ctx = _ctx(tmp_path)
    _run(stage0.RENDER, ctx)
    _local_state(ctx, _workload_state(serial=2))
    assert _check(ctx, "s0.apply_bootstrap").status == _S.UNKNOWN
    _record_apply(ctx, "s0.apply_workload")
    verdict = _check(ctx, "s0.apply_bootstrap")
    assert verdict.status == _S.PENDING
    assert "records no s0.apply_bootstrap" in verdict.detail
    # A state of another lineage, such as one applied by hand, is unknown.
    other = helpers_deploy.project_state(
        4, "99999999-9999-9999-9999-999999999999"
    )
    _local_state(ctx, other)
    verdict = _check(ctx, "s0.apply_bootstrap")
    assert verdict.status == _S.UNKNOWN
    assert "without stellar" in verdict.detail


def test_apply_final_reads_the_remote_state(tmp_path):
    ctx = _ctx(tmp_path)
    _migrated(ctx)
    _fake(ctx).objects[(_BUCKET, probe_lib.REMOTE_OBJECT)] = (
        api.AccessDeniedError("no")
    )
    ctx.invalidate()
    verdict = _check(ctx, "s0.apply_final")
    assert verdict.status == _S.UNKNOWN
    assert "remote state" in verdict.detail


def test_verify_needs_the_outputs_and_the_remote_state(tmp_path):
    ctx = _ctx(tmp_path)
    _migrated(ctx)
    verdict = _check(ctx, "s0.verify")
    assert verdict.status == _S.PENDING
    for name in workspace_lib.OUTPUT_LINKS[paths.RESMAN]:
        _write(ctx.env.fast_config / name, "{}")
    assert _check(ctx, "s0.verify").status == _S.DONE


# Stage 1.


def test_outputs_download_from_the_outputs_bucket(tmp_path):
    bucket = "tst-prod-iac-core-outputs-0"
    names = workspace_lib.OUTPUT_LINKS[paths.RESMAN]
    cloud = conftest.FakeCloud(
        objects={(bucket, name): api.ObjectData(b"{}", 1) for name in names}
    )
    cloud.objects[(bucket, names[0], None)] = api.AccessDeniedError("ADC")
    cloud.objects[(bucket, names[0], _RESMAN_SA)] = api.ObjectData(b"x", 2)
    ctx = _ctx(tmp_path, cloud=cloud)
    assert _check(ctx, "s1.outputs").status == _S.PENDING
    _run(stage1.OUTPUTS, ctx)
    assert (ctx.env.fast_config / names[0]).read_bytes() == b"x"
    assert conftest.mode(ctx.env.fast_config / names[1]) == 0o600
    assert _check(ctx, "s1.outputs").status == _S.DONE


def test_outputs_block_when_stage0_wrote_none(tmp_path):
    with pytest.raises(model.BlockedError, match="does not exist"):
        _run(stage1.OUTPUTS, _ctx(tmp_path))


def test_stage1_render_links_the_outputs(tmp_path):
    ctx = _ctx(tmp_path)
    for name in workspace_lib.OUTPUT_LINKS[paths.RESMAN]:
        _write(ctx.env.fast_config / name, "{}")
    verdict = _check(ctx, "s1.render")
    assert verdict.status == _S.PENDING
    _run(stage1.RENDER, ctx)
    assert _check(ctx, "s1.render").status == _S.DONE


def _external_grant(**billing):
    return helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, **billing}
    )


def test_billing_grant_applies_to_an_external_grant(tmp_path):
    ctx = _ctx(tmp_path, answers=_external_grant(no_iam=True))
    assert not stage1.BILLING_GRANT.applies_when(ctx)
    ctx.answers = _external_grant(no_iam=True, external_grant=True)
    assert stage1.BILLING_GRANT.applies_when(ctx)
    assert "outside Terraform" in stage1.BILLING_GRANT.explain(ctx)


def test_billing_grant_reads_and_grants_billing_user(tmp_path):
    answers = _external_grant(no_iam=True, external_grant=True)
    ctx = _ctx(tmp_path, answers=answers)
    verdict = _check(ctx, "s1.billing_grant")
    assert verdict.status == _S.PENDING
    assert "roles/billing.user" in (verdict.remedy or "")
    _run(stage1.BILLING_GRANT, ctx)
    assert _fake(ctx).writes == [
        (
            "add_billing_account_binding",
            conftest.BILLING,
            "roles/billing.user",
            f"serviceAccount:{_RESMAN_SA}",
        )
    ]
    assert _check(ctx, "s1.billing_grant").status == _S.DONE
    _fake(ctx).billing_policy = api.CloudError("denied")
    assert _check(ctx, "s1.billing_grant").status == _S.UNKNOWN


def _tenant_answers(**fields):
    return helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "no_iam": True},
        resman={
            "envs": {"Prod": {}},
            "tenants": {"ten1": {"descriptive_name": "tenant-1"}},
        },
        **fields,
    )


def test_precreate_tenants_lists_the_projects(tmp_path):
    ctx = _ctx(tmp_path, answers=_tenant_answers())
    assert stage1.PRECREATE_TENANTS.applies_when(ctx)
    verdict = _check(ctx, "s1.precreate_tenants")
    assert verdict.status == _S.PENDING
    card = verdict.remedy or ""
    assert "tst-prod-ten1-iac-core-0" in card
    # The printed `--set` line parses back to the import of the project.
    line = next(line for line in card.splitlines() if "main-projects" in line)
    data = answers_lib.apply_sets({}, [shlex.split(line)[-1]])
    address = (
        'module.tenant-self-main-projects["Prod-ten1"]'
        ".google_project.project[0]"
    )
    assert data == {
        "imports": {paths.RESMAN: {address: "tst-prod-ten1-main-0"}}
    }


def test_precreate_tenants_done_when_imported_and_linked(tmp_path):
    imports = {
        "1-resman": {
            'module.tenant-self-iac-projects["Prod-ten1"]'
            ".google_project.project[0]": "tst-prod-ten1-iac-core-0",
            'module.tenant-self-main-projects["Prod-ten1"]'
            ".google_project.project[0]": "tst-prod-ten1-main-0",
        }
    }
    ctx = _ctx(tmp_path, answers=_tenant_answers(imports=imports))
    assert _check(ctx, "s1.precreate_tenants").status == _S.DONE
    _fake(ctx).project_link = api.ProjectBilling(None, False)
    assert _check(ctx, "s1.precreate_tenants").status == _S.PENDING


def test_precreate_tenants_skips_other_billing_paths(tmp_path):
    override = {"project": "my-project", "billing_project": "my-project"}
    ctx = _ctx(tmp_path, answers=_tenant_answers(billing_override=override))
    assert not stage1.PRECREATE_TENANTS.applies_when(ctx)


def test_apply_identity_follows_the_billing_override(tmp_path):
    override = {"project": "my-project", "billing_project": "my-project"}
    ctx = _ctx(tmp_path, answers=_tenant_answers(billing_override=override))
    assert stage1.APPLY.identity(ctx) == model.Identity.DEPLOYER
    _fake(ctx).project_link = api.CloudError("not found")
    assert stage1.APPLY.identity(ctx) == model.Identity.BILLING_LINKER
    ctx.answers = _tenant_answers()
    assert stage1.APPLY.identity(ctx) == model.Identity.DEPLOYER


def test_stage1_apply_records_the_remote_state(tmp_path):
    bucket = "tst-prod-iac-core-resman-0"
    cloud = conftest.FakeCloud()
    ctx = _ctx(tmp_path, cloud=cloud)
    ctx.workspace("1").mkdir(parents=True)
    assert _check(ctx, "s1.apply").status == _S.PENDING
    cloud.objects[(bucket, probe_lib.REMOTE_OBJECT)] = api.ObjectData(
        _bytes(helpers_deploy.project_state(4)), 9
    )
    ctx.save()
    _record_apply(ctx, "s1.apply", "1")
    assert _check(ctx, "s1.apply").status == _S.DONE


def test_stage1_apply_stops_on_environment_problems(tmp_path):
    # Only s0.ready reports the environment, and Stage 1 never runs it.
    empty = tmp_path / "gcloud"
    empty.mkdir()
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, runner=runner, environ={"CLOUDSDK_CONFIG": str(empty)})
    ctx.record(stage1.RENDER.id).status = _S.DONE
    report = engine.run(ctx, [stage1.APPLY])
    assert deploy_cmd.exit_code(report) == common.EXIT_STOPPED
    assert "CLOUDSDK_CONFIG" in (report.reason or "")
    assert runner.calls == []


def test_stage1_verify_needs_the_stage2_inputs(tmp_path):
    ctx = _ctx(tmp_path)
    assert _check(ctx, "s1.verify").status == _S.PENDING
    for name in workspace_lib.RESMAN_OUTPUTS:
        _write(ctx.env.fast_config / name, "{}")
    assert _check(ctx, "s1.verify").status == _S.DONE


def test_checks_never_write(tmp_path):
    """Checks read only, so `stellar status` changes nothing."""
    runner = conftest.FakeTerraform()
    ctx = _ctx(tmp_path, runner=runner)
    before = sorted(str(path) for path in tmp_path.rglob("*"))
    for step in _STEPS:
        if step.applies_when(ctx):
            engine.check(ctx, step)
    assert sorted(str(path) for path in tmp_path.rglob("*")) == before
    assert not _fake(ctx).writes
    assert runner.calls == []


# Sync tests: the ported scripts and the documentation.


def test_apis_explanation_lists_the_enable_services_script(tmp_path, repo):
    script = (repo.bootstrap_dir / "enableServices.sh").read_text()
    names = re.search(r'list_of_services="([^"]+)"', script)
    assert names is not None
    text = pre.APIS.explain(_ctx(tmp_path))
    for name in names.group(1).split():
        assert f"{name}.googleapis.com" in text
    assert "monitoring.googleapis.com" in text


def test_granted_roles_follow_the_set_iam_sample(repo):
    sample = json.loads((repo.bootstrap_dir / "setIAM.yaml.sample").read_text())
    roles = {binding["role"] for binding in sample["bindings"]}
    assert roles == set(repo.required_roles())


def test_allow_bq_services_are_those_of_the_script():
    script = (conftest.REPO_ROOT / "scripts/allow_bq.sh").read_text()
    allowed = set(re.findall(r'echo "  - ([\w.]+)"', script))
    checked = {*cloud_ops.BQ_SERVICES, cloud_ops.BQ_TRANSFER_SERVICE}
    # Stage 0 enables only the checked services, so the script allows
    # three more; a change to the script shows up here.
    assert allowed - checked == {
        "bigqueryconnection.googleapis.com",
        "bigquerydatapolicy.googleapis.com",
        "bigquerymigration.googleapis.com",
    }


def test_remedies_match_the_errors_the_ddg_quotes():
    ddg = (conftest.REPO_ROOT / "docs/ddg.md").read_text()
    quoted = re.search(r"`(Request is disallowed by [^`]+)`", ddg)
    assert quoted is not None
    failure = remedies.Failure("s0.apply_final", "0", "apply", quoted.group(1))
    found = remedies.match(failure, stage0.APPLY_REMEDIES)
    assert found is remedies.REMEDIES[remedies.BQ_RESTRICT_SERVICE_USAGE]
    denied = re.search(r"`(Permission '[^`]+' denied)`", ddg)
    assert denied is not None
    output = (
        f"Error 403: {denied.group(1)} on "
        "tst-prod-bootstrap-0@tst-prod-iac-core-0.iam.gserviceaccount.com"
    )
    failure = remedies.Failure("s0.apply_final", "0", "apply", output)
    found = remedies.match(failure, stage0.APPLY_REMEDIES)
    assert found is remedies.REMEDIES[remedies.SA_PROPAGATION]
    assert "set-quota-project" in ddg
    assert (
        "set-quota-project"
        in remedies.REMEDIES[remedies.ADC_QUOTA_PROJECT].text
    )


def test_readme_names_every_command_and_step():
    readme = (conftest.REPO_ROOT / "cli/README.md").read_text()
    for step in _STEPS:
        assert f"`{step.id}`" in readme, step.id
    # The `--yes` flag also answers the questions of these two steps.
    yes = re.search(r"The `--yes` flag answers[^\n]*(\n  [^\n]*)*", readme)
    assert yes is not None
    for step_id in ("pre.iam_roles", "s0.allow_bq"):
        assert f"`{step_id}`" in yes.group(0), step_id
    for command in (
        "stellar guide",
        "stellar status",
        "stellar deploy",
        "stellar iam snapshot",
        "stellar iam diff",
        "stellar iam restore",
    ):
        assert command in readme, command
