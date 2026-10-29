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

"""Tests for the overwrite-safe writer."""

import datetime
import hashlib

import pytest

import conftest
from stellar_engine import paths as paths_lib
from stellar_engine.render import imports
from stellar_engine.render import phase
from stellar_engine.render import stages
from stellar_engine.render import writer

NOW = datetime.datetime(2026, 10, 23, 12, 30, 5, tzinfo=datetime.UTC)
STAMP = "20261023T123005Z"
_GENERATED = f"{writer.MARKER}tst/answers.yaml\nvalue = 1\n"


@pytest.fixture
def paths(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace / "terraform.tfvars", tmp_path / "generated" / "0.sha256"


def _never(diff):
    raise AssertionError(f"confirm called unexpectedly with {diff!r}")


def _write(target, hash_file, content, **kwargs):
    options = {"force": False, "interactive": False, "confirm": _never}
    options.update(kwargs)
    return writer.write(target, content, hash_file, now=NOW, **options)


def _digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def test_creates_missing_target(paths):
    target, hash_file = paths
    result = _write(target, hash_file, 'a = "1"\n')
    assert result.outcome == writer.Outcome.CREATED
    assert result.path == target
    assert result.backup is None
    assert '+a = "1"' in result.diff
    assert target.read_text() == 'a = "1"\n'
    assert hash_file.read_text() == _digest('a = "1"\n') + "\n"
    assert conftest.mode(target) == 0o600
    assert conftest.mode(hash_file) == 0o600
    assert conftest.mode(hash_file.parent) == 0o700


def test_unchanged_refreshes_hash(paths):
    target, hash_file = paths
    target.write_text("same\n")
    result = _write(target, hash_file, "same\n")
    assert result.outcome == writer.Outcome.UNCHANGED
    assert result.diff == ""
    assert hash_file.read_text().strip() == _digest("same\n")


def test_unedited_target_updates_silently(paths):
    target, hash_file = paths
    _write(target, hash_file, "old\n")
    result = _write(target, hash_file, "new\n")
    assert result.outcome == writer.Outcome.UPDATED
    assert result.backup is None
    assert "-old" in result.diff
    assert "+new" in result.diff
    assert target.read_text() == "new\n"
    assert hash_file.read_text().strip() == _digest("new\n")
    assert list(target.parent.iterdir()) == [target]


def test_edited_target_refused_without_force(paths):
    target, hash_file = paths
    _write(target, hash_file, "old\n")
    target.write_text("edited\n")
    with pytest.raises(writer.OverwriteRefusedError, match="--force"):
        _write(target, hash_file, "new\n")
    assert target.read_text() == "edited\n"
    assert hash_file.read_text().strip() == _digest("old\n")


def test_target_without_hash_counts_as_edited(paths):
    target, hash_file = paths
    target.write_text("hand written\n")
    with pytest.raises(writer.OverwriteRefusedError):
        _write(target, hash_file, "new\n")


def test_force_backs_up_then_writes(paths):
    target, hash_file = paths
    target.write_text("edited\n")
    target.chmod(0o644)
    result = _write(target, hash_file, "new\n", force=True)
    assert result.outcome == writer.Outcome.UPDATED
    backup = result.backup
    assert backup is not None
    assert backup == target.with_name(f"terraform.tfvars.backup.{STAMP}")
    assert backup.read_text() == "edited\n"
    assert conftest.mode(backup) == 0o600
    assert target.read_text() == "new\n"
    assert conftest.mode(target) == 0o600
    assert hash_file.read_text().strip() == _digest("new\n")


def test_backups_in_the_same_second_do_not_collide(paths):
    target, hash_file = paths
    target.write_text("first edit\n")
    first = _write(target, hash_file, "new\n", force=True).backup
    target.write_text("second edit\n")
    second = _write(target, hash_file, "newer\n", force=True).backup
    assert first is not None
    assert second is not None
    assert second.name == f"{first.name}.1"
    assert first.read_text() == "first edit\n"
    assert second.read_text() == "second edit\n"


def test_backup_name_uses_utc(paths):
    target, hash_file = paths
    target.write_text("edited\n")
    offset = datetime.timezone(datetime.timedelta(hours=-4))
    local = NOW.astimezone(offset)
    result = writer.write(
        target,
        "new\n",
        hash_file,
        force=True,
        interactive=False,
        confirm=_never,
        now=local,
    )
    assert result.backup is not None
    assert result.backup.name.endswith(STAMP)


def test_interactive_confirm_accepts(paths):
    target, hash_file = paths
    target.write_text("edited\n")
    seen = []

    def confirm(diff):
        seen.append(diff)
        return True

    result = _write(
        target, hash_file, "new\n", interactive=True, confirm=confirm
    )
    assert result.outcome == writer.Outcome.UPDATED
    assert result.backup is not None
    assert seen == [result.diff]
    assert "-edited" in seen[0]
    assert target.read_text() == "new\n"


def test_interactive_confirm_declines(paths):
    target, hash_file = paths
    _write(target, hash_file, "old\n")
    target.write_text("edited\n")
    result = _write(
        target, hash_file, "new\n", interactive=True, confirm=lambda d: False
    )
    assert result.outcome == writer.Outcome.SKIPPED
    assert result.backup is None
    assert "+new" in result.diff
    assert target.read_text() == "edited\n"
    assert hash_file.read_text().strip() == _digest("old\n")
    assert list(target.parent.iterdir()) == [target]


def test_force_skips_confirm(paths):
    target, hash_file = paths
    target.write_text("edited\n")
    result = _write(target, hash_file, "new\n", force=True, interactive=True)
    assert result.outcome == writer.Outcome.UPDATED


def test_diff_contents(tmp_path):
    target = tmp_path / "terraform.tfvars"
    assert writer.diff(target, "") == ""
    assert writer.diff(target, "a\n").endswith("+a\n")
    target.write_text("a\n")
    assert writer.diff(target, "a\n") == ""
    text = writer.diff(target, "b\n")
    assert text.startswith(f"--- {target}\n+++ {target} (rendered)\n")
    assert "-a\n+b\n" in text


def test_outcome_values():
    assert [str(outcome) for outcome in writer.Outcome] == [
        "created",
        "updated",
        "unchanged",
        "skipped",
        "removed",
    ]


def test_marker_starts_the_owned_headers_only(repo):
    assert phase.header("tst")[0].startswith(writer.MARKER)
    assert imports.header("0", "tst")[0].startswith(writer.MARKER)
    # The tfvars keep a hash instead, so their header must not match.
    for stage in paths_lib.STAGES:
        assert not stages.header(repo, stage, "tst")[0].startswith(
            writer.MARKER
        )


def test_is_generated(tmp_path):
    generated = tmp_path / "generated.tf"
    generated.write_text(_GENERATED)
    assert writer.is_generated(generated)
    assert phase.is_generated is writer.is_generated
    later = tmp_path / "later.tf"
    later.write_text(f"# operator file\n{writer.MARKER}\n")
    assert not writer.is_generated(later)
    link = tmp_path / "link.tf"
    link.symlink_to(generated)
    assert not writer.is_generated(link)
    assert not writer.is_generated(tmp_path / "missing.tf")
    assert not writer.is_generated(tmp_path)


def test_write_owned_creates_updates_and_keeps(tmp_path):
    target = tmp_path / "owned.tf"
    created = writer.write_owned(target, _GENERATED, 0o644)
    assert created is writer.Outcome.CREATED
    assert target.read_text() == _GENERATED
    assert conftest.mode(target) == 0o644
    kept = writer.write_owned(target, _GENERATED, 0o644)
    assert kept is writer.Outcome.UNCHANGED
    changed = _GENERATED.replace("1", "2")
    updated = writer.write_owned(target, changed, 0o600)
    assert updated is writer.Outcome.UPDATED
    assert target.read_text() == changed
    assert conftest.mode(target) == 0o600


def test_write_owned_removes_on_empty_content(tmp_path):
    target = tmp_path / "owned.tf"
    assert writer.write_owned(target, "", 0o644) is None
    assert not target.exists()
    target.write_text(_GENERATED)
    assert writer.write_owned(target, "", 0o644) is writer.Outcome.REMOVED
    assert not target.exists()
