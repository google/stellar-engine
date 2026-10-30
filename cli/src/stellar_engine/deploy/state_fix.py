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

"""Adopts the Stage 0 log buckets that Terraform would replace.

A Stage 0 apply can time out while it creates the log buckets, which then
exist outside the state. Importing one hits provider bug #15725
(terraform-provider-google): the imported bucket stores its `project` as
`projects/<id>` while the configuration says `<id>`, so the next plan
replaces it. Bucket names stay reserved for 7 days after a delete, and the
logs go with the bucket. `fix_log_buckets` repeats the fix the lab applied
by hand: back up the state, import the missing buckets, strip the prefix
from their `project` in the pulled state, raise the serial, and push it.
"""

from collections.abc import Collection, Iterable, Mapping, Sequence
import dataclasses
import pathlib
import re
import shlex
from typing import Any

from stellar_engine import fsutil
from stellar_engine import naming
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.terraform import guards
from stellar_engine.terraform import runner as runner_lib

LOG_BUCKET_MODULE = "module.log-export-logbucket"
LOG_BUCKET_RESOURCE = f"{guards.LOG_BUCKET_TYPE}.bucket[0]"
# The `name` of the log export project in `0-bootstrap/log-export.tf`.
LOGGING_PROJECT_NAME = "audit-logs-0"
# The sink type whose destination is a log bucket in `0-bootstrap`.
LOGGING_SINK_TYPE = "logging"
# Names the logs, plans and state backups of the fix.
STEP = "bucket-fix"
_STAGE = "0"
_PROJECT = "project"
_PROJECT_PREFIX = "projects/"
_ADDRESS_RE = re.compile(
    rf'^{re.escape(LOG_BUCKET_MODULE)}\["(?P<sink>[^"]+)"\]\.'
)
# The fix in words, with the commands that `commands` prints in full.
MANUAL_FIX = (
    "Import each bucket and fix its project in the state, which stellar "
    "offers, or by hand after a state backup: terraform import "
    f"'{LOG_BUCKET_MODULE}[\"<sink>\"].{LOG_BUCKET_RESOURCE}' "
    "projects/<logging project>/locations/<region>/buckets/<sink>, then "
    "terraform state pull, set attributes.project of each bucket to the "
    "bare project ID, raise serial by 1, and terraform state push the file."
)


@dataclasses.dataclass(frozen=True)
class Bucket:
    """A Stage 0 log bucket.

    Attributes:
        sink: The log sink it receives, which names it.
        address: Its resource address.
        import_id: Its import ID,
            `projects/<project>/locations/<region>/buckets/<sink>`.
    """

    sink: str
    address: str
    import_id: str


def log_buckets(
    ctx: model.Context, sinks: Iterable[str] | None = None
) -> list[Bucket]:
    """Returns the log buckets of the deployment.

    Args:
        ctx: The deploy context.
        sinks: The sinks whose buckets to return; None returns those of
            every Stage 0 log sink when the sinks write to log buckets.
    """
    if sinks is None:
        if ctx.answers.logging.sink_type != LOGGING_SINK_TYPE:
            return []
        sinks = ctx.repo.log_sink_names()
    project = naming.stage0_project_id(ctx.answers.prefix, LOGGING_PROJECT_NAME)
    return [
        Bucket(
            sink=sink,
            address=f'{LOG_BUCKET_MODULE}["{sink}"].{LOG_BUCKET_RESOURCE}',
            import_id=(
                f"projects/{project}/locations/{ctx.answers.region}/"
                f"buckets/{sink}"
            ),
        )
        for sink in sinks
    ]


def sinks_of(addresses: Iterable[str | None]) -> list[str]:
    """Returns the sinks of the log bucket addresses among addresses.

    Args:
        addresses: Resource addresses, such as those of plan findings.
    """
    found = (_ADDRESS_RE.match(address or "") for address in addresses)
    return sorted({match.group("sink") for match in found if match})


def rewrite_projects(doc: Mapping[str, Any], addresses: Collection[str]) -> int:
    """Strips `projects/` from the `project` of instances in a state.

    Args:
        doc: The pulled state; changed in place.
        addresses: The instances to fix.

    Returns:
        How many instances changed.
    """
    changed = 0
    for address, instance in probe_lib.instances(doc):
        attributes = instance.get("attributes") or {}
        value = attributes.get(_PROJECT)
        if (
            address in addresses
            and isinstance(value, str)
            and value.startswith(_PROJECT_PREFIX)
        ):
            attributes[_PROJECT] = value.removeprefix(_PROJECT_PREFIX)
            changed += 1
    return changed


