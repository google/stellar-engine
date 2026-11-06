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

"""Check helpers that the step modules of every catalog stage share.

They answer the questions that the prerequisites, Stage 0 and Stage 1 all
ask: whether a render or an apply is current, whether the first Stage 0
apply has run, which earlier stage outputs are missing, and how to apply a
stage by hand.
"""

from collections.abc import Sequence
import pathlib

from stellar_engine import paths
from stellar_engine import workspace as workspace_lib
from stellar_engine.deploy import apply
from stellar_engine.deploy import model
from stellar_engine.render import pipeline
from stellar_engine.terraform import runner as runner_lib

Status = model.StepStatus


def manual_apply(
    ctx: model.Context, stage: str, plan: str, targets: Sequence[str] = ()
) -> str:
    """Returns the manual init, plan and apply commands of a stage.

    Args:
        ctx: The deploy context.
        stage: Catalog stage `0` or `1`.
        plan: The plan file name under `plans/`, such as `s0.tfplan`.
        targets: `-target` addresses of a targeted plan.
    """
    commands = runner_lib.manual_apply(
        ctx.workspace(stage), ctx.env.plans / plan, targets
    )
    return ", then ".join(commands)


def _changed_files(changes: str) -> list[str]:
    """Returns the names of the files that a render diff changes."""
    return [
        pathlib.Path(line.removeprefix("--- ")).name
        for line in changes.splitlines()
        if line.startswith("--- ")
    ]


def render_verdict(ctx: model.Context, stage: str) -> model.Verdict:
    """Checks that a stage workspace matches the answers and this engine.

    The check compares the files a render writes, without writing, and
    the links that `workspace.sync` makes and the module manifest that it
    moves, through `workspace.stale_links`.

    Args:
        ctx: The deploy context.
        stage: Catalog stage `0` or `1`.
    """
    name = paths.resolve_stage(stage)
    try:
        changes = pipeline.diff(name, ctx.answers, ctx.repo, ctx.env, ctx.tools)
        links = workspace_lib.stale_links(ctx.env, ctx.repo.root, name)
    except pipeline.ERRORS as error:
        return model.Verdict(
            Status.BLOCKED,
            str(error),
            "Fix it, then rerun stellar deploy.",
        )
    stale = [*_changed_files(changes), *links]
    if stale:
        return model.Verdict(
            Status.PENDING,
            f"The render would change {model.named(stale)}.",
            f"Run stellar deploy, or stellar render --stage {stage}.",
        )
    return model.Verdict(
        Status.DONE, f"The {name} workspace matches the answers."
    )


def _lineage_recorded(ctx: model.Context, lineage: str | None) -> bool:
    """Returns whether a step record holds a state of this lineage.

    Terraform keeps the lineage for the life of a state, so a recorded
    lineage shows that stellar applied or planned that state, while a state
    that someone applied by hand or with another tool has a lineage that
    run-state never saw.
    """
    if lineage is None:
        return False
    return any(
        found is not None and found.lineage == lineage
        for record in ctx.run_state.steps.values()
        for found in (record.state, record.failed_state)
    )


def applied_verdict(
    ctx: model.Context, step_id: str, stage: str, *, exact: bool
) -> model.Verdict:
    """Checks that run-state records an apply that matches the state.

    An apply records the state it left behind and the hash of the stage
    inputs. The step is done while the inputs keep that hash and the state
    keeps the recorded lineage; `exact` also needs the same serial and
    remote generation, while a bootstrap apply only needs a serial that is
    not above the current one, because later Stage 0 steps raise it.

    A stage with a state but no recorded apply of the step is pending only
    when another step record holds the state's lineage, such as the
    targeted workload apply before the first Stage 0 apply. Any other
    state is unknown, in `stellar status` and `stellar deploy` alike, so
    the deploy asks before it plans a state that it did not write.

    Args:
        ctx: The deploy context.
        step_id: The apply step.
        stage: Catalog stage `0` or `1`.
        exact: Whether any later state write makes the step unknown.

    Raises:
        api.CloudError: If the remote state cannot be read, which the
            engine reports as UNKNOWN.
    """
    current = apply.current_state(ctx, stage)
    record = ctx.run_state.steps.get(step_id)
    recorded = record.state if record else None
    if record is None or recorded is None:
        if current.serial is None:
            return model.Verdict(Status.PENDING, "The stage has no state yet.")
        if not _lineage_recorded(ctx, current.lineage):
            return model.Verdict(
                Status.UNKNOWN,
                f"run-state records no apply in the lineage of the state at "
                f"{current}, so someone may have applied it without stellar.",
            )
        return model.Verdict(Status.PENDING, f"run-state records no {step_id}.")
    if record.tfvars_sha256 != apply.inputs_sha256(ctx, stage):
        return model.Verdict(
            Status.PENDING, "The stage inputs changed since the last apply."
        )
    moved = recorded.lineage != current.lineage or (
        recorded != current
        if exact
        else (recorded.serial or 0) > (current.serial or 0)
    )
    if moved:
        return model.Verdict(
            Status.UNKNOWN,
            f"The state is at {current}, but the last apply left {recorded}.",
        )
    return model.Verdict(Status.DONE, f"Applied at {current}.")


def first_apply_pending(ctx: model.Context) -> bool:
    """Returns whether no Stage 0 apply has created anything yet.

    The prerequisites apply until then: afterwards Stage 0 manages the
    organization IAM roles and owns the names that preflight checks. The
    remote providers file and the remote backend exist only after a first
    apply, so either one answers False before any state is read; a remote
    state that cannot be read must never turn the prerequisites back on.

    Args:
        ctx: The deploy context.
    """
    probe = ctx.stage0()
    if probe.outputs_providers or probe.providers_remote or probe.configured:
        return False
    return probe.local is None or probe.local.empty


def missing_outputs(ctx: model.Context, names: tuple[str, ...]) -> list[str]:
    """Returns the files under `fast-config/` that do not exist.

    Args:
        ctx: The deploy context.
        names: Paths relative to `fast-config/`.
    """
    return [
        name for name in names if not (ctx.env.fast_config / name).is_file()
    ]
