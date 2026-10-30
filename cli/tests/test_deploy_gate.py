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

"""Tests for the review of a saved plan: the organization IAM review."""

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine.config import answers as answers_lib
from stellar_engine.deploy import apply
from stellar_engine.deploy import gate
from stellar_engine.deploy import model
from stellar_engine.wizard import prompts

_S = model.StepStatus
Script = helpers_deploy.Script
_ROLE = helpers_deploy.IAM_ROLE
_GROUP = helpers_deploy.ADMINS
_OLD = helpers_deploy.OLD_MEMBER
_STEP = Script([_S.DONE]).step("s0.test", stage="0")
_asked = helpers_deploy.asked
_pipeline = helpers_deploy.pipeline_ctx
_calls = helpers_deploy.calls
_policy = helpers_deploy.org_policy


_KEEP = "keep the removed grants in the answers and plan again"
_TYPED = (
    f"This apply changes the IAM policy of organization {conftest.ORG_ID}. "
    f"Type {conftest.ORG_ID} to confirm:"
)


def _gate_doc(*members):
    return helpers_deploy.plan_doc(
        [helpers_deploy.binding(_ROLE, members or [_GROUP])]
    )


_PROJECT = "tst-prod-iac-core-0"


def _owners():
    """Returns the authoritative owner binding of a pre-created project."""
    return helpers_deploy.change(
        "module.automation-project.google_project_iam_binding."
        'authoritative["roles/owner"]',
        "google_project_iam_binding",
        ("create",),
        after={
            "project": _PROJECT,
            "role": "roles/owner",
            "members": ["serviceAccount:sa@example.com"],
        },
    )


def _imported():
    """Returns answers that import the pre-created automation project."""
    return helpers.minimal_answers(
        imports={"0-bootstrap": {conftest.AUTOMATION_ADDRESS: _PROJECT}}
    )


