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

"""Initializes, plans and applies a stage workspace.

`apply_pipeline` is the only way a step applies Terraform. It checks the
Terraform environment, the workspace links, the engine and the stage
service accounts, initializes the workspace, plans to a file, saves the
plan as JSON and text, prints the summary and the guard findings, lets
`gate.confirm_apply` review the plan with the operator, and applies the
saved plan, never with `-target` or `-var`. A guard that blocks the plan
raises `model.CommandError`, so the engine matches the step's remedies
against its findings.

Stage 0 initializes as `probe.migrate_decision` decides, which moves its
state into the bootstrap bucket once the remote providers file is in the
workspace. `init_workspace` runs the same environment, link and engine
checks before that init. `current_state` and `inputs_sha256` tell a later
check whether an apply that run-state records still matches the stage,
and `engine_sha256` tells the plan guards whether the code changed.
"""

from collections.abc import Sequence
import dataclasses
import hashlib
import pathlib
import subprocess

from stellar_engine import fsutil
from stellar_engine import paths
from stellar_engine import workspace as workspace_lib
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import gate
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import api
from stellar_engine.render import imports as imports_lib
from stellar_engine.render import phase as phase_lib
from stellar_engine.terraform import guards
from stellar_engine.terraform import plan as plan_lib
from stellar_engine.terraform import runner as runner_lib
from stellar_engine.terraform import summary as summary_lib

_STAGE0 = "0"
# A review that keeps removed grants plans again; more rounds mean the
# policy keeps changing.
_MAX_REPLANS = 3
_TFVARS_PATTERNS = ("terraform.tfvars", "*.auto.tfvars", "*.auto.tfvars.json")
# The provider versions that `terraform init` selected for a workspace.
_LOCK_FILE = ".terraform.lock.hcl"


@dataclasses.dataclass(frozen=True)
class Applied:
    """What `apply_pipeline` did.

    Attributes:
        plan: The parsed plan.
        files: The saved plan files.
        applied: False when the plan changed nothing.
    """

    plan: plan_lib.Plan
    files: runner_lib.PlanFiles
    applied: bool


@dataclasses.dataclass(frozen=True)
class _Inputs:
    """What a plan read besides the state.

    Attributes:
        tfvars: `inputs_sha256` of the stage.
        engine: `engine_sha256` of the stage, or None when unknown.
    """

    tfvars: str
    engine: str | None


def inputs_sha256(ctx: model.Context, stage: str) -> str:
    """Returns the hash of the files that set a stage's inputs.

    The tfvars, the generated auto tfvars, the linked outputs of earlier
    stages and the import blocks; the plan guards compare it with the hash
    of the last apply to tell outside changes from changed inputs.

    Args:
        ctx: The deploy context.
        stage: Catalog stage `0` or `1`.
    """
    workspace = ctx.workspace(stage)
    names = {
        found.name
        for pattern in _TFVARS_PATTERNS
        for found in workspace.glob(pattern)
        if found.is_file()
    }
    imports = workspace / imports_lib.filename(paths.resolve_stage(stage))
    if imports.is_file():
        names.add(imports.name)
    digest = hashlib.sha256()
    for name in sorted(names):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update((workspace / name).read_bytes() + b"\0")
    return digest.hexdigest()


def engine_sha256(ctx: model.Context, stage: str) -> str | None:
    """Returns the hash of the engine commit and the provider lock file.

    The plan guards compare it with the hash of the last apply, because a
    new engine commit or provider versions that `init -upgrade` selected
    change a plan as much as new inputs do.

    Args:
        ctx: The deploy context.
        stage: Catalog stage `0` or `1`.

    Returns:
        The hash, or None when the checkout has no commit or uncommitted
        changes, which leave the code unknown.
    """
    provenance = ctx.repo.provenance()
    if provenance is None or provenance.dirty or not provenance.commit:
        return None
    digest = hashlib.sha256(provenance.commit.encode("utf-8") + b"\0")
    lock = fsutil.read_bytes_or_none(ctx.workspace(stage) / _LOCK_FILE)
    digest.update(lock or b"")
    return digest.hexdigest()


