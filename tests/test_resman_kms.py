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

"""Checks Stage 1 tenant KMS configuration reads locations from tenant_info."""

import pathlib
import re
import unittest

_RESMAN_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "fast/stages-aw/1-resman"
)
_KMS_TF = _RESMAN_DIR / "kms.tf"
_BRANCH_TENANTS_TF = _RESMAN_DIR / "branch-tenants.tf"


def _top_level_block(text, header):
    pattern = re.compile(
        r"^" + re.escape(header) + r"\s*\{.*?^\}", re.MULTILINE | re.DOTALL
    )
    match = pattern.search(text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _nested_block(text, name):
    pattern = re.compile(
        r"^\s{2}" + re.escape(name) + r"\s*=\s*\{.*?^\s{2}\}",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        raise AssertionError(f"Nested block not found: {name}")
    return match.group(0)


class TestResmanTenantKmsLocation(unittest.TestCase):
    def setUp(self):
        self.kms_text = _KMS_TF.read_text(encoding="utf-8")
        self.tenant_keys_module = _top_level_block(
            self.kms_text, 'module "tenant-project-keys"'
        )
        self.branch_tenants_text = _BRANCH_TENANTS_TF.read_text(
            encoding="utf-8"
        )

    def test_no_direct_each_value_locations_lookup(self):
        self.assertNotIn("each.value.locations.kms", self.kms_text)

    def test_keyring_location_coalesces_tenant_info_kms_location(self):
        keyring_block = _nested_block(self.tenant_keys_module, "keyring")
        self.assertRegex(
            keyring_block,
            r"location\s*=\s*coalesce\("
            r"try\(each\.value\.tenant_info\.locations\.kms,\s*null\),\s*"
            r"var\.regions\.primary\)",
        )

    def test_keys_block_omits_unsupported_locations_attribute(self):
        keys_block = _nested_block(self.tenant_keys_module, "keys")
        self.assertNotRegex(keys_block, r"\blocations\s*=")

    def test_branch_tenants_exposes_tenant_info_and_null_safe_gcs_locations(
        self,
    ):
        locals_block = _top_level_block(self.branch_tenants_text, "locals")
        self.assertRegex(
            locals_block,
            r"tenant_envs\s*=\s*merge\([\s\S]*?tenant_info\s*=\s*v",
        )
        self.assertRegex(
            locals_block,
            r"gcs_locations\s*=\s*\{[\s\S]*?"
            r"coalesce\(try\(v\.locations\.gcs,\s*null\),\s*"
            r"var\.regions\.primary\)",
        )


if __name__ == "__main__":
    unittest.main()
