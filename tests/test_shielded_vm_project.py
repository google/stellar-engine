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

"""Checks SEV default machine type and CMEK ordering in shielded-vm-project."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/il5/shielded-vm-project"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestShieldedVmProject(unittest.TestCase):
    def test_default_instance_type_supports_sev(self):
        variables_tf = (_BLUEPRINT_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        instance_type = _top_block(variables_tf, 'variable "instance_type"')
        self.assertRegex(
            instance_type, r'\n\s*default\s*=\s*"n2d-standard-2"\n'
        )

    def test_vm_depends_on_cmek_iam_binding(self):
        main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        vm_block = _top_block(main_tf, 'module "shielded-vm"')
        self.assertIn("google_service_account.compute", vm_block)
        self.assertIn("google_kms_crypto_key_iam_member.compute", vm_block)


if __name__ == "__main__":
    unittest.main()
