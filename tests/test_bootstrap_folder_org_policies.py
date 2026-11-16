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

"""Checks Stage 0 folder org policy attachment."""

import pathlib
import re
import unittest

_ORG_TF = (
    pathlib.Path(__file__).resolve().parents[1]
    / "fast/stages-aw/0-bootstrap/organization.tf"
)


def _block(text, header):
    pattern = re.compile(re.escape(header) + r"\s*\{[\s\S]*?\n\}")
    match = pattern.search(text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestBootstrapFolderOrgPolicies(unittest.TestCase):
    def setUp(self):
        self.text = _ORG_TF.read_text(encoding="utf-8")
        self.root_folder = _block(self.text, 'module "root-folder-config"')

    def test_deploy_root_folder_config_includes_org_policies(self):
        self.assertRegex(
            self.text,
            r"deploy_root_folder_config\s*=\s*\([\s\S]*?"
            r"!var\.deploy_org_resources\.org_policies[\s\S]*?\)",
        )

    def test_root_folder_config_passes_org_policies_and_factory(self):
        self.assertRegex(
            self.root_folder,
            r"org_policies\s*=\s*\(\s*"
            r"var\.deploy_org_resources\.org_policies\s*\|\|\s*"
            r"var\.bootstrap_user\s*!=\s*null\s*\?\s*null\s*:\s*\{\s*"
            r"for\s+k,\s*v\s+in\s+local\.org_policies\s*:\s*k\s*=>\s*v\s+"
            r'if\s*!startswith\(k,\s*"custom\."\)\s*\}\s*\)',
        )
        self.assertRegex(
            self.root_folder,
            r"factories_config\s*=\s*\{[\s\S]*?"
            r"org_policies\s*=\s*\(\s*"
            r"var\.deploy_org_resources\.org_policies\s*\|\|\s*"
            r"var\.bootstrap_user\s*!=\s*null\s*\?\s*null\s*:\s*"
            r"var\.factories_config\.org_policy\s*\)",
        )

    def test_root_folder_config_omits_scalar_context_condition_vars(self):
        self.assertNotIn("condition_vars", self.root_folder)


if __name__ == "__main__":
    unittest.main()
