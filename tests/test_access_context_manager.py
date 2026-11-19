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

"""Checks how the access-context-manager module renders access levels."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_MODULE_DIR = _REPO_ROOT / "modules/access-context-manager"
_ACCESS_LEVEL = (
    'resource "google_access_context_manager_access_level" "access_levels"'
)


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestAccessLevelConditions(unittest.TestCase):
    def setUp(self):
        main_tf = (_MODULE_DIR / "main.tf").read_text(encoding="utf-8")
        self.access_level = _top_block(main_tf, _ACCESS_LEVEL)

    def test_access_level_renders_every_condition(self):
        self.assertRegex(
            self.access_level,
            r'dynamic "conditions" \{\s*'
            r"for_each\s*=\s*each\.value\.conditions\n",
        )
        # A static index reads one condition and drops the others.
        self.assertNotRegex(self.access_level, r"conditions\[\d+\]")
        self.assertNotRegex(self.access_level, r"\n\s*conditions \{")

    def test_access_level_keeps_the_default_combining_function(self):
        # The provider default combines conditions with AND. An explicit
        # argument would show a diff on existing access levels.
        self.assertNotIn("combining_function", self.access_level)

    def test_device_policy_renders_only_when_set(self):
        self.assertRegex(
            self.access_level,
            r'dynamic "device_policy" \{\s*for_each\s*=\s*\(\s*'
            r"conditions\.value\.device_policy == null\s*"
            r"\? \[\]\s*"
            r": \[conditions\.value\.device_policy\]\s*\)",
        )
        self.assertNotRegex(self.access_level, r"\n\s*device_policy \{")

    def test_device_policy_is_optional_in_the_variable_type(self):
        variables_tf = (_MODULE_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        variable = _top_block(variables_tf, 'variable "access_levels"')
        self.assertRegex(variable, r"device_policy\s*=\s*optional\(object\(\{")
        # The other condition attributes keep their required types, so
        # callers that pass the full shape see no interface change.
        for attribute, attribute_type in (
            ("ip_subnetworks", r"list\(string\)"),
            ("members", r"list\(string\)"),
            ("negate", "bool"),
            ("regions", r"list\(string\)"),
        ):
            self.assertRegex(
                variable, rf"\n\s*{attribute}\s*=\s*{attribute_type}\n"
            )


if __name__ == "__main__":
    unittest.main()