class TestIamGate:
    def _run(self, tmp_path, replies, docs=None, **kwargs):
        cloud = kwargs.pop("cloud", None) or conftest.FakeCloud(
            policy=_policy(_OLD)
        )
        ctx, runner = _pipeline(
            tmp_path, docs or [_gate_doc()], replies, cloud=cloud, **kwargs
        )
        return ctx, runner, cloud

    def test_confirm_needs_the_typed_org_id(self, tmp_path):
        ctx, _, _ = self._run(tmp_path, ["confirm", conftest.ORG_ID, True])
        applied = apply.apply_pipeline(ctx, _STEP, "0")
        assert applied.applied
        asked = _asked(ctx)
        assert asked[:2] == ["How do you want to go on?", _TYPED]
        (snapshot,) = ctx.run_state.iam.snapshots
        assert snapshot.reason == "gate"
        snapshot_path = ctx.env.root / snapshot.path
        assert snapshot_path.parent == ctx.env.iam_snapshots
        assert snapshot_path.is_file()
        gate = [
            item
            for item in ctx.record("s0.test").confirmations
            if item.kind == "iam_gate"
        ]
        assert [item.decision for item in gate] == ["confirmed"]
        assert "1 removed" in gate[0].detail
        output = helpers_deploy.output(ctx)
        assert "Organization IAM review" in output
        assert _OLD in output

    def test_keep_is_offered_first(self, tmp_path):
        class Recorder(prompts.ScriptedPrompter):
            def __init__(self, answers):
                super().__init__(answers)
                self.choices = []

            def select(self, message, choices, default=None):
                self.choices.append(choices)
                return super().select(message, choices, default)

        cloud = conftest.FakeCloud(policy=_policy(_OLD))
        ctx, _ = _pipeline(tmp_path, [_gate_doc()], cloud=cloud)
        prompter = Recorder(["abort"])
        ctx.prompter = prompter
        with pytest.raises(model.StoppedError):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert prompter.choices == [
            [_KEEP, "confirm", "skip the review", "abort"]
        ]

    def test_skip_is_recorded(self, tmp_path):
        ctx, _, _ = self._run(
            tmp_path, ["skip the review", conftest.ORG_ID, True]
        )
        apply.apply_pipeline(ctx, _STEP, "0")
        (gate,) = [
            item
            for item in ctx.record("s0.test").confirmations
            if item.kind == "iam_gate"
        ]
        assert gate.decision == "skipped"

    def test_a_wrong_org_id_stops(self, tmp_path):
        ctx, runner, _ = self._run(tmp_path, ["confirm", "12345"])
        with pytest.raises(model.StoppedError, match="did not match"):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert not _calls(runner, "apply")

    def test_abort_stops(self, tmp_path):
        ctx, runner, _ = self._run(tmp_path, ["abort"])
        with pytest.raises(model.StoppedError, match="IAM review"):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert not _calls(runner, "apply")

    def test_yes_never_answers_the_review(self, tmp_path):
        ctx, _, _ = self._run(tmp_path, [], interactive=False, yes=True)
        with pytest.raises(model.InputRequiredError):
            apply.apply_pipeline(ctx, _STEP, "0")
        ctx, runner, _ = self._run(
            tmp_path / "tty", ["confirm", conftest.ORG_ID], yes=True
        )
        apply.apply_pipeline(ctx, _STEP, "0")
        # --yes answered only the apply question.
        assert _asked(ctx) == ["How do you want to go on?", _TYPED]
        assert _calls(runner, "apply")

    def test_nothing_removed_passes_silently(self, tmp_path):
        cloud = conftest.FakeCloud(policy=_policy(_GROUP))
        ctx, _, _ = self._run(tmp_path, [True], cloud=cloud)
        assert apply.apply_pipeline(ctx, _STEP, "0").applied
        (question,) = _asked(ctx)
        assert question.startswith("Apply ")
        assert len(ctx.run_state.iam.snapshots) == 1

    def test_keep_writes_the_overrides_and_plans_again(self, tmp_path):
        ctx, runner, _ = self._run(
            tmp_path,
            [_KEEP, True],
            docs=[_gate_doc(), _gate_doc(_GROUP, _OLD)],
        )
        assert apply.apply_pipeline(ctx, _STEP, "0").applied
        assert len(_calls(runner, "plan")) == 2
        overrides = ctx.answers.overrides["0-bootstrap"]["iam"]
        assert overrides == {_ROLE: [_OLD]}
        saved = answers_lib.load(ctx.env.answers)
        assert saved.overrides == ctx.answers.overrides
        assert (ctx.workspace("0") / "terraform.tfvars").is_file()
        kept = [
            item.decision
            for item in ctx.record("s0.test").confirmations
            if item.kind == "iam_gate"
        ]
        assert kept == ["kept"]

    def test_a_changed_etag_repeats_the_review(self, tmp_path):
        cloud = conftest.FakeCloud(policy=_policy(_OLD))

        class Changer(prompts.ScriptedPrompter):
            """Changes the live policy once, after the first review."""

            changed = False

            def confirm(self, message, default=True):
                answer = super().confirm(message, default)
                if message.startswith("Apply") and not self.changed:
                    self.changed = True
                    cloud.policy = _policy(_OLD, etag="BwYBBBBBBBB=")
                return answer

        replies = ["confirm", conftest.ORG_ID, True] * 2
        ctx, runner = _pipeline(tmp_path, [_gate_doc()], cloud=cloud)
        ctx.prompter = Changer(replies)
        assert apply.apply_pipeline(ctx, _STEP, "0").applied
        assert len(ctx.run_state.iam.snapshots) == 2
        assert ctx.prompter.asked.count("How do you want to go on?") == 2
        assert len(_calls(runner, "apply")) == 1

    def test_a_policy_that_keeps_changing_stops(self, tmp_path):
        class Changing(conftest.FakeCloud):
            """Returns a new etag on every read of the live policy."""

            reads = 0

            def get_org_iam_policy(self, org_id):
                self.reads += 1
                self.policy = _policy(_OLD, etag=f"BwY{self.reads}=")
                return super().get_org_iam_policy(org_id)

        rounds = gate._MAX_ETAG_ROUNDS
        replies = ["confirm", conftest.ORG_ID, True] * rounds
        ctx, runner, _ = self._run(tmp_path, replies, cloud=Changing())
        with pytest.raises(model.StoppedError, match="keeps changing"):
            apply.apply_pipeline(ctx, _STEP, "0")
        snapshots = ctx.run_state.iam.snapshots
        assert len(snapshots) == rounds
        assert len({snapshot.etag for snapshot in snapshots}) == rounds
        files = {ctx.env.root / snapshot.path for snapshot in snapshots}
        assert len(files) == rounds
        assert all(path.is_file() for path in files)
        asked = _asked(ctx)
        assert asked.count("How do you want to go on?") == rounds
        assert sum(q.startswith("Apply ") for q in asked) == rounds
        assert not _calls(runner, "apply")

    def test_owners_of_imported_projects_are_listed(self, tmp_path):
        doc = _gate_doc()
        doc["resource_changes"].append(_owners())
        ctx, _, _ = self._run(
            tmp_path, ["abort"], docs=[doc], answers=_imported()
        )
        with pytest.raises(model.StoppedError):
            apply.apply_pipeline(ctx, _STEP, "0")
        output = helpers_deploy.output(ctx)
        assert f"roles/owner on {_PROJECT}" in output
        assert "Only serviceAccount:sa@example.com keep the role" in output

    def test_owners_need_the_review_without_org_removals(self, tmp_path):
        # The lab case: the overrides keep every live grant, so only the
        # owners of the pre-created projects change.
        doc = _gate_doc()
        doc["resource_changes"].append(_owners())
        cloud = conftest.FakeCloud(policy=_policy(_GROUP))
        replies = ["confirm", conftest.ORG_ID, True]
        ctx, runner, _ = self._run(
            tmp_path, replies, docs=[doc], cloud=cloud, answers=_imported()
        )
        assert apply.apply_pipeline(ctx, _STEP, "0").applied
        asked = _asked(ctx)
        assert asked[0] == "How do you want to go on?"
        assert "replaces the owners of 1 imported projects" in asked[1]
        assert f"roles/owner on {_PROJECT}" in helpers_deploy.output(ctx)
        (gate_record,) = [
            item
            for item in ctx.record("s0.test").confirmations
            if item.kind == "iam_gate"
        ]
        assert "1 imported project owners" in gate_record.detail
        assert _calls(runner, "apply")

    def test_yes_never_answers_owners_outside_the_review(self, tmp_path):
        # A plan without organization IAM, as a Stage 1 plan.
        doc = helpers_deploy.plan_doc([_owners()])
        ctx, runner, _ = self._run(
            tmp_path,
            [],
            docs=[doc],
            answers=_imported(),
            interactive=False,
            yes=True,
        )
        with pytest.raises(model.InputRequiredError, match="owners"):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert not _calls(runner, "apply")
        ctx, runner, _ = self._run(
            tmp_path / "tty", [True, True], docs=[doc], answers=_imported()
        )
        assert apply.apply_pipeline(ctx, _STEP, "0").applied
        assert _asked(ctx)[0] == (
            "The apply replaces the owners of 1 imported projects. "
            "Apply anyway?"
        )
        (record,) = ctx.record("s0.test").confirmations
        assert (record.kind, record.detail) == ("owners", _PROJECT)
        assert not ctx.run_state.iam.snapshots

    def test_unknown_members_block(self, tmp_path):
        doc = _gate_doc()
        doc["resource_changes"][0]["change"]["after_unknown"] = {
            "members": True
        }
        ctx, runner, _ = self._run(tmp_path, [], docs=[doc])
        with pytest.raises(model.FailedError, match=gate.IAM_UNKNOWN):
            apply.apply_pipeline(ctx, _STEP, "0")
        assert not _calls(runner, "apply")
