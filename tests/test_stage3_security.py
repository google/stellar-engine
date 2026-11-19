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

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SECURITY_DIR = _REPO_ROOT / "fast/stages-aw/3-security"


class TestStage3Security(unittest.TestCase):
    def test_tfvars_local_file_is_owner_only(self):
        """Verify only the owner can read the Stage 3 tfvars output file."""
        outputs_tf = (_SECURITY_DIR / "outputs.tf").read_text(encoding="utf-8")
        block = re.search(
            r'resource "local_file" "tfvars" \{\n(.*?)\n\}',
            outputs_tf,
            re.DOTALL,
        )
        self.assertIsNotNone(block)
        permissions = re.findall(
            r'^\s*file_permission\s*=\s*"([^"]*)"', block.group(1), re.MULTILINE
        )
        self.assertEqual(permissions, ["0600"])


if __name__ == "__main__":
    unittest.main()
