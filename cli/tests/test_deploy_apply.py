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

"""Tests for the apply pipeline: init, plan, guards, apply and state."""

import json

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine import workspace as workspace_lib
from stellar_engine.commands import deploy as deploy_cmd
from stellar_engine.deploy import apply
from stellar_engine.deploy import engine
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import run_state
from stellar_engine.deploy.catalog import common as catalog_common
from stellar_engine.gcp import api
from stellar_engine.terraform import guards
from stellar_engine.wizard import prompts

_S = model.StepStatus
_K = model.StepKind
Script = helpers_deploy.Script
_ROLE = helpers_deploy.IAM_ROLE
_GROUP = helpers_deploy.ADMINS
_STEP = Script([_S.DONE]).step("s0.test", stage="0")
_ctx = helpers_deploy.scripted_ctx
_asked = helpers_deploy.asked
_pipeline = helpers_deploy.pipeline_ctx
_calls = helpers_deploy.calls
_policy = helpers_deploy.org_policy
_folder = helpers_deploy.folder_change


def _org_policy_resource():
    """Returns a change that replaces the whole organization IAM policy."""
    return helpers_deploy.change(
        "google_organization_iam_policy.x",
        guards.ORG_IAM_POLICY_TYPE,
        ("update",),
        before={"org_id": conftest.ORG_ID, "policy_data": "{}"},
        after={"org_id": conftest.ORG_ID, "policy_data": '{"bindings": []}'},
    )