def current_state(ctx: model.Context, stage: str) -> run_state_lib.StateRecord:
    """Returns the state Terraform uses for a stage, without Terraform.

    Stage 0 reads the probe, local or remote; Stage 1 reads its remote
    state object. A check compares it with the state an apply recorded.

    Args:
        ctx: The deploy context.
        stage: Catalog stage `0` or `1`.

    Raises:
        api.CloudError: If the remote state cannot be read, which a check
            reports as UNKNOWN.
    """
    stage = model.catalog_stage(stage)
    if stage == _STAGE0:
        probe = ctx.stage0()
        summary = probe.readable_state()
        remote = probe.remote if probe.uses_remote else None
    else:
        target = probe_lib.backend(ctx.answers.prefix, stage)
        remote = probe_lib.read_remote(ctx.cloud, target)
        summary = remote.readable_summary(target)
    generation = remote.generation if remote else None
    if summary is None:
        return run_state_lib.StateRecord(remote_generation=generation)
    return summary.record(generation)


def _record_engine(ctx: model.Context) -> None:
    """Records the engine checkout that initialized the workspaces."""
    provenance = ctx.repo.provenance()
    ctx.run_state.engine = run_state_lib.EngineRecord(
        path=str(ctx.repo.root),
        commit=provenance.commit if provenance else None,
        dirty=provenance.dirty if provenance else False,
        terraform_version=ctx.tools.terraform_version() or "",
    )
    ctx.save()


def _links_guard(ctx: model.Context, stage: str) -> None:
    """Refuses a workspace whose links do not match this engine.

    Only the render step of a stage links the workspace, so a deploy that
    switched engines, or a rerun with `--only`, would otherwise run the
    previous engine's code under this engine's record. The check also
    covers the module manifest of the last init: a plain init keeps its
    records, so it would plan with the modules of the engine that wrote
    them, and the render moves it away.

    Raises:
        model.BlockedError: If `workspace.stale_links` finds a link to
            create or change, or a module manifest to move.
    """
    name = paths.resolve_stage(stage)
    remedy = (
        f"Run stellar deploy --stage {stage}, whose render step relinks "
        "the workspace."
    )
    try:
        stale = workspace_lib.stale_links(ctx.env, ctx.repo.root, name)
    except workspace_lib.WorkspaceError as error:
        raise model.BlockedError(str(error), remedy=remedy) from error
    if stale:
        raise model.BlockedError(
            f"The {name} workspace does not match a render from "
            f"{ctx.repo.root}: {model.named(stale)}.",
            remedy=remedy,
        )


def _engine_guard(ctx: model.Context, step: model.Step, stage: str) -> None:
    """Checks the workspace links and the engine of the last init.

    The engine record changes only through the init that follows this
    guard, so another engine path, another commit and uncommitted changes
    each need the operator's answer, once per run and checkout state.

    Raises:
        model.BlockedError: If the workspace links do not match this
            engine.
        model.StoppedError: If the operator declines the engine.
    """
    _links_guard(ctx, stage)
    recorded = ctx.run_state.engine
    root = str(ctx.repo.root)
    current = ctx.repo.provenance()
    commit = current.commit if current else None
    moved = bool(recorded.path) and recorded.path != root
    changed = bool(recorded.commit) and commit != recorded.commit
    dirty = bool(current and current.dirty)
    answered = f"engine {root} {commit} {dirty}"
    if not (moved or changed or dirty) or answered in ctx.answered:
        return
    before = f"engine commit {recorded.commit or 'none'}"
    if moved:
        before = f"the engine {recorded.path} at {before}"
    detail = (
        f"run-state records {before}; {root} is at {commit or 'no commit'}"
        + (" with uncommitted changes" if dirty else "")
    )
    ctx.say(detail)
    if not ctx.confirm("Plan and apply with this engine?"):
        raise model.StoppedError("The operator declined the engine.")
    ctx.answered.add(answered)
    ctx.confirmed(step.id, run_state_lib.ENGINE, detail)


def _accounts_guard(ctx: model.Context) -> None:
    """Refuses an untargeted apply while a stage service account is off."""
    found = cloud_ops.service_accounts_enabled(ctx)
    if found.enabled is False:
        raise model.BlockedError(
            f"Disabled stage service accounts: {', '.join(found.disabled)}.",
            remedy=found.remedy,
        )
    if found.enabled is None:
        ctx.say(f"Cannot check the stage service accounts: {found.error}")


