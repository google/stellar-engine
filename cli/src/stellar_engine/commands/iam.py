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

"""The `stellar iam snapshot`, `diff` and `restore` commands.

Stage 0 manages organization roles authoritatively, so an apply removes the
grants that it does not declare. A snapshot keeps the live organization
policy in the `gcloud organizations get-iam-policy --format=json` shape,
`diff` shows what changed since a snapshot or what a saved plan removes,
and `restore` writes a snapshot back, or records its missing grants in the
answers so Stage 0 grants them itself.
"""

import functools
import json
import pathlib
from typing import Annotated

from rich import console as rich_console
from rich import text as rich_text
import typer

from stellar_engine import iam_diff as iam_diff_lib
from stellar_engine import paths
from stellar_engine.commands import common
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.deploy import model
from stellar_engine.gcp import api
from stellar_engine.gcp import live
from stellar_engine.preflight import report
from stellar_engine.terraform import plan as plan_lib
from stellar_engine.wizard import prompts

# How often `restore` reads the etag again after a concurrent change.
_RESTORE_ATTEMPTS = 3
_UPDATE_MASK = ("bindings", "etag", "auditConfigs")


def _principal(cloud: model.Cloud) -> str | None:
    """Returns the identity of the credentials, or None when unknown."""
    try:
        return cloud.adc_principal().email
    except api.CLOUD_ERRORS:
        return None


def _read_policy(cloud: model.Cloud, org_id: str) -> iam_diff_lib.Policy:
    """Reads the live organization policy, or exits 1."""
    with common.ExitOn(*api.CLOUD_ERRORS, code=common.EXIT_CLOUD):
        return cloud.get_org_iam_policy(org_id)


def _save_snapshot(
    session: common.Session,
    env: paths.EnvPaths,
    cloud: model.Cloud,
    policy: iam_diff_lib.Policy,
    *,
    org_id: str,
    reason: str,
) -> pathlib.Path:
    """Saves a policy snapshot with its metadata, or exits 2."""
    meta = iam_diff_lib.snapshot_meta(
        session.repo,
        org_id=org_id,
        reason=reason,
        taken=common.now(),
        principal=_principal(cloud),
    )
    with common.ExitOn(ValueError):
        return iam_diff_lib.write_snapshot(env, policy, meta)