class TestPipeline:
    def test_no_changes_apply_nothing(self, tmp_path):
        doc = helpers_deploy.plan_doc(applyable=False)
        ctx, runner = _pipeline(tmp_path, [doc])
        applied = apply.apply_pipeline(ctx, _STEP, "0")
        assert not applied.applied
        assert helpers_deploy.subcommands(runner) == [
            "init",
            "plan",
            "show",
            "show",
        ]
        record = ctx.record("s0.test")
        assert record.state == apply.current_state(ctx, "0")
        assert record.tfvars_sha256 == apply.inputs_sha256(ctx, "0")
        assert record.artifacts.plan == str(
            applied.files.tfplan.relative_to(ctx.env.root)
        )
        assert json.loads(applied.files.json.read_text()) == doc
        assert applied.files.text.read_text() == "plan text\n"
        assert conftest.mode(applied.files.json) == 0o600
        assert ctx.run_state.engine.path == str(ctx.repo.root)
        assert ctx.run_state.engine.commit == helpers_deploy.COMMIT

    def test_apply_of_the_saved_plan(self, tmp_path):
        ctx, runner = _pipeline(
            tmp_path, [helpers_deploy.plan_doc([_folder()])], [True]
        )
        applied = apply.apply_pipeline(ctx, _STEP, "0")
        assert applied.applied
        (apply_args,) = _calls(runner, "apply")
        assert apply_args == (
            "apply",
            "-no-color",
            "-input=false",
            str(applied.files.tfplan),
        )
        assert _asked(ctx) == [f"Apply {applied.files.tfplan.name}?"]
        assert ctx.record("s0.test").summary["create"] == 1

    def test_yes_applies_without_a_terminal(self, tmp_path):
        ctx, runner = _pipeline(
            tmp_path,
            [helpers_deploy.plan_doc([_folder()])],
            interactive=False,
            yes=True,
        )
        assert apply.apply_pipeline(ctx, _STEP, "0").applied
        assert _calls(runner, "apply")

    def test_declined_apply(self, tmp_path):
        ctx, runner = _pipeline(
            tmp_path, [helpers_deploy.plan_doc([_folder()])], [False]
        )
        with pytest.raises(model.StoppedError):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert not _calls(runner, "apply")

    def test_targets_go_to_the_plan_only(self, tmp_path):
        doc = helpers.plan_fixture("targeted-workload")
        cloud = conftest.FakeCloud(
            accounts=[api.ServiceAccount("x@y.iam.gserviceaccount.com", True)]
        )
        ctx, runner = _pipeline(tmp_path, [doc], [True], cloud=cloud)
        target = ctx.repo.assured_workload().address
        apply.apply_pipeline(ctx, _STEP, "0", targets=(target,))
        (plan,) = _calls(runner, "plan")
        assert f"-target={target}" in plan
        (apply_args,) = _calls(runner, "apply")
        assert not any(
            arg.startswith(("-target", "-var")) for arg in apply_args
        )

    def test_disabled_accounts_block_untargeted_applies(self, tmp_path):
        email = (
            "tst-prod-bootstrap-0@tst-prod-iac-core-0.iam.gserviceaccount.com"
        )
        cloud = conftest.FakeCloud(accounts=[api.ServiceAccount(email, True)])
        ctx, runner = _pipeline(tmp_path, [], cloud=cloud)
        with pytest.raises(model.BlockedError) as raised:
            apply.apply_pipeline(ctx, _STEP, "0")
        assert f"gcloud iam service-accounts enable {email}" in (
            raised.value.remedy or ""
        )
        assert runner.calls == []

    def test_drift_reverts_need_the_operator(self, tmp_path):
        doc = helpers.plan_fixture("stage0-org-policy-drift")
        ctx, runner = _pipeline(tmp_path, [doc], [False])
        with pytest.raises(model.StoppedError, match="org_policy_drift_revert"):
            apply.apply_pipeline(ctx, _STEP, "0")
        (question,) = _asked(ctx)
        assert "org_policy_drift_revert findings. Apply anyway?" in question
        assert not _calls(runner, "apply")

    def test_the_snapshot_comes_before_the_findings(self, tmp_path):
        # A redeploy plan refreshes the bindings and reverts drift only.
        doc = helpers.plan_fixture("stage0-org-policy-drift")
        doc["resource_changes"].append(
            helpers_deploy.binding(_ROLE, [_GROUP], actions=("no-op",))
        )
        cloud = conftest.FakeCloud(policy=_policy(_GROUP))
        ctx, runner = _pipeline(tmp_path, [doc], [False], cloud=cloud)
        with pytest.raises(model.StoppedError, match="org_policy_drift_revert"):
            apply.apply_pipeline(ctx, _STEP, "0")
        (question,) = _asked(ctx)
        assert "org_policy_drift_revert findings" in question
        (snapshot,) = ctx.run_state.iam.snapshots
        assert snapshot.reason == "gate"
        assert (ctx.env.root / snapshot.path).is_file()
        assert not _calls(runner, "apply")

    def test_yes_never_answers_findings(self, tmp_path):
        doc = helpers.plan_fixture("stage0-org-policy-drift")
        ctx, _ = _pipeline(tmp_path, [doc], interactive=False, yes=True)
        with pytest.raises(model.InputRequiredError):
            apply.apply_pipeline(ctx, _STEP, "0")

    def test_a_whole_policy_change_needs_the_operator(self, tmp_path):
        # The review models bindings and audit configs only, so this
        # change gets no review and `--yes` must not apply it.
        doc = helpers_deploy.plan_doc([_org_policy_resource()])
        ctx, runner = _pipeline(tmp_path, [doc], interactive=False, yes=True)
        with pytest.raises(
            model.InputRequiredError, match="iam_policy_replace"
        ):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert not _calls(runner, "apply")
        assert not ctx.run_state.iam.snapshots

    def test_a_whole_policy_change_declined(self, tmp_path):
        doc = helpers_deploy.plan_doc([_org_policy_resource()])
        ctx, runner = _pipeline(tmp_path, [doc], [False])
        with pytest.raises(model.StoppedError, match="iam_policy_replace"):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert _asked(ctx) == [
            "The plan has 1 iam_policy_replace findings. Apply anyway?"
        ]
        assert not _calls(runner, "apply")

    def test_guard_blocks_become_command_errors(self, tmp_path):
        project = helpers_deploy.change(
            "module.automation-project.google_project.project[0]",
            "google_project",
            ("delete",),
            before={"project_id": "tst-prod-iac-core-0"},
            module_address="module.automation-project",
        )
        ctx, runner = _pipeline(tmp_path, [helpers_deploy.plan_doc([project])])
        with pytest.raises(model.CommandError) as raised:
            apply.apply_pipeline(ctx, _STEP, "0")
        assert raised.value.command == "plan checks"
        assert raised.value.findings == ("protected_delete",)
        assert raised.value.plan is not None
        assert not _calls(runner, "apply")
        assert (
            ctx.record("s0.test")
            .findings[0]
            .startswith("BLOCK protected_delete")
        )

    def test_unreadable_plans_block(self, tmp_path):
        ctx, _ = _pipeline(tmp_path, [{"format_version": "2.0"}])
        with pytest.raises(model.CommandError) as raised:
            apply.apply_pipeline(ctx, _STEP, "0")
        assert raised.value.findings == ("plan_integrity",)

    @pytest.mark.parametrize("command", ["plan", "apply"])
    def test_terraform_failures(self, tmp_path, command):
        runner = conftest.FakeTerraform()
        if command == "plan":
            runner.results["plan"] = [helpers_deploy.completed("Error: x", 1)]
        else:
            helpers_deploy.script_plan(
                runner, helpers_deploy.plan_doc([_folder()])
            )
            runner.results["apply"] = [helpers_deploy.completed("Error: x", 1)]
        ctx, _ = _pipeline(tmp_path, [], [True], runner=runner)
        with pytest.raises(model.CommandError) as raised:
            apply.apply_pipeline(ctx, _STEP, "0")
        assert (raised.value.command, raised.value.output) == (
            command,
            "Error: x",
        )
        assert raised.value.log is not None and raised.value.log.is_file()

    def test_final_applies_are_recorded(self, tmp_path):
        ctx, _ = _pipeline(
            tmp_path, [helpers_deploy.plan_doc([_folder()])], [True]
        )
        apply.apply_pipeline(ctx, _STEP, "0")
        assert ctx.run_state.stage0.final_applied

    def test_a_final_plan_without_changes_is_recorded(self, tmp_path):
        # The lab applied the final phase by hand, so the first deploy plan
        # changes nothing, and the answers must still refuse a return to
        # the bootstrap phase.
        ctx, _ = _pipeline(tmp_path, [helpers_deploy.plan_doc(applyable=False)])
        assert not apply.apply_pipeline(ctx, _STEP, "0").applied
        assert ctx.run_state.stage0.final_applied
        targeted = helpers_deploy.plan_doc(applyable=False)
        ctx, _ = _pipeline(tmp_path / "targeted", [targeted])
        apply.apply_pipeline(ctx, _STEP, "0", targets=("google_folder.x",))
        assert not ctx.run_state.stage0.final_applied

    def test_bootstrap_applies_are_not_final(self, tmp_path):
        doc = helpers_deploy.plan_doc([_folder()], bootstrap_user=conftest.USER)
        ctx, _ = _pipeline(tmp_path, [doc], [True])
        apply.apply_pipeline(ctx, _STEP, "0")
        assert not ctx.run_state.stage0.final_applied

    def test_local_state_is_saved_before_the_apply(self, tmp_path):
        ctx, _ = _pipeline(
            tmp_path, [helpers_deploy.plan_doc([_folder()])], [True]
        )
        state = helpers_deploy.state_bytes(helpers_deploy.project_state(3))
        (ctx.workspace("0") / probe_lib.STATE_FILE).write_bytes(state)
        apply.apply_pipeline(ctx, _STEP, "0")
        (backup,) = ctx.env.plans.glob("terraform.tfstate.before-s0.test.*")
        assert backup.read_bytes() == state
        assert conftest.mode(backup) == 0o600