def _backup_state(
    ctx: model.Context, workspace: pathlib.Path, step: str
) -> pathlib.Path | None:
    """Copies a non-empty local state into `plans/` and returns the copy."""
    data = fsutil.read_bytes_or_none(workspace / probe_lib.STATE_FILE)
    if not data:
        return None
    target = runner_lib.state_backup_path(
        ctx.env.plans, step=step, now=ctx.now()
    )
    fsutil.write_private(target, data)
    ctx.say(f"Saved the local state to {target}.")
    return target


def _record_migration(
    ctx: model.Context, probe: probe_lib.Probe, backup: pathlib.Path | None
) -> None:
    """Records the local and remote states before a migration or archive."""
    ctx.run_state.stage0.migration = run_state_lib.Migration(
        backup=ctx.relative(backup),
        local=probe.local.record() if probe.local else None,
        remote_before=_remote_record(probe.remote),
    )
    ctx.save()


def _remote_record(
    remote: probe_lib.RemoteState,
) -> run_state_lib.StateRecord | None:
    """Returns the remote state object as run-state records it, if any."""
    if not remote.exists or remote.summary is None:
        return None
    return remote.summary.record(remote.generation)


def _record_remote_after(ctx: model.Context) -> None:
    """Records the remote state object that a migration wrote."""
    ctx.invalidate()
    migration = ctx.run_state.stage0.migration
    if migration is not None:
        # An empty record still shows that the migration ran.
        remote = _remote_record(ctx.stage0().remote)
        migration.remote_after = remote or run_state_lib.StateRecord()
        ctx.save()


def _init_stage0(
    ctx: model.Context, tf: runner_lib.Terraform, workspace: pathlib.Path
) -> subprocess.CompletedProcess[str]:
    """Runs the init that `probe.migrate_decision` chooses.

    Raises:
        model.BlockedError: If the decision refuses, as the check of
            `s0.migrate_state` reports the same decision.
    """
    probe = ctx.stage0()
    decision = probe_lib.migrate_decision(probe)
    ctx.say(decision.reason)
    action = decision.action
    if action == probe_lib.MigrateAction.REFUSE:
        raise model.BlockedError(
            decision.reason, remedy=probe_lib.refusal_remedy(probe, decision)
        )
    if action == probe_lib.MigrateAction.MIGRATE:
        _record_migration(ctx, probe, _backup_state(ctx, workspace, "migrate"))
        completed = tf.init(workspace, migrate=True, force_copy=True)
        if completed.returncode == 0:
            _record_remote_after(ctx)
        return completed
    if action == probe_lib.MigrateAction.ARCHIVE:
        _record_migration(ctx, probe, _backup_state(ctx, workspace, "archive"))
        fsutil.atomic_write(
            workspace / probe_lib.STATE_FILE, b"", fsutil.PRIVATE_FILE_MODE
        )
    return tf.init(workspace)


def _before_terraform(ctx: model.Context, step: model.Step, stage: str) -> None:
    """Runs the checks that every init of a step needs first.

    Raises:
        model.BlockedError: If the Terraform environment has a problem or
            the workspace links do not match this engine.
        model.StoppedError: If the operator declines the engine.
    """
    ctx.require_terraform_env()
    _engine_guard(ctx, step, stage)


def _init(ctx: model.Context, tf: runner_lib.Terraform, stage: str) -> None:
    """Initializes a workspace and records the engine that ran the init."""
    workspace = ctx.workspace(stage)
    if stage == _STAGE0:
        completed = _init_stage0(ctx, tf, workspace)
    else:
        completed = tf.init(workspace)
    model.succeeded(completed, "init", log=tf.last_log)
    _record_engine(ctx)
    ctx.invalidate()