def iam_snapshot(
    reason: Annotated[
        str,
        typer.Option(
            "--reason",
            help="Lowercase word that names the file, such as before-audit.",
        ),
    ] = "manual",
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Save the organization IAM policy under iam-snapshots/.

    The file keeps the gcloud JSON shape without the etag, so `gcloud
    organizations set-iam-policy` restores it by hand as well; the
    metadata file beside it keeps the etag.
    """
    session = common.session(home, repo)
    env, answers = common.load_env(session, prefix)
    org_id = answers.organization.id
    cloud = live.LiveCloudApi()
    policy = _read_policy(cloud, org_id)
    path = _save_snapshot(
        session, env, cloud, policy, org_id=org_id, reason=reason
    )
    typer.echo(f"Saved the IAM policy of organization {org_id} to {path}.")


def _env_path(env: paths.EnvPaths, path: pathlib.Path) -> pathlib.Path:
    """Resolves a relative path against the environment when needed.

    The deploy prints and records paths relative to the environment, such
    as `plans/<file>` and `iam-snapshots/<file>`, so a relative path that
    the current directory lacks names a file of the environment.

    Args:
        env: The environment.
        path: The path the operator passed.
    """
    if path.is_absolute() or path.exists():
        return path
    return env.root / path


def _load_snapshot(
    env: paths.EnvPaths, path: pathlib.Path | None
) -> iam_diff_lib.Snapshot:
    """Reads a snapshot, the newest one without a path, or exits 2."""
    with common.ExitOn(iam_diff_lib.SnapshotError):
        found = (
            iam_diff_lib.latest_snapshot(env)
            if path is None
            else iam_diff_lib.read_snapshot(_env_path(env, path))
        )
    if found is None:
        common.fail(
            f"{env.prefix} has no IAM snapshot yet; run stellar iam snapshot."
        )
    return found


def _plan_target(
    env: paths.EnvPaths, path: pathlib.Path
) -> iam_diff_lib.Target:
    """Reads the organization IAM target of a saved plan, or exits 2.

    A `.tfplan` path reads the `terraform show -json` document that the
    deploy saved beside it.
    """
    if path.suffix == ".tfplan":
        path = path.with_suffix(".json")
    path = _env_path(env, path)
    with common.ExitOn(
        OSError,
        ValueError,
        plan_lib.PlanError,
        iam_diff_lib.UnknownMembersError,
    ):
        doc = json.loads(path.read_text(encoding="utf-8"))
        return iam_diff_lib.target_from_plan(plan_lib.parse(doc))


def _print_diff(
    console: rich_console.Console, title: str, found: iam_diff_lib.Diff
) -> None:
    """Prints the changes of a diff as a table, then their counts."""
    rows = iam_diff_lib.rows(found, added=True)
    if rows:
        console.print(report.iam_table(title, rows))
    console.print(
        rich_text.Text(
            f"{title}: {len(found.removed)} removed, {len(found.added)} "
            f"added, {len(found.kept_foreign)} kept, "
            f"{len(found.audit_overwrites)} audit configs."
        )
    )


def iam_diff(
    plan: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--plan",
            help=(
                "A saved plan under plans/, as .tfplan or its .json "
                "document; shows what it changes in the live policy. A "
                "relative path missing from the current directory names a "
                "file of the environment."
            ),
        ),
    ] = None,
    snapshot_path: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--snapshot",
            help=(
                "The snapshot to compare with, such as "
                "iam-snapshots/<file>.json. Defaults to the newest one."
            ),
        ),
    ] = None,
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Show how the live organization IAM policy differs.

    Without `--plan`, the command lists the grants removed and added since
    the snapshot. With `--plan`, it lists the grants that applying the
    plan removes and adds.
    """
    if plan is not None and snapshot_path is not None:
        common.fail("Pass --plan or --snapshot, not both.")
    session = common.session(home, repo)
    env, answers = common.load_env(session, prefix)
    org_id = answers.organization.id
    if plan is not None:
        title, target = f"Changes of {plan.name}", _plan_target(env, plan)
        current = _read_policy(live.LiveCloudApi(), org_id)
        result = iam_diff_lib.diff(current, target)
    else:
        found = _load_snapshot(env, snapshot_path)
        title = f"Changes since {found.path.name}"
        current = _read_policy(live.LiveCloudApi(), org_id)
        result = iam_diff_lib.diff(
            found.policy,
            iam_diff_lib.target_from_policy(current, keys_of=found.policy),
        )
    _print_diff(common.console(), title, result)


def _emit_overrides(
    session: common.Session,
    env: paths.EnvPaths,
    answers: models.Answers,
    missing: tuple[iam_diff_lib.Grant, ...],
) -> None:
    """Adds the missing grants of Stage 0 roles to the answers.

    The deploy's IAM review keeps removed grants the same way, through
    `iam_diff_lib.keep_in_overrides`. The Stage 0 roles come from the target
    that preflight builds, whose members do not matter here.
    """
    target = iam_diff_lib.target_from_repo(
        session.repo,
        lambda holder: None,
        answers_lib.stage0_iam_overrides(answers),
    )
    roles = {key.role for key in target.bindings}
    kept = [
        grant
        for grant in missing
        if grant.key.condition is None and grant.key.role in roles
    ]
    for grant in missing:
        if grant not in kept:
            typer.echo(f"Stage 0 does not manage {grant}; grant it by hand.")
    if not kept:
        typer.echo("No grant on a Stage 0 role is missing.")
        return
    with common.ExitOn(answers_lib.AnswersError):
        answers_lib.update(
            env.answers,
            functools.partial(iam_diff_lib.keep_in_overrides, grants=kept),
            repo=session.repo,
            home=session.home.root,
            source="stellar iam restore --emit-overrides",
        )
    typer.echo(
        f"Added {len(kept)} grants to overrides.{paths.BOOTSTRAP}.iam in "
        f"{env.answers}. Run stellar deploy --stage 0 so Stage 0 grants them."
    )


def _write_policy(
    cloud: model.Cloud, org_id: str, snap: iam_diff_lib.Snapshot, etag: str
) -> bool:
    """Writes a snapshot policy; returns False when the etag is stale."""
    try:
        cloud.set_org_iam_policy(
            org_id, snap.policy, etag=etag, update_mask=_UPDATE_MASK
        )
    except api.ConflictError:
        return False
    except api.CLOUD_ERRORS as error:
        common.fail(
            f"Cannot restore the policy: {error}. Fallback: "
            f"{_fallback(org_id, snap)}",
            common.EXIT_CLOUD,
        )
    return True


def _fallback(org_id: str, snap: iam_diff_lib.Snapshot) -> str:
    """Returns the gcloud command that restores a snapshot by hand."""
    return f"gcloud organizations set-iam-policy {org_id} {snap.path}"


def _restore_changes(
    current: iam_diff_lib.Policy, snap: iam_diff_lib.Snapshot
) -> iam_diff_lib.Diff:
    """Returns what writing a snapshot back changes in the live policy."""
    return iam_diff_lib.diff(
        current, iam_diff_lib.target_from_policy(snap.policy, keys_of=current)
    )


def _changes_anything(changes: iam_diff_lib.Diff) -> bool:
    """Returns whether a restore would change the live policy."""
    return bool(changes.removed or changes.added or changes.audit_overwrites)


def _confirm_restore(
    console: rich_console.Console, org_id: str, non_interactive: bool
) -> None:
    """Asks for the organization ID, or exits 4."""
    if not common.interactive(non_interactive):
        common.fail(
            "The restore needs the organization ID typed in a terminal.",
            common.EXIT_STOPPED,
        )
    question = f"This replaces the IAM policy of organization {org_id}."
    if not prompts.typed_confirm(common.prompter(console), question, org_id):
        common.fail(
            "The typed organization ID did not match.", common.EXIT_STOPPED
        )


def _reconfirm(
    console: rich_console.Console,
    snap: iam_diff_lib.Snapshot,
    org_id: str,
    current: iam_diff_lib.Policy,
    confirmed: iam_diff_lib.Diff,
) -> iam_diff_lib.Diff | None:
    """Recomputes a restore after a concurrent change to the live policy.

    Returns:
        The changes the operator confirmed, asking again when they differ
        from the ones confirmed before; None when nothing is left to do.
    """
    changes = _restore_changes(current, snap)
    if not _changes_anything(changes):
        return None
    if changes != confirmed:
        title = f"Restoring {snap.path.name} after a concurrent change"
        _print_diff(console, title, changes)
        # The first question already proved a terminal.
        _confirm_restore(console, org_id, non_interactive=False)
    return changes


def _write_back(
    session: common.Session,
    env: paths.EnvPaths,
    cloud: model.Cloud,
    console: rich_console.Console,
    snap: iam_diff_lib.Snapshot,
    *,
    org_id: str,
    current: iam_diff_lib.Policy,
    confirmed: iam_diff_lib.Diff,
) -> None:
    """Saves the live policy, then writes the snapshot back with its etag.

    After a concurrent change the policy is read and saved again, and the
    operator confirms the changes again when they differ from the ones
    confirmed, so a restore never removes a grant that nobody reviewed.
    """
    for attempt in range(_RESTORE_ATTEMPTS):
        if attempt:
            current = _read_policy(cloud, org_id)
            found = _reconfirm(console, snap, org_id, current, confirmed)
            if found is None:
                typer.echo("The live policy now matches the snapshot.")
                return
            confirmed = found
        backup = _save_snapshot(
            session, env, cloud, current, org_id=org_id, reason="restore"
        )
        typer.echo(f"Saved the live policy to {backup}.")
        if _write_policy(cloud, org_id, snap, current.etag):
            typer.echo(f"Restored the IAM policy of organization {org_id}.")
            return
    common.fail(
        f"The policy of organization {org_id} changed during each of "
        f"{_RESTORE_ATTEMPTS} writes. Fallback: {_fallback(org_id, snap)}",
        common.EXIT_CLOUD,
    )


def iam_restore(
    snapshot_path: Annotated[
        pathlib.Path,
        typer.Argument(help="The snapshot file under iam-snapshots/."),
    ],
    emit_overrides: Annotated[
        bool,
        typer.Option(
            "--emit-overrides",
            help=(
                "Add the missing grants of Stage 0 roles to "
                "overrides.0-bootstrap.iam instead, so the next Stage 0 "
                "apply grants them."
            ),
        ),
    ] = False,
    non_interactive: Annotated[
        bool,
        common.non_interactive_option(
            "Never prompt; a restore then stops with exit status 4."
        ),
    ] = False,
    prefix: common.PrefixOption = None,
    home: common.HomeOption = None,
    repo: common.RepoOption = None,
):
    """Write a snapshot back as the organization IAM policy.

    The command shows what the restore changes, asks for the organization
    ID, saves the live policy as a new snapshot, and writes the snapshot
    with the etag of a fresh read. When someone changes the policy during
    the write, it reads and saves the policy again, and asks again when
    the changes differ.
    """
    session = common.session(home, repo)
    env, answers = common.load_env(session, prefix)
    org_id = answers.organization.id
    snap = _load_snapshot(env, snapshot_path)
    if snap.meta is not None and snap.meta.org_id != org_id:
        common.fail(
            f"{snap.path} holds the policy of organization "
            f"{snap.meta.org_id}, not {org_id}."
        )
    cloud = live.LiveCloudApi()
    current = _read_policy(cloud, org_id)
    changes = _restore_changes(current, snap)
    console = common.console()
    _print_diff(console, f"Restoring {snap.path.name}", changes)
    if emit_overrides:
        _emit_overrides(session, env, answers, changes.added)
        return
    if not _changes_anything(changes):
        typer.echo("The live policy already matches the snapshot.")
        return
    _confirm_restore(console, org_id, non_interactive)
    _write_back(
        session,
        env,
        cloud,
        console,
        snap,
        org_id=org_id,
        current=current,
        confirmed=changes,
    )