def _relink(ctx, name, target):
    """Points one workspace link elsewhere, as another engine's render."""
    link = ctx.workspace("0") / name
    link.unlink()
    link.symlink_to(target)


class TestEngineGuard:
    def test_links_into_another_engine_block(self, tmp_path):
        # A render from another checkout left the links there; an
        # `--only` rerun must not plan that code under this engine.
        ctx, runner = _pipeline(tmp_path, [])
        ctx.run_state.engine.path = "/elsewhere/engine"
        _relink(ctx, "variables.tf", tmp_path / "elsewhere" / "variables.tf")
        with pytest.raises(model.BlockedError, match="variables") as raised:
            apply.apply_pipeline(ctx, _STEP, "0")
        assert "stellar deploy --stage 0" in (raised.value.remedy or "")
        assert runner.calls == []
        # Only an init after a clean link check records the engine.
        assert ctx.run_state.engine.path == "/elsewhere/engine"

    def test_a_module_manifest_of_another_engine_blocks_the_init(
        self, tmp_path
    ):
        # The links match this engine, but the last init recorded the
        # modules of another checkout, which a plain init would keep.
        runner = conftest.FakeTerraform()
        ctx = _linked(tmp_path, runner=runner)
        workspace = ctx.workspace("0")
        manifest = helpers.module_manifest(workspace, tmp_path / "old")
        with pytest.raises(
            model.BlockedError, match=r"modules\.json"
        ) as raised:
            apply.init_workspace(ctx, _STEP, "0")
        assert "stellar deploy --stage 0" in (raised.value.remedy or "")
        assert runner.calls == []
        # The render step of the remedy moves it, and init then runs.
        engine.render(ctx, "0")
        assert not manifest.exists()
        (backup,) = ctx.env.plans.glob("modules.json.0-bootstrap.*")
        # The console wraps long lines, so compare the words.
        printed = " ".join(helpers_deploy.output(ctx).split())
        assert f"so the render moved it to {backup}." in printed
        apply.init_workspace(ctx, _STEP, "0")
        assert [args for args, _ in runner.calls] == [
            ("init", "-no-color", "-input=false")
        ]

    def test_an_unlinked_workspace_blocks_the_init(self, tmp_path):
        runner = conftest.FakeTerraform()
        ctx = _ctx(tmp_path, runner=runner)
        with pytest.raises(model.BlockedError, match="modules"):
            apply.init_workspace(ctx, _STEP, "0")
        assert runner.calls == []

    def test_another_engine_path_needs_the_operator(self, tmp_path):
        # The render relinked the workspace to this engine.
        no_changes = helpers_deploy.plan_doc(applyable=False)
        ctx, runner = _pipeline(tmp_path, [no_changes], [False])
        ctx.run_state.engine.path = "/elsewhere/engine"
        ctx.run_state.engine.commit = helpers_deploy.COMMIT
        with pytest.raises(model.StoppedError, match="declined the engine"):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert _asked(ctx) == ["Plan and apply with this engine?"]
        assert "/elsewhere/engine" in helpers_deploy.output(ctx)
        assert runner.calls == []
        ctx.prompter = prompts.ScriptedPrompter([True])
        apply.apply_pipeline(ctx, _STEP, "0")
        assert ctx.run_state.engine.path == str(ctx.repo.root)

    def test_another_commit_needs_the_operator(self, tmp_path):
        ctx, runner = _pipeline(tmp_path, [], [False])
        ctx.run_state.engine.path = str(ctx.repo.root)
        ctx.run_state.engine.commit = "f" * 40
        with pytest.raises(model.StoppedError):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert _asked(ctx) == ["Plan and apply with this engine?"]
        assert runner.calls == []

    def test_another_commit_stops_without_a_terminal(self, tmp_path):
        ctx, runner = _pipeline(tmp_path, [], interactive=False, yes=True)
        ctx.run_state.engine.path = str(ctx.repo.root)
        ctx.run_state.engine.commit = "f" * 40
        with pytest.raises(model.InputRequiredError):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert _asked(ctx) == []
        assert runner.calls == []

    def test_dirty_checkouts_are_asked_once_per_run(self, tmp_path):
        no_changes = helpers_deploy.plan_doc(applyable=False)
        repo = helpers_deploy.FixedRepo(conftest.REPO_ROOT, dirty=True)
        ctx, _ = _pipeline(
            tmp_path, [no_changes, no_changes], [True], repo=repo, yes=True
        )
        apply.apply_pipeline(ctx, _STEP, "0")
        apply.apply_pipeline(ctx, _STEP, "0")
        assert _asked(ctx) == ["Plan and apply with this engine?"]
        (confirmation,) = ctx.record("s0.test").confirmations
        assert "uncommitted changes" in confirmation.detail


