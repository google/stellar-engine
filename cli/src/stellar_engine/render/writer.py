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

"""Writes rendered files without losing the operator's manual edits.

The hash file records what the last render wrote. A target that still
matches it holds no manual edits and is replaced silently. Any other
existing content is treated as an edit: it is backed up before it is
replaced, and only with `--force` or the operator's confirmation.

Files that every render replaces, such as the import file and the Stage 0
phase file, keep no hash. Their first line starts with `MARKER` instead,
so the callers of `write_owned` never replace or remove an operator's own
file of the same name.
"""

from collections.abc import Callable
import dataclasses
import datetime
import difflib
import enum
import hashlib
import os
import pathlib

from stellar_engine import fsutil

# Marks files that stellar generated, so it never replaces or removes an
# operator's own file of the same name.
MARKER = "# stellar render writes this file from envs/"
_FILE_MODE = 0o600
_DIR_MODE = 0o700
BACKUP_TIME_FORMAT = "%Y%m%dT%H%M%SZ"


class Outcome(enum.StrEnum):
    """What `write` or `write_owned` did with the target file."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"
    REMOVED = "removed"


class OverwriteRefusedError(Exception):
    """Raised when an edited file would be replaced without consent."""


@dataclasses.dataclass(frozen=True)
class WriteResult:
    """Result of `write`.

    Attributes:
        outcome: What happened to the target.
        path: Path of the target file.
        backup: Path of the backup of the replaced content, or None.
        diff: Unified diff from the previous content to the new content,
            empty when nothing changed.
    """

    outcome: Outcome
    path: pathlib.Path
    backup: pathlib.Path | None
    diff: str


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp(now: datetime.datetime) -> str:
    """Returns the UTC time stamp that names backups, logs, plans and snapshots.

    Args:
        now: The time to format.
    """
    return now.astimezone(datetime.UTC).strftime(BACKUP_TIME_FORMAT)


def _backup(
    target: pathlib.Path, data: bytes, now: datetime.datetime
) -> pathlib.Path:
    """Copies the current content next to the target and returns the path.

    The name carries the UTC time, plus a counter when two backups land in
    the same second, so an earlier backup is never overwritten.
    """
    base = f"{target.name}.backup.{stamp(now)}"
    counter = 0
    while True:
        name = base if counter == 0 else f"{base}.{counter}"
        candidate = target.with_name(name)
        try:
            descriptor = os.open(
                candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _FILE_MODE
            )
        except FileExistsError:
            counter += 1
            continue
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), _FILE_MODE)
            handle.write(data)
        return candidate


def _store_hash(hash_file: pathlib.Path, digest: str) -> None:
    if fsutil.read_text_or_none(hash_file) == f"{digest}\n":
        return
    hash_file.parent.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
    fsutil.atomic_write(hash_file, f"{digest}\n".encode(), _FILE_MODE)


def diff(target: pathlib.Path, content: str) -> str:
    """Returns a unified diff from the target's content to `content`.

    Args:
        target: File to compare. A missing file counts as empty.
        content: New content.

    Returns:
        The diff text, or an empty string when the contents are equal.
    """
    current = fsutil.read_text_or_none(target) or ""
    if current == content:
        return ""
    lines = difflib.unified_diff(
        current.splitlines(keepends=True),
        content.splitlines(keepends=True),
        fromfile=str(target),
        tofile=f"{target} (rendered)",
    )
    return "".join(lines)


def write(
    target: pathlib.Path,
    content: str,
    hash_file: pathlib.Path,
    *,
    force: bool,
    interactive: bool,
    confirm: Callable[[str], bool],
    now: datetime.datetime,
) -> WriteResult:
    """Writes `content` to `target`, protecting manual edits.

    Args:
        target: File to write, such as a workspace `terraform.tfvars`. Its
            directory must exist.
        content: Rendered content.
        hash_file: File holding the sha256 hex digest of the last content
            written to `target`. It is updated after every write.
        force: Replaces an edited target without asking, after a backup.
        interactive: Asks through `confirm` before replacing an edited
            target.
        confirm: Called with the diff; returns True to replace the target.
        now: Current time, used to name backups.

    Returns:
        What happened, with the backup path and the diff.

    Raises:
        OverwriteRefusedError: If the target holds manual edits and neither
            `force` nor `interactive` is set.
    """
    data = content.encode("utf-8")
    digest = _digest(data)
    try:
        current = target.read_bytes()
    except FileNotFoundError:
        changes = diff(target, content)
        fsutil.atomic_write(target, data, _FILE_MODE)
        _store_hash(hash_file, digest)
        return WriteResult(Outcome.CREATED, target, None, changes)
    if current == data:
        _store_hash(hash_file, digest)
        return WriteResult(Outcome.UNCHANGED, target, None, "")
    changes = diff(target, content)
    recorded = (fsutil.read_text_or_none(hash_file) or "").strip()
    if recorded and recorded == _digest(current):
        fsutil.atomic_write(target, data, _FILE_MODE)
        _store_hash(hash_file, digest)
        return WriteResult(Outcome.UPDATED, target, None, changes)
    if not force:
        if not interactive:
            raise OverwriteRefusedError(
                f"{target} has manual edits since the last render. Move "
                "them into answers.yaml, or rerun with --force to replace "
                "the file after a backup."
            )
        if not confirm(changes):
            return WriteResult(Outcome.SKIPPED, target, None, changes)
    backup = _backup(target, current, now)
    fsutil.atomic_write(target, data, _FILE_MODE)
    _store_hash(hash_file, digest)
    return WriteResult(Outcome.UPDATED, target, backup, changes)


def is_generated(path: pathlib.Path) -> bool:
    """Returns whether stellar wrote the file at a path.

    A generated file starts with `MARKER` on its first line.

    Args:
        path: File to check. A symlink or a missing file is not generated.
    """
    if path.is_symlink() or not path.is_file():
        return False
    with path.open(encoding="utf-8") as handle:
        return handle.readline().startswith(MARKER)


def write_owned(
    target: pathlib.Path, content: str, mode: int
) -> Outcome | None:
    """Writes or removes a generated file that every render replaces.

    The caller checks with `is_generated` first, because this function
    replaces or removes whatever file is at the target.

    Args:
        target: File to write. Its directory must exist.
        content: Rendered content; empty removes the file.
        mode: Permission bits of the written file, such as 0o600.

    Returns:
        What happened to the file: created, updated, unchanged or removed.
        None when the content is empty and no file was there to remove.
    """
    if not content:
        try:
            target.unlink()
        except FileNotFoundError:
            return None
        return Outcome.REMOVED
    previous = fsutil.read_text_or_none(target)
    fsutil.atomic_write(target, content, mode)
    if previous is None:
        return Outcome.CREATED
    if previous == content:
        return Outcome.UNCHANGED
    return Outcome.UPDATED
