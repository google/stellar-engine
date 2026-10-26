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

"""Checks the delegated role grant conditions in the FAST stages."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_STAGES_DIR = _REPO_ROOT / "fast/stages-aw"

# The IAM condition language has no size() function, so IAM rejects any
# binding whose condition calls it.
_SIZE_CALL = re.compile(r"modifiedGrantsByRole'[^)]*\)\.size\(\)")
_HAS_ONLY = re.compile(r"modifiedGrantsByRole'[^)]*\)\.hasOnly\(")


def _stage_files():
    return sorted(_STAGES_DIR.glob("*/*.tf"))


class TestDelegatedGrantConditions(unittest.TestCase):
    def test_conditions_never_call_size(self):
        for path in _stage_files():
            with self.subTest(path=path.relative_to(_REPO_ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(_SIZE_CALL.search(text))

    def test_conditions_still_limit_the_roles(self):
        found = [
            path
            for path in _stage_files()
            if _HAS_ONLY.search(path.read_text(encoding="utf-8"))
        ]
        names = {path.relative_to(_STAGES_DIR).as_posix() for path in found}
        self.assertLessEqual(
            {
                "0-bootstrap/automation.tf",
                "0-bootstrap/organization.tf",
                "3-security/main.tf",
            },
            names,
        )


if __name__ == "__main__":
    unittest.main()