_REMOTE_PROVIDERS = """terraform {
  backend "gcs" {
    bucket = "tst-prod-iac-core-bootstrap-0"
  }
}
"""
_BUCKET = "tst-prod-iac-core-bootstrap-0"


def _remote_workspace(ctx, local=None):
    workspace = ctx.workspace("0")
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / workspace_lib.BOOTSTRAP_PROVIDERS).write_text(
        _REMOTE_PROVIDERS
    )
    if local is not None:
        (workspace / probe_lib.STATE_FILE).write_bytes(
            helpers_deploy.state_bytes(local)
        )
    return workspace


def _linked(tmp_path, **kwargs):
    """Returns a context with a linked Stage 0 workspace."""
    ctx = _ctx(tmp_path, **kwargs)
    helpers_deploy.link_workspace(ctx)
    return ctx


class TestInit:
    def test_local_backend_plain_init(self, tmp_path):
        runner = conftest.FakeTerraform()
        ctx = _linked(tmp_path, runner=runner)
        apply.init_workspace(ctx, _STEP, "0")
        assert [args for args, _ in runner.calls] == [
            ("init", "-no-color", "-input=false")
        ]

    def test_migrate_backs_up_and_forces_the_copy(self, tmp_path):
        runner = conftest.FakeTerraform()
        ctx = _linked(tmp_path, runner=runner)
        workspace = _remote_workspace(ctx, helpers_deploy.project_state(297))
        apply.init_workspace(ctx, _STEP, "0")
        assert [args for args, _ in runner.calls] == [
            (
                "init",
                "-no-color",
                "-input=false",
                "-migrate-state",
                "-force-copy",
            )
        ]
        (backup,) = ctx.env.plans.glob("terraform.tfstate.before-migrate.*")
        assert (
            backup.read_bytes()
            == (workspace / probe_lib.STATE_FILE).read_bytes()
        )
        migration = ctx.run_state.stage0.migration
        assert migration is not None
        assert migration.local is not None and migration.local.serial == 297
        assert migration.remote_before is None
        assert migration.backup == str(backup.relative_to(ctx.env.root))
        assert migration.remote_after is not None

    def test_archive_keeps_the_newer_remote_state(self, tmp_path):
        remote = helpers_deploy.state_bytes(helpers_deploy.project_state(299))
        cloud = conftest.FakeCloud(
            objects={
                (_BUCKET, probe_lib.REMOTE_OBJECT): api.ObjectData(remote, 12)
            }
        )
        runner = conftest.FakeTerraform()
        ctx = _linked(tmp_path, runner=runner, cloud=cloud)
        workspace = _remote_workspace(ctx, helpers_deploy.project_state(297))
        apply.init_workspace(ctx, _STEP, "0")
        assert [args for args, _ in runner.calls] == [
            ("init", "-no-color", "-input=false")
        ]
        assert (workspace / probe_lib.STATE_FILE).read_bytes() == b""
        (archive,) = ctx.env.plans.glob("terraform.tfstate.before-archive.*")
        assert json.loads(archive.read_text())["serial"] == 297

    def test_refusal_runs_nothing(self, tmp_path):
        other = helpers_deploy.project_state(
            299, "99999999-9999-9999-9999-999999999999"
        )
        cloud = conftest.FakeCloud(
            objects={
                (_BUCKET, probe_lib.REMOTE_OBJECT): api.ObjectData(
                    helpers_deploy.state_bytes(other), 12
                )
            }
        )
        runner = conftest.FakeTerraform()
        ctx = _linked(tmp_path, runner=runner, cloud=cloud)
        _remote_workspace(ctx, helpers_deploy.project_state(297))
        # The check of s0.migrate_state reports the same decision as
        # BLOCKED, so the run stops the same way, with exit status 4.
        with pytest.raises(
            model.BlockedError, match="different lineages"
        ) as raised:
            apply.init_workspace(ctx, _STEP, "0")
        assert "keep the right one" in (raised.value.remedy or "")
        assert runner.calls == []

    def test_stage1_plain_init(self, tmp_path):
        runner = conftest.FakeTerraform()
        ctx = _ctx(tmp_path, runner=runner)
        helpers_deploy.link_workspace(ctx, "1")
        apply.init_workspace(ctx, _STEP, "1-resman")
        assert [args for args, _ in runner.calls] == [
            ("init", "-no-color", "-input=false")
        ]

    def test_init_failure(self, tmp_path):
        runner = conftest.FakeTerraform(
            results={"init": [helpers_deploy.completed("Error: no", 1)]}
        )
        with pytest.raises(model.CommandError) as raised:
            apply.init_workspace(_linked(tmp_path, runner=runner), _STEP, "0")
        assert raised.value.command == "init"

    def test_environment_problems_block_the_init(self, tmp_path):
        runner = conftest.FakeTerraform()
        ctx = _linked(
            tmp_path,
            runner=runner,
            environ={"CLOUDSDK_CONFIG": str(tmp_path / "empty")},
        )
        with pytest.raises(model.BlockedError, match="CLOUDSDK_CONFIG"):
            apply.init_workspace(ctx, _STEP, "0")
        assert runner.calls == []