def init_workspace(ctx: model.Context, step: model.Step, stage: str) -> None:
    """Runs `terraform init -input=false` in a stage workspace.

    The Terraform environment, the workspace links and the engine are
    checked first, as before every plan. Stage 0 follows
    `probe.migrate_decision`, which migrates the state to the bootstrap
    bucket once the remote providers file is in place. Each init records
    the engine that ran it.

    Args:
        ctx: The deploy context.
        step: The step that initializes.
        stage: Catalog stage `0` or `1`.

    Raises:
        model.BlockedError: If the Terraform environment has a problem,
            the workspace links do not match this engine, or the Stage 0
            decision refuses.
        model.StoppedError: If the operator declines the engine.
        model.CommandError: If init fails.
    """
    stage = model.catalog_stage(stage)
    _before_terraform(ctx, step, stage)
    _init(ctx, ctx.terraform.for_step(stage, step.id), stage)


def apply_pipeline(
    ctx: model.Context,
    step: model.Step,
    stage: str,
    *,
    targets: Sequence[str] = (),
) -> Applied:
    """Initializes, plans, reviews and applies a stage.

    Every apply follows one path: the environment, link, engine and
    service account checks, init, `plan -out`, `show -json` and `show`
    saved under `plans/`, the summary and guard findings, the organization
    IAM snapshot and review when the plan manages organization IAM, a
    confirmation per CONFIRM finding, the routine apply question, a state
    backup, and the apply of the saved plan. A plan that changes nothing
    records the state and applies nothing. A failed apply records the
    state it left behind as the step's `failed_state`, so a rerun knows
    that stellar wrote its lineage.

    Args:
        ctx: The deploy context.
        step: The step that applies.
        stage: Catalog stage `0` or `1`.
        targets: `-target` addresses of a targeted plan.

    Returns:
        What was planned and whether it was applied.

    Raises:
        model.CommandError: If a Terraform command fails or a guard
            refuses the plan; the engine matches the step's remedies.
        model.DeployError: If a guard, the review or the operator stops.
    """
    stage = model.catalog_stage(stage)
    _before_terraform(ctx, step, stage)
    if not targets:
        _accounts_guard(ctx)
    tf = ctx.terraform.for_step(stage, step.id)
    _init(ctx, tf, stage)
    for _ in range(_MAX_REPLANS):
        try:
            return _plan_and_apply(ctx, tf, step, stage, tuple(targets))
        except gate.ReplanError:
            continue
    raise model.FailedError(
        f"{step.id} planned {_MAX_REPLANS} times, and the organization IAM "
        "review kept finding grants to keep."
    )


def _plan_and_apply(
    ctx: model.Context,
    tf: runner_lib.Terraform,
    step: model.Step,
    stage: str,
    targets: tuple[str, ...],
) -> Applied:
    """Plans once, then reviews and applies the saved plan."""
    workspace = ctx.workspace(stage)
    paths.make_private_dir(ctx.env.plans)
    files = tf.plan_files(ctx.env.plans)
    completed = tf.plan(workspace, files.tfplan, targets=targets)
    # The plan log holds the provider errors; `_show` writes two more logs.
    plan_log = tf.last_log
    model.succeeded(completed, "plan", log=plan_log)
    doc = _show(tf, workspace, files)
    inputs = _Inputs(inputs_sha256(ctx, stage), engine_sha256(ctx, stage))
    plan, findings = _evaluate(ctx, step, stage, doc, inputs, targets)
    _record_plan(ctx, step, files, plan_log, plan, findings)
    if plan is None or guards.blocks(findings):
        raise _blocked(plan, findings, plan_log)
    if not plan.applyable:
        _record_state(ctx, step, stage, inputs)
        _mark_final(ctx, stage, targets, plan)
        return Applied(plan, files, applied=False)
    gate.confirm_apply(ctx, step, stage, plan, files, findings)
    _backup_state(ctx, workspace, step.id)
    completed = tf.apply(workspace, files.tfplan)
    if completed.returncode != 0:
        _record_failed_state(ctx, step, stage)
    model.succeeded(completed, "apply", log=tf.last_log, plan=plan)
    _record_state(ctx, step, stage, inputs)
    _mark_final(ctx, stage, targets, plan)
    return Applied(plan, files, applied=True)


def _mark_final(
    ctx: model.Context,
    stage: str,
    targets: tuple[str, ...],
    plan: plan_lib.Plan,
) -> None:
    """Records that the final phase is in effect after a Stage 0 plan.

    An untargeted plan without `bootstrap_user` that was applied, or that
    had nothing to apply, shows that the final phase holds, which forbids
    returning to the bootstrap phase.
    """
    if (
        stage == _STAGE0
        and not targets
        and plan.variable(phase_lib.VARIABLE) is None
    ):
        ctx.run_state.stage0.final_applied = True
        ctx.save()