def commands(ctx: model.Context, found: Sequence[Bucket]) -> str:
    """Returns the manual fix, the commands the lab ran by hand.

    Args:
        ctx: The deploy context.
        found: The buckets to fix.
    """
    workspace = ctx.workspace(_STAGE)
    pull = runner_lib.manual(workspace, ("state", "pull"))
    now = ctx.now()
    backup = runner_lib.state_backup_path(ctx.env.plans, step=STEP, now=now)
    fixed = runner_lib.fixed_state_path(ctx.env.plans, now=now)
    lines = [f"{pull} > {shlex.quote(str(backup))}"]
    lines += [
        runner_lib.manual(
            workspace, ("import",), (), (bucket.address, bucket.import_id)
        )
        for bucket in found
    ]
    lines += [
        f"{pull} > {shlex.quote(str(fixed))}",
        f"Edit {fixed.name}: set attributes.project of each bucket to the "
        "bare project ID, and raise serial by 1.",
        runner_lib.manual(workspace, ("state", "push"), (), (str(fixed),)),
    ]
    return "\n".join(lines)


def _pull(tf: runner_lib.Terraform, ctx: model.Context) -> dict[str, Any]:
    """Pulls the Stage 0 state, or fails like a Terraform command."""
    try:
        return tf.state_pull(ctx.workspace(_STAGE))
    except runner_lib.TerraformError as error:
        raise model.command_error(error, "state pull") from error


def _generation(ctx: model.Context) -> int | None:
    """Returns the remote state generation, or None for a local state."""
    probe = ctx.stage0()
    return probe.remote.generation if probe.uses_remote else None


def _ask(ctx: model.Context, found: Sequence[Bucket]) -> None:
    """Lists the buckets and asks to fix them, or stops with the commands."""
    for bucket in found:
        ctx.say(f"  {bucket.address}\n    {bucket.import_id}")
    fallback = commands(ctx, found)
    if not ctx.interactive:
        raise model.InputRequiredError(
            "The log buckets need a state fix, which needs a confirmation.",
            remedy=fallback,
        )
    question = "Back up the state, import these buckets and fix their project?"
    if not ctx.confirm(question):
        raise model.StoppedError(
            "The operator declined the log bucket fix.", remedy=fallback
        )


def fix_log_buckets(
    ctx: model.Context,
    buckets: Sequence[Bucket],
    *,
    step_id: str | None = None,
) -> bool:
    """Imports the log buckets and fixes their project in the state.

    Each pull and push goes through the workspace's backend, local or
    remote. Terraform refuses a push whose lineage differs or whose serial
    is lower, so a change that raised the serial past the fixed state fails
    the push instead of being overwritten; a single concurrent write to the
    same serial is not detected. The caller plans again and requires no
    replacement.

    Args:
        ctx: The deploy context.
        buckets: The buckets to fix, usually from `log_buckets`.
        step_id: The step whose run-state records the fix, if any.

    Returns:
        Whether anything was imported or rewritten.

    Raises:
        model.BlockedError: If the Terraform environment has a problem.
        model.InputRequiredError: If the deploy may not prompt; the remedy
            holds the manual commands.
        model.StoppedError: If the operator declines.
        model.CommandError: If a Terraform command fails.
    """
    if not buckets:
        return False
    ctx.require_terraform_env()
    tf = ctx.terraform.for_step(_STAGE, STEP)
    ctx.say(
        f"{len(buckets)} log buckets need a state fix for "
        "terraform-provider-google issue 15725:"
    )
    _ask(ctx, buckets)
    generation = _generation(ctx)
    before = _pull(tf, ctx)
    now = ctx.now()
    backup = runner_lib.state_backup_path(ctx.env.plans, step=STEP, now=now)
    fsutil.write_private_json(backup, before)
    imported = _import_missing(ctx, tf, buckets, before)
    doc = _pull(tf, ctx)
    changed = rewrite_projects(doc, {bucket.address for bucket in buckets})
    if changed:
        _push_fixed(
            ctx, tf, doc, runner_lib.fixed_state_path(ctx.env.plans, now=now)
        )
    ctx.invalidate()
    if step_id is not None:
        ctx.confirmed(
            step_id,
            run_state_lib.BUCKET_FIX,
            f"backup {ctx.relative(backup)}; imported {imported}; "
            f"fixed {changed}; "
            f"serial {before.get('serial')} to {doc.get('serial')}; remote "
            f"generation {generation} to {_generation(ctx)}",
        )
        ctx.save()
    return bool(imported or changed)


def _import_missing(
    ctx: model.Context,
    tf: runner_lib.Terraform,
    buckets: Sequence[Bucket],
    state: Mapping[str, Any],
) -> int:
    """Imports the buckets that a state lacks and returns how many."""
    present = {address for address, _ in probe_lib.instances(state)}
    missing = [bucket for bucket in buckets if bucket.address not in present]
    for bucket in missing:
        completed = tf.import_resource(
            ctx.workspace(_STAGE), bucket.address, bucket.import_id
        )
        model.succeeded(completed, "import", log=tf.last_log)
    return len(missing)


def _push_fixed(
    ctx: model.Context,
    tf: runner_lib.Terraform,
    doc: dict[str, Any],
    path: pathlib.Path,
) -> None:
    """Raises the serial of a rewritten state, saves it and pushes it."""
    doc["serial"] = int(doc.get("serial") or 0) + 1
    fsutil.write_private_json(path, doc)
    completed = tf.state_push(ctx.workspace(_STAGE), path)
    model.succeeded(completed, "state push", log=tf.last_log)
