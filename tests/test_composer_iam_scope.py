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

"""Checks the scope of the IAM grants in the Cloud Composer blueprint."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = (
    _REPO_ROOT / "blueprints/fedramp-high/cloud-composer-environment"
)
_AGENT_MEMBER = "google_project_service_identity.composer_agent.member"
_SUBNETWORK = "data.google_compute_subnetwork.subnetwork"


def _block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _argument(block, name):
    """Returns the expression assigned to a single-line block argument."""
    match = re.search(rf"\n\s*{name}\s*=\s*(.+)\n", block)
    if match is None:
        raise AssertionError(f"Argument not found: {name}")
    return match.group(1).strip()


class TestComposerIamScope(unittest.TestCase):
    def setUp(self):
        self.iam_tf = (_BLUEPRINT_DIR / "iam.tf").read_text(encoding="utf-8")
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")

    def test_network_user_is_granted_on_the_environment_subnetwork(self):
        grant = _block(
            self.iam_tf,
            'resource "google_compute_subnetwork_iam_member" '
            '"composer_network_user"',
        )
        self.assertEqual(
            _argument(grant, "role"), '"roles/compute.networkUser"'
        )
        self.assertEqual(_argument(grant, "member"), _AGENT_MEMBER)
        # The provider block defaults to the main project, so the grant has
        # to name the host project and region of the subnetwork explicitly.
        self.assertEqual(_argument(grant, "project"), f"{_SUBNETWORK}.project")
        self.assertEqual(_argument(grant, "region"), f"{_SUBNETWORK}.region")
        self.assertEqual(_argument(grant, "subnetwork"), f"{_SUBNETWORK}.name")

    def test_project_level_grants_are_limited_to_the_documented_set(self):
        grants = {
            name: (_argument(body, "project"), _argument(body, "role"))
            for name, body in re.findall(
                r'resource "google_project_iam_member" "(\w+)" '
                r"(\{[\s\S]*?\n\})",
                self.iam_tf + self.main_tf,
            )
        }
        # Any project-level grant added here needs a reason why the service
        # cannot take a resource-level binding.
        self.assertEqual(
            grants,
            {
                "composer_worker": (
                    "var.main_project_id",
                    '"roles/composer.worker"',
                ),
                "composer_service_agent": (
                    "var.main_project_id",
                    "var.service_agent_version",
                ),
                "composer_vpc_agent": (
                    "var.network_project_id",
                    '"roles/composer.sharedVpcAgent"',
                ),
            },
        )

    def test_environment_waits_for_every_grant(self):
        environment = _block(
            self.main_tf, 'resource "google_composer_environment" "main"'
        )
        depends_on = re.search(r"depends_on\s*=\s*\[([\s\S]*?)\]", environment)
        self.assertIsNotNone(depends_on)
        dependencies = {
            dep.strip() for dep in depends_on.group(1).split(",") if dep.strip()
        }
        for address in (
            "google_project_iam_member.composer_worker",
            "google_project_iam_member.composer_service_agent",
            "google_compute_subnetwork_iam_member.composer_network_user",
            "google_project_iam_member.composer_vpc_agent",
        ):
            self.assertIn(address, dependencies)
        # A dependency on the replaced project-level grant fails the plan
        # with a reference to an undeclared resource.
        self.assertNotIn(
            "google_project_iam_member.composer_network_user", dependencies
        )


if __name__ == "__main__":
    unittest.main()