def _show(
    tf: runner_lib.Terraform,
    workspace: pathlib.Path,
    files: runner_lib.PlanFiles,
) -> dict:
    """Saves the plan as JSON and text beside the plan file."""
    try:
        doc = tf.show_json(workspace, files.tfplan)
        text = tf.show_text(workspace, files.tfplan)
    except runner_lib.TerraformError as error:
        raise model.command_error(error, "show") from error
    fsutil.write_private_json(files.json, doc)
    fsutil.write_private(files.text, text)
    return doc


def _evaluate(
    ctx: model.Context,
    step: model.Step,
    stage: str,
    doc: dict,
    inputs: _Inputs,
    targets: tuple[str, ...],
) -> tuple[plan_lib.Plan | None, list[guards.Finding]]:
    """Parses the plan and runs the guards; an unreadable plan blocks."""
    record = ctx.record(step.id)
    history = guards.HistoryView(
        final_applied=ctx.run_state.stage0.final_applied,
        last_tfvars_sha256=record.tfvars_sha256,
        tfvars_sha256=inputs.tfvars,
        last_engine_sha256=record.engine_sha256,
        engine_sha256=inputs.engine,
    )
    try:
        plan = plan_lib.parse(doc)
    except plan_lib.PlanError as error:
        return None, [guards.integrity_finding(error)]
    findings = guards.evaluate(
        plan,
        stage=stage,
        run_state=history,
        repo=ctx.repo,
        targeted_to=targets or None,
    )
    return plan, findings


def _record_plan(
    ctx: model.Context,
    step: model.Step,
    files: runner_lib.PlanFiles,
    log: pathlib.Path | None,
    plan: plan_lib.Plan | None,
    findings: list[guards.Finding],
) -> None:
    """Prints the plan summary and records the plan in run-state."""
    if plan is not None:
        summary_lib.render(ctx.console, plan, findings)
    else:
        for finding in findings:
            ctx.say(finding.line())
    record = ctx.record(step.id)
    record.artifacts = run_state_lib.Artifacts(
        plan=ctx.relative(files.tfplan),
        plan_json=ctx.relative(files.json),
        plan_text=ctx.relative(files.text),
        log=ctx.relative(log),
    )
    record.summary = plan_lib.summary(plan) if plan is not None else {}
    record.findings = [finding.label() for finding in findings]
    ctx.save()


def _blocked(
    plan: plan_lib.Plan | None,
    findings: list[guards.Finding],
    log: pathlib.Path | None,
) -> model.CommandError:
    """Returns the failure of a plan that a guard refused.

    Remedies match it by the findings' keys, such as the #15725 bucket fix.
    The log is the plan log, which the operator reads for the cause.
    """
    blocking = guards.blocks(findings)
    return model.CommandError(
        "plan checks",
        "\n".join(finding.line() for finding in blocking),
        plan=plan,
        findings=[finding.remedy_key or finding.key for finding in blocking],
        log=log,
    )


def _record_state(
    ctx: model.Context, step: model.Step, stage: str, inputs: _Inputs
) -> None:
    """Records the state, inputs and engine of a plan or apply."""
    ctx.invalidate()
    record = ctx.record(step.id)
    try:
        record.state = current_state(ctx, stage)
    except api.CloudError as error:
        # The step's check reports UNKNOWN until the state is readable.
        ctx.say(str(error))
        record.state = None
    record.failed_state = None
    record.tfvars_sha256 = inputs.tfvars
    record.engine_sha256 = inputs.engine
    ctx.save()


def _record_failed_state(
    ctx: model.Context, step: model.Step, stage: str
) -> None:
    """Records the state that a failed apply left behind.

    The step stays pending, but its lineage now shows that stellar wrote
    the state, so `catalog.common.applied_verdict` does not ask whether
    someone applied it by hand. A failed first apply starts that lineage.
    """
    ctx.invalidate()
    try:
        state = current_state(ctx, stage)
    except api.CloudError:
        # The rerun asks, because no record holds the lineage.
        return
    ctx.record(step.id).failed_state = state
    ctx.save()
