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

"""Tests for the file helpers that every environment writer shares."""

import conftest
from stellar_engine import fsutil


def test_read_bytes_or_none(tmp_path):
    path = tmp_path / "state"
    assert fsutil.read_bytes_or_none(path) is None
    assert fsutil.read_bytes_or_none(tmp_path) is None
    path.write_bytes(b"data")
    assert fsutil.read_bytes_or_none(path) == b"data"


def test_atomic_write_uses_the_private_mode(tmp_path):
    path = tmp_path / "plan.json"
    fsutil.atomic_write(path, "{}\n", fsutil.PRIVATE_FILE_MODE)
    assert path.read_text() == "{}\n"
    assert conftest.mode(path) == 0o600
