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

"""Checks the IAM scope of the Cloud Workstations blueprint."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/fedramp-high/cloud-workstations"
_VM_SA = "module.workstation-vm-sa"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestCloudWorkstationsIam(unittest.TestCase):
    def setUp(self):
        self.iam_tf = (_BLUEPRINT_DIR / "iam.tf").read_text(encoding="utf-8")
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        self.terraform = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(_BLUEPRINT_DIR.glob("*.tf"))
        )

    def test_no_project_level_binding_is_declared_directly(self):
        self.assertNotIn("google_project_iam_member", self.terraform)

    def test_grants_are_never_authoritative(self):
        # Authoritative resources would remove grants that the network and
        # repository owners manage on the same subnetwork and repository.
        self.assertNotRegex(self.terraform, r"_iam_(binding|policy)\b")

    def test_default_compute_service_account_is_not_used(self):
        self.assertNotIn("compute_default_sa", self.terraform)
        self.assertNotIn("-compute@developer", self.terraform)

    def test_network_user_is_scoped_to_the_cluster_subnetwork(self):
        grant = _top_block(
            self.iam_tf,
            'resource "google_compute_subnetwork_iam_member" "network_user"',
        )
        self.assertRegex(
            grant, r'\n\s*role\s*=\s*"roles/compute\.networkUser"\n'
        )
        self.assertRegex(
            grant, r"\n\s*member\s*=\s*local\.workstation_default_sa\n"
        )
        # The grant must name the subnetwork that the cluster attaches to,
        # so both are built from the same project, region and name.
        self.assertRegex(grant, r"\n\s*project\s*=\s*local\.landing_project\n")
        self.assertRegex(grant, r"\n\s*region\s*=\s*var\.region\n")
        self.assertRegex(grant, r"\n\s*subnetwork\s*=\s*var\.subnetwork_name\n")
        self.assertIn(
            'subnetwork = "projects/${local.landing_project}'
            '/regions/${var.region}/subnetworks/${var.subnetwork_name}"',
            self.main_tf,
        )

    def test_landing_project_falls_back_to_the_main_project(self):
        # A deployment without a separate network project keeps its
        # subnetwork in the workstation project.
        self.assertRegex(
            _top_block(self.main_tf, "locals"),
            r"landing_project\s*=\s*var\.network_project_id == null"
            r" \? var\.main_project_id : var\.network_project_id\n",
        )

    def test_repository_is_ignored_without_an_image(self):
        self.assertRegex(
            _top_block(self.main_tf, "locals"),
            r"\n\s*image_repository\s*=\s*"
            r"var\.image == null \? null : var\.image_repository\n",
        )

    def test_reader_is_scoped_to_the_image_repository(self):
        grant = _top_block(
            self.iam_tf,
            'resource "google_artifact_registry_repository_iam_member" '
            '"artifact_registry_reader"',
        )
        self.assertRegex(
            grant, r'\n\s*role\s*=\s*"roles/artifactregistry\.reader"\n'
        )
        self.assertRegex(
            grant,
            r"\n\s*count\s*=\s*local\.image_repository == null \? 0 : 1\n",
        )
        self.assertRegex(
            grant,
            r"\n\s*project\s*=\s*coalesce\("
            r"local\.image_repository\.project_id, var\.main_project_id\)\n",
        )
        self.assertRegex(
            grant, r"\n\s*location\s*=\s*local\.image_repository\.location\n"
        )
        self.assertRegex(
            grant, r"\n\s*repository\s*=\s*local\.image_repository\.name\n"
        )
        self.assertRegex(
            grant,
            r"\n\s*member\s*=\s*" + re.escape(f"{_VM_SA}[0].iam_email") + r"\n",
        )

    def test_vm_account_holds_only_the_log_and_metric_writer_roles(self):
        account = _top_block(self.iam_tf, 'module "workstation-vm-sa"')
        self.assertRegex(
            account,
            r'\n\s*source\s*=\s*"\.\./\.\./\.\./modules/iam-service-account"\n',
        )
        # The account and the repository grant exist under one condition.
        self.assertRegex(
            account,
            r"\n\s*count\s*=\s*local\.image_repository == null \? 0 : 1\n",
        )
        self.assertRegex(
            account, r"\n\s*project_id\s*=\s*var\.main_project_id\n"
        )
        self.assertEqual(
            re.findall(r'"(roles/[^"]+)"', account),
            ["roles/logging.logWriter", "roles/monitoring.metricWriter"],
        )
        self.assertRegex(
            account,
            r"iam_project_roles\s*=\s*\{\s*\(var\.main_project_id\)\s*=\s*\[",
        )

    def test_workstation_vms_run_as_the_account_that_reads_the_image(self):
        workstations = _top_block(self.main_tf, 'module "workstations"')
        # The repository grant only takes effect when the VMs run as the
        # same account, and one() yields null when the account is absent.
        self.assertRegex(
            workstations,
            r"\n\s*service_account\s*=\s*one\("
            + re.escape(f"{_VM_SA}[*].email")
            + r"\)\n",
        )

    def test_cluster_waits_for_the_scoped_grants(self):
        workstations = _top_block(self.main_tf, 'module "workstations"')
        depends_on = re.search(r"depends_on\s*=\s*\[([^\]]*)\]", workstations)
        self.assertIsNotNone(depends_on)
        self.assertEqual(
            [dep.strip() for dep in depends_on.group(1).split(",")],
            [
                "google_kms_crypto_key_iam_member."
                "workstations_sa_kms_permissions",
                "google_kms_crypto_key_iam_member.compute_sa_kms_permissions",
                "google_artifact_registry_repository_iam_member."
                "artifact_registry_reader",
                "google_compute_subnetwork_iam_member.network_user",
                _VM_SA,
            ],
        )

    def test_image_repository_variable_is_optional(self):
        variables_tf = (_BLUEPRINT_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        variable = _top_block(variables_tf, 'variable "image_repository"')
        self.assertRegex(variable, r"\n\s*default\s*=\s*null\n")
        self.assertRegex(variable, r"\n\s*location\s*=\s*string\n")
        self.assertRegex(variable, r"\n\s*name\s*=\s*string\n")
        self.assertRegex(
            variable, r"\n\s*project_id\s*=\s*optional\(string\)\n"
        )


if __name__ == "__main__":
    unittest.main()
