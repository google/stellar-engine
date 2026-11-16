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

"""Checks Stage 1 tenant folder IAM lookups in branch-tenants.tf."""

import pathlib
import unittest

_BRANCH_TENANTS_TF = (
    pathlib.Path(__file__).resolve().parents[1]
    / "fast/stages-aw/1-resman/branch-tenants.tf"
)


class TestResmanTenantIamLookup(unittest.TestCase):
    def setUp(self):
        self.text = _BRANCH_TENANTS_TF.read_text(encoding="utf-8")

    def test_no_invalid_tenant_name_lookup(self):
        self.assertNotIn("each.value.tenant.name", self.text)

    def test_top_folder_roles_uses_each_key(self):
        self.assertRegex(
            self.text,
            r"for\s+k\s+in\s+var\.tenants_config\.top_folder_roles\s*:\s*"
            r"k\s*=>\s*local\.tenant_iam\[each\.key\]",
        )


if __name__ == "__main__":
    unittest.main()