class TestStateAndInputs:
    def test_current_state_of_stage1(self, tmp_path):
        remote = helpers_deploy.state_bytes(helpers_deploy.project_state(8))
        cloud = conftest.FakeCloud(
            objects={
                ("tst-prod-iac-core-resman-0", probe_lib.REMOTE_OBJECT): (
                    api.ObjectData(remote, 21)
                )
            }
        )
        ctx = _ctx(tmp_path, cloud=cloud)
        found = apply.current_state(ctx, "1")
        assert (found.lineage, found.serial, found.remote_generation) == (
            helpers_deploy.LINEAGE,
            8,
            21,
        )

    def test_current_state_of_a_local_stage0(self, tmp_path):
        ctx = _ctx(tmp_path)
        workspace = ctx.workspace("0")
        workspace.mkdir(parents=True)
        (workspace / probe_lib.STATE_FILE).write_bytes(
            helpers_deploy.state_bytes(helpers_deploy.project_state(4))
        )
        found = apply.current_state(ctx, "0")
        assert (found.serial, found.remote_generation) == (4, None)

    def test_unreadable_remote_states_raise(self, tmp_path):
        bucket = "tst-prod-iac-core-resman-0"
        denied = api.AccessDeniedError("denied")
        cloud = conftest.FakeCloud(
            objects={
                (bucket, probe_lib.REMOTE_OBJECT): denied,
                (
                    bucket,
                    probe_lib.REMOTE_OBJECT,
                    "tst-prod-resman-0@tst-prod-iac-core-0.iam."
                    "gserviceaccount.com",
                ): denied,
            }
        )
        ctx = _ctx(tmp_path, cloud=cloud)
        with pytest.raises(api.CloudError, match="denied"):
            apply.current_state(ctx, "1-resman")

    def test_local_stage0_ignores_the_remote(self, tmp_path):
        cloud = conftest.FakeCloud(
            objects={(_BUCKET, probe_lib.REMOTE_OBJECT): api.CloudError("x")}
        )
        ctx = _ctx(tmp_path, cloud=cloud)
        found = apply.current_state(ctx, "0")
        assert found == run_state.StateRecord()

    def test_engine_hash_follows_the_commit_and_the_lock_file(self, tmp_path):
        ctx = _linked(tmp_path)
        clean = apply.engine_sha256(ctx, "0")
        assert clean is not None
        (ctx.workspace("0") / ".terraform.lock.hcl").write_text("# new\n")
        upgraded = apply.engine_sha256(ctx, "0")
        assert upgraded not in (None, clean)
        ctx.repo = helpers_deploy.FixedRepo(conftest.REPO_ROOT, "f" * 40)
        assert apply.engine_sha256(ctx, "0") not in (None, clean, upgraded)
        ctx.repo = helpers_deploy.FixedRepo(conftest.REPO_ROOT, dirty=True)
        assert apply.engine_sha256(ctx, "0") is None

    def test_an_apply_records_the_engine_hash(self, tmp_path):
        ctx, _ = _pipeline(tmp_path, [helpers_deploy.plan_doc(applyable=False)])
        apply.apply_pipeline(ctx, _STEP, "0")
        record = ctx.record("s0.test")
        assert record.engine_sha256 == apply.engine_sha256(ctx, "0")

    def test_a_failed_apply_records_the_state_it_left(self, tmp_path):
        doc = helpers_deploy.plan_doc([_folder()])
        ctx, runner = _pipeline(tmp_path, [doc, doc], [True, True])
        runner.results["apply"] = [helpers_deploy.completed("Error: x", 1)]
        # The fake runner writes no state, so the test writes the state
        # that the failed first apply left behind.
        (ctx.workspace("0") / probe_lib.STATE_FILE).write_bytes(
            helpers_deploy.state_bytes(helpers_deploy.project_state(3))
        )
        with pytest.raises(model.CommandError):
            apply.apply_pipeline(ctx, _STEP, "0")
        record = ctx.record("s0.test")
        assert record.state is None
        assert record.failed_state == run_state.StateRecord(
            lineage=helpers_deploy.LINEAGE, serial=3
        )
        # stellar wrote the lineage, so an apply step of the stage that
        # run-state does not record is pending, not unknown.
        verdict = catalog_common.applied_verdict(
            ctx, "s0.other", "0", exact=True
        )
        assert verdict.status == _S.PENDING
        apply.apply_pipeline(ctx, _STEP, "0")
        assert record.failed_state is None
        assert record.state is not None

    def test_inputs_hash_follows_the_inputs(self, tmp_path):
        ctx = _ctx(tmp_path)
        workspace = ctx.workspace("0")
        workspace.mkdir(parents=True)
        empty = apply.inputs_sha256(ctx, "0")
        (workspace / "terraform.tfvars").write_text('prefix = "tst"\n')
        with_tfvars = apply.inputs_sha256(ctx, "0")
        assert with_tfvars != empty
        (workspace / "main.tf").write_text("# not an input\n")
        assert apply.inputs_sha256(ctx, "0") == with_tfvars
        (workspace / "0-bootstrap-imports.tf").write_text("# imports\n")
        assert apply.inputs_sha256(ctx, "0") != with_tfvars


def test_a_rerun_after_an_apply_is_a_no_op(tmp_path):
    """A step whose check compares run-state with the state is resumable."""

    def check(ctx):
        record = ctx.record("s0.apply")
        done = (
            record.state is not None
            and record.state == apply.current_state(ctx, "0")
            and record.tfvars_sha256 == apply.inputs_sha256(ctx, "0")
        )
        return model.Verdict(_S.DONE if done else _S.PENDING, "checked")

    step = model.Step(
        id="s0.apply",
        stage="0",
        kind=_K.AUTO,
        title="Apply",
        doc_anchor="docs/ddg.md#stage-0---bootstrap",
        explain=lambda ctx: "Applies Stage 0.",
        check=check,
        run=lambda ctx: apply.apply_pipeline(ctx, step, "0"),
    )
    doc = helpers_deploy.plan_doc([_folder()])
    ctx, runner = _pipeline(tmp_path, [doc], [True])
    assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0
    calls = len(runner.calls)
    assert deploy_cmd.exit_code(engine.run(ctx, [step])) == 0
    assert len(runner.calls) == calls
