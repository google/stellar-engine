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

"""File helpers shared by every module that writes environment files."""

import os
import pathlib
import tempfile


def read_text_or_none(path: pathlib.Path) -> str | None:
    """Returns the UTF-8 text of a file, or None when it does not exist.

    Args:
        path: File to read.
    """
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def atomic_write(path: pathlib.Path, data: bytes | str, mode: int) -> None:
    """Replaces a file with new content in one step.

    A temporary file in the same directory plus `os.replace` means a crash
    never leaves a half-written file behind. The temporary file gets its
    mode before any content, so a private file is never readable by others.

    Args:
        path: File to write. Its directory must exist.
        data: New content; text is encoded as UTF-8.
        mode: Permission bits of the file, such as 0o600.
    """
    path = pathlib.Path(path)
    if isinstance(data, str):
        data = data.encode("utf-8")
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except BaseException:
        pathlib.Path(temp_name).unlink(missing_ok=True)
        raise
