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

"""Checks the Stage 0 wiring for pre-created projects and workloads."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BOOTSTRAP_DIR = _REPO_ROOT / "fast/stages-aw/0-bootstrap"
_PROJECT_MODULE_DIR = _REPO_ROOT / "modules/project"

# Maps each Stage 0 project module to its file and policy key.
_PROJECT_BLOCKS = (
    ("automation.tf", "automation-project", "automation"),
    ("billing.tf", "billing-export-project", "billing"),
    ("log-export.tf", "log-export-project", "logging"),
)


def _block(text, header):
    """Returns the top-level HCL block that starts with header."""
    pattern = re.compile(re.escape(header) + r"\s*\{[\s\S]*?\n\}")
    match = pattern.search(text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _read(path):
    return path.read_text(encoding="utf-8")


class TestBootstrapDeletionPolicy(unittest.TestCase):
    def setUp(self):
        self.variable = _block(
            _read(_BOOTSTRAP_DIR / "variables.tf"),
            'variable "project_deletion_policies"',
        )

    def test_each_project_module_passes_its_policy(self):
        for filename, module, key in _PROJECT_BLOCKS:
            with self.subTest(module=module):
                block = _block(
                    _read(_BOOTSTRAP_DIR / filename), f'module "{module}"'
                )
                self.assertRegex(
                    block,
                    r"\n\s*deletion_policy\s*=\s*"
                    rf"var\.project_deletion_policies\.{key}\n",
                )

    def test_every_key_defaults_to_delete(self):
        keys = {key for _, _, key in _PROJECT_BLOCKS}
        defaults = dict(
            re.findall(
                r'(\w+)\s*=\s*optional\(string,\s*"(\w+)"\)', self.variable
            )
        )
        self.assertEqual(defaults, dict.fromkeys(keys, "DELETE"))
        self.assertRegex(self.variable, r"\n\s*default\s*=\s*\{\}\n")
        self.assertRegex(self.variable, r"\n\s*nullable\s*=\s*false\n")

    def test_validation_matches_project_module_values(self):
        module_variable = _block(
            _read(_PROJECT_MODULE_DIR / "variables.tf"),
            'variable "deletion_policy"',
        )

        def allowed(text):
            match = re.search(r"contains\(\[([^\]]*)\]", text)
            self.assertIsNotNone(match)
            return set(re.findall(r'"(\w+)"', match.group(1)))

        self.assertEqual(allowed(self.variable), allowed(module_variable))
        self.assertEqual(
            allowed(self.variable), {"ABANDON", "DELETE", "PREVENT"}
        )


class TestBootstrapWorkloadImport(unittest.TestCase):
    def test_workload_ignores_input_only_fields(self):
        block = _block(
            _read(_BOOTSTRAP_DIR / "organization.tf"),
            'resource "google_assured_workloads_workload" "primary"',
        )
        match = re.search(r"ignore_changes\s*=\s*\[([^\]]*)\]", block)
        self.assertIsNotNone(match)
        ignored = {item.strip() for item in match.group(1).split(",")}
        self.assertLessEqual({"billing_account", "resource_settings"}, ignored)


if __name__ == "__main__":
    unittest.main()
