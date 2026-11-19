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
"""Checks the OS Login metadata handling of the FedRAMP networking stage.

Stage 0 enforces compute.requireOsLogin for every regime except IL4 and IL5.
Under that constraint Compute Engine sets enable-oslogin on each new project
and rejects its removal, so the stage must neither create nor destroy a
metadata item for that key on its host projects.
"""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_STAGES = _REPO_ROOT / "fast/stages-aw"
_NET_DIR = _STAGES / "2-networking-a-fedramp"
_COMPUTE_POLICY = (
    _STAGES / "0-bootstrap/data/custom-org-policies/compute_policy.yaml"
)
_RESMAN_SAMPLE = _STAGES / "1-resman/terraform.tfvars.sample"
_LEGACY_ITEM = 'google_compute_project_metadata_item.default["enable-oslogin"]'
_RELEASED = "google_compute_project_metadata_item.oslogin_released"


def _read(name):
    return (_NET_DIR / name).read_text(encoding="utf-8")


def _block(text, header):
    """Returns the body of the first brace block that follows the header."""
    start = text.index(header)
    opening = text.index("{", start + len(header) - 1)
    depth = 0
    for position in range(opening, len(text)):
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return text[opening + 1 : position]
    raise AssertionError(f"unterminated block after {header!r}")


def _code(text):
    """Returns the text without full-line and trailing hash comments."""
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _moves(text):
    return dict(
        re.findall(r"moved \{\s*from\s*=\s*(\S+)\s*to\s*=\s*(\S+)\s*\}", text)
    )


class TestFedrampOsloginMetadata(unittest.TestCase):
    def test_host_project_modules_do_not_set_enable_oslogin(self):
        """Verify compute_metadata keeps SSH key blocking and drops OS Login."""
        for name, module in (
            ("net-hub.tf", 'module "hub-project" {'),
            ("branch-net-envs.tf", 'module "env-spoke-projects" {'),
        ):
            with self.subTest(file=name):
                body = _block(_read(name), module)
                metadata = _code(_block(body, "compute_metadata = {"))
                self.assertRegex(
                    metadata, r'block-project-ssh-keys\s*=\s*"true"'
                )
                self.assertNotIn("enable-oslogin", metadata)
                self.assertIn("google      = google.billing", body)

    def test_regime_gate_matches_stage_0_policy_template(self):
        """Verify the stage skips exactly the regimes Stage 0 constrains."""
        policy = _COMPUTE_POLICY.read_text(encoding="utf-8")
        gate = re.search(
            r"%\{ if !contains\((\[[^\]]*\]), regime\) ~\}\s*"
            r"(?:#[^\n]*\n)*compute\.requireOsLogin:",
            policy,
        )
        self.assertIsNotNone(gate)
        unconstrained = gate.group(1)
        self.assertEqual(unconstrained, '["IL4", "IL5"]')

        managed = _code(_block(_read("oslogin.tf"), "locals {"))
        self.assertIn(f"contains({unconstrained},", managed)
        self.assertIn("var.manage_oslogin_metadata != null", managed)
        self.assertIn("var.assured_workloads.regime == null ||", managed)

    def test_fallback_item_sets_enable_oslogin_on_every_host_project(self):
        """Verify the stage-level item covers the hub and every spoke."""
        oslogin = _read("oslogin.tf")
        resource = _code(
            _block(
                oslogin,
                'resource "google_compute_project_metadata_item" "oslogin" {',
            )
        )
        self.assertRegex(resource, r"provider\s*=\s*google\.billing")
        self.assertRegex(
            resource, r"for_each\s*=\s*local\._oslogin_host_projects"
        )
        self.assertRegex(resource, r'key\s*=\s*"enable-oslogin"')
        self.assertRegex(resource, r'value\s*=\s*"true"')

        projects = _code(_block(oslogin, "locals {"))
        self.assertIn("!local._oslogin_metadata_managed ? {}", projects)
        self.assertIn("hub = module.hub-project.project_id", projects)
        self.assertIn(
            "for k, v in module.env-spoke-projects : lower(k) => v.project_id",
            projects,
        )

    def test_legacy_items_are_released_without_destroy(self):
        """Verify tracked enable-oslogin items leave state and stay in GCP."""
        oslogin = _read("oslogin.tf")
        moves = _moves(oslogin)

        sample = _RESMAN_SAMPLE.read_text(encoding="utf-8")
        envs = re.findall(
            r"^  (\w+) = \{$", _block(sample, "envs_folders = {"), re.M
        )
        self.assertEqual(envs, ["Prod", "Int", "Test"])

        expected = {f"module.hub-project.{_LEGACY_ITEM}": f'{_RELEASED}["hub"]'}
        for env in envs:
            source = f'module.env-spoke-projects["{env}"].{_LEGACY_ITEM}'
            expected[source] = f'{_RELEASED}["{env.lower()}"]'
        self.assertEqual(moves, expected)

        removed = re.findall(r"removed \{(.*?)\n\}", oslogin, re.S)
        self.assertEqual(len(removed), 1)
        self.assertRegex(removed[0], rf"from\s*=\s*{re.escape(_RELEASED)}\n")
        self.assertRegex(removed[0], r"lifecycle \{\s*destroy\s*=\s*false\s*\}")

        # A removed block is only valid while no resource uses its address.
        for path in sorted(_NET_DIR.glob("*.tf")):
            self.assertNotIn(
                '"google_compute_project_metadata_item" "oslogin_released"',
                path.read_text(encoding="utf-8"),
            )

    def test_variable_and_readme_document_the_override(self):
        """Verify the override stays optional and the upgrade is documented."""
        variable = _block(
            _read("variables.tf"), 'variable "manage_oslogin_metadata" {'
        )
        self.assertRegex(variable, r"type\s*=\s*bool")
        self.assertRegex(variable, r"default\s*=\s*null")
        self.assertNotIn("nullable", variable)

        readme = _read("README.md")
        self.assertIn("## 6 Host project OS Login", readme)
        self.assertIn("manage_oslogin_metadata = true", readme)
        self.assertIn(
            "terraform state rm google_compute_project_metadata_item.oslogin`",
            readme,
        )
        self.assertIn(
            'terraform state rm \'module.env-spoke-projects["<Env>"].'
            f"{_LEGACY_ITEM}'",
            readme,
        )
        self.assertIn(
            'to = google_compute_project_metadata_item.oslogin["hub"]', readme
        )
        self.assertIn(
            'id = "projects/<prefix>-net-hub-host/meta-data/enable-oslogin"',
            readme,
        )


if __name__ == "__main__":
    unittest.main()
