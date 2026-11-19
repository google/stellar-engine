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

"""Checks that the postgresql blueprint creates no VPC firewall rule."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/il5/postgresql"
_DEPRECATED_INPUTS = {
    "allowed_firewall_ports": "list(number)",
    "firewall_name": "string",
    "firewall_source_range": "list(string)",
}


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestPostgresqlFirewall(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        self.variables_tf = (_BLUEPRINT_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )

    def test_blueprint_declares_no_firewall_resource(self):
        # The instance uses Private Service Access, so a VPC firewall rule
        # cannot protect it, and a rule without a target opens the port to
        # every instance in the Shared VPC.
        dirs = [_BLUEPRINT_DIR]
        for source in re.findall(r'source\s*=\s*"(\.[^"]+)"', self.main_tf):
            dirs.append((_BLUEPRINT_DIR / source).resolve())
        self.assertEqual(len(dirs), 2)
        for directory in dirs:
            for path in sorted(directory.glob("*.tf")):
                self.assertNotRegex(
                    path.read_text(encoding="utf-8"),
                    r'resource\s+"google_compute_\w*firewall\w*"',
                    msg=str(path.relative_to(_REPO_ROOT)),
                )

    def test_firewall_inputs_are_optional(self):
        # Existing tfvars files and module calls still set these inputs, so
        # they stay declared, and new callers can leave them out.
        for name, type_ in _DEPRECATED_INPUTS.items():
            block = _top_block(self.variables_tf, f'variable "{name}"')
            self.assertRegex(block, r"\n\s*default\s*=\s*null\n", msg=name)
            self.assertRegex(
                block,
                r"\n\s*type\s*=\s*" + re.escape(type_) + r"\n",
                msg=name,
            )
            self.assertRegex(
                block, r'description\s*=\s*"Deprecated and ignored\.', msg=name
            )

    def test_firewall_inputs_only_feed_the_deprecation_check(self):
        check = _top_block(self.main_tf, 'check "deprecated_firewall_inputs"')
        rest = self.main_tf.replace(check, "")
        for name in _DEPRECATED_INPUTS:
            self.assertRegex(check, rf"var\.{name} == null", msg=name)
            self.assertNotIn(f"var.{name}", rest, msg=name)

    def test_sample_tfvars_omits_the_firewall_inputs(self):
        sample = (_BLUEPRINT_DIR / "terraform.tfvars.sample").read_text(
            encoding="utf-8"
        )
        for name in _DEPRECATED_INPUTS:
            self.assertNotIn(name, sample)

    def test_readme_does_not_describe_a_firewall_rule_for_the_database(self):
        readme = (_BLUEPRINT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("This blueprint creates no VPC firewall rule.", readme)
        self.assertNotIn("google_compute_firewall.rules", readme)
        permissions = readme.split("## Deployer Permissions")[1]
        permissions = permissions.split("\n## ")[0]
        self.assertNotIn("roles/compute.securityAdmin", permissions)


if __name__ == "__main__":
    unittest.main()
