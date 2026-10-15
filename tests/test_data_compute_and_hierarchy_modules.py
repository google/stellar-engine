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

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestModuleAndBlueprintHardening(unittest.TestCase):
    def test_data_compute_and_hierarchy_modules_validations(self):
        """Verify hierarchy, data, storage, and compute module hardening."""
        org_log = (REPO_ROOT / "modules/organization/logging.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "kms_key_name         = var.logging_settings.kms_key_name", org_log
        )

        proj_cmek = (REPO_ROOT / "modules/project/cmek.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '"${service}-key-${index}.'
            '${local._aliased_service_agents[dep].name}"',
            proj_cmek,
        )

        proj_vpc_sc = (REPO_ROOT / "modules/project/vpc-sc.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "try(var.vpc_sc.perimeter_bridges, [])",
            proj_vpc_sc,
        )

        pf_auto = (
            REPO_ROOT / "modules/project-factory/automation.tf"
        ).read_text(encoding="utf-8")
        self.assertIn('each.value, "versioning", true', pf_auto)

        alloydb_main = (REPO_ROOT / "modules/alloydb/main.tf").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            alloydb_main.count('dynamic "client_connection_config"'), 4
        )
        self.assertEqual(
            alloydb_main.count('dynamic "query_insights_config"'), 4
        )

        bt_main = (REPO_ROOT / "modules/bigtable-instance/main.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn('"${v.table}-${v.column_family}"', bt_main)

        binauthz_main = (REPO_ROOT / "modules/binauthz/main.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "google_binary_authorization_attestor.attestors[attestor].id",
            binauthz_main,
        )
        self.assertIn(
            "google_container_analysis_note.notes[each.key].id", binauthz_main
        )

        cf1_bundle = (
            REPO_ROOT / "modules/cloud-function-v1/bundle.tf"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "try(fileexists(pathexpand(var.bundle_config.path)), false)",
            cf1_bundle,
        )
        cf2_bundle = (
            REPO_ROOT / "modules/cloud-function-v2/bundle.tf"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "try(fileexists(pathexpand(var.bundle_config.path)), false)",
            cf2_bundle,
        )

        gke_np_main = (REPO_ROOT / "modules/gke-nodepool/main.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn("coalesce(var.node_config.metadata, {})", gke_np_main)

        wf_iam = (REPO_ROOT / "modules/workflows/iam.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn('resource "google_project_iam_member" "bindings"', wf_iam)

        ws_vars = (
            REPO_ROOT / "modules/workstation-cluster/variables.tf"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "disable_public_ip_addresses  = optional(bool, true)", ws_vars
        )
        self.assertIn("enable_private_endpoint = optional(bool, true)", ws_vars)


if __name__ == "__main__":
    unittest.main()
