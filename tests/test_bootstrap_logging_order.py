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
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BOOTSTRAP_DIR = _REPO_ROOT / "fast/stages-aw/0-bootstrap"


class TestBootstrapLoggingOrder(unittest.TestCase):
    def test_folders_and_workload_depend_on_organization_logging(self):
        org_tf = (_BOOTSTRAP_DIR / "organization.tf").read_text(
            encoding="utf-8"
        )
        for block_header in (
            'resource "google_assured_workloads_workload" "primary"',
            'module "no-compliance-folder"',
            'module "branch-common-services-folder"',
        ):
            with self.subTest(block=block_header):
                pattern = re.compile(
                    re.escape(block_header) + r"\s*\{[\s\S]*?\n\}", re.MULTILINE
                )
                match = pattern.search(org_tf)
                self.assertIsNotNone(match, f"Block not found: {block_header}")
                self.assertIn(
                    "module.organization-logging",
                    match.group(0),
                    f"{block_header} must depend on "
                    "module.organization-logging",
                )

    def test_bootstrap_projects_depend_on_organization_logging(self):
        project_blocks = (
            ("log-export.tf", 'module "log-export-project"'),
            ("automation.tf", 'module "automation-project"'),
            ("billing.tf", 'module "billing-export-project"'),
        )
        for filename, block_header in project_blocks:
            with self.subTest(file=filename, block=block_header):
                content = (_BOOTSTRAP_DIR / filename).read_text(
                    encoding="utf-8"
                )
                pattern = re.compile(
                    re.escape(block_header) + r"\s*\{[\s\S]*?\n\}", re.MULTILINE
                )
                match = pattern.search(content)
                self.assertIsNotNone(match, f"Block not found: {block_header}")
                self.assertIn(
                    "depends_on = [module.organization-logging]",
                    match.group(0),
                    f"{block_header} in {filename} must depend on"
                    " module.organization-logging",
                )

    def test_org_policy_parameters_not_double_encoded(self):
        org_tf = (_BOOTSTRAP_DIR / "organization.tf").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            "parameters = try(jsonencode(r.parameters), null)",
            org_tf,
            "org_policies should not unconditionally jsonencode "
            "string parameters",
        )
        self.assertIn(
            "try(r.parameters, null) != null",
            org_tf,
        )
        self.assertIn(
            "try(tostring(r.parameters), jsonencode(r.parameters))",
            org_tf,
        )

    def test_log_export_project_settings_provisioned_before_cmek(self):
        log_export_tf = (_BOOTSTRAP_DIR / "log-export.tf").read_text(
            encoding="utf-8"
        )
        kms_tf = (_BOOTSTRAP_DIR / "kms.tf").read_text(encoding="utf-8")
        self.assertIn(
            'data "google_logging_project_settings" "log_export"',
            log_export_tf,
        )
        self.assertIn(
            "depends_on = [module.log-export-project]",
            log_export_tf,
        )
        self.assertIn(
            "data.google_logging_project_settings.log_export",
            log_export_tf,
        )
        self.assertIn(
            "data.google_logging_project_settings.log_export[0]"
            ".kms_service_account_id",
            kms_tf,
        )

    def test_logging_location_avoids_checklist_cycle(self):
        main_tf = (_BOOTSTRAP_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertNotIn("local.checklist.location", main_tf)
        self.assertIn(
            "logging = var.regions.primary",
            main_tf,
        )

    def test_only_the_organization_sets_logging_settings(self):
        # Folders inherit the organization settings. Folder settings without
        # a KMS key fail under regimes that enforce CMEK for Logging.
        org_tf = (_BOOTSTRAP_DIR / "organization.tf").read_text(
            encoding="utf-8"
        )
        blocks = {
            header: re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", org_tf)
            for header in (
                'module "organization-logging"',
                'module "no-compliance-folder"',
                'module "branch-common-services-folder"',
            )
        }
        for header, match in blocks.items():
            self.assertIsNotNone(match, f"Block not found: {header}")
        self.assertIn(
            "logging_settings", blocks['module "organization-logging"'].group(0)
        )
        for header in (
            'module "no-compliance-folder"',
            'module "branch-common-services-folder"',
        ):
            with self.subTest(block=header):
                self.assertNotIn("logging_settings", blocks[header].group(0))

    def test_automation_project_protects_bootstrap_service_accounts(self):
        automation_tf = (_BOOTSTRAP_DIR / "automation.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn("sa_admin_scoped", automation_tf)
        self.assertIn("sa_token_creator_devops", automation_tf)
        self.assertIn(
            "!resource.name.endsWith('/serviceAccounts/%s')",
            automation_tf,
        )

    def test_stage0_checklist_bucket_configures_cmek_and_force_destroy(self):
        """Checklist GCS bucket configures CMEK encryption and force_destroy."""
        # Arrange
        checklist_tf = (_BOOTSTRAP_DIR / "checklist.tf").read_text(
            encoding="utf-8"
        )

        # Act
        match = re.search(
            r'module\s+"automation-tf-checklist-gcs"\s*\{(.*?)^\}',
            checklist_tf,
            re.DOTALL | re.MULTILINE,
        )

        # Assert
        self.assertIsNotNone(match)
        block = match.group(1)
        self.assertIn("encryption_key = module.gcs-kms.keys.gcs.id", block)
        self.assertIn("force_destroy  = var.force_destroy", block)

    def test_stage0_custom_firewall_constraint_blocks_any_open_cidr(self):
        """Custom firewall constraint checks whether any source CIDR is open."""
        # Arrange
        net_constraint = (
            _BOOTSTRAP_DIR / "data/custom-constraint-policies/networking.yaml"
        ).read_text(encoding="utf-8")

        # Act & Assert
        self.assertIn(
            (
                "resource.sourceRanges.exists("
                "range, range == '0.0.0.0/0' || range == '::/0')"
            ),
            net_constraint,
        )

    def test_stage0_storage_viewer_custom_role_excludes_object_create(self):
        """Read-only storage_viewer role excludes storage.objects.create."""
        # Arrange
        storage_viewer = (
            _BOOTSTRAP_DIR / "data/custom-roles/storage_viewer.yaml"
        ).read_text(encoding="utf-8")

        # Act & Assert
        self.assertNotIn("storage.objects.create", storage_viewer)

    def test_stage1_tenant_folder_iam_uses_tenant_key_and_merged_bindings(self):
        """Stage 1 tenant IAM uses each.key and merges folder bindings."""
        # Arrange
        resman_dir = _REPO_ROOT / "fast" / "stages-aw" / "1-resman"
        tenants_tf = (resman_dir / "branch-tenants.tf").read_text(
            encoding="utf-8"
        )

        # Act & Assert
        self.assertNotIn("each.value.tenant.name", tenants_tf)
        self.assertNotIn(
            'resource "google_folder_iam_binding" "tenant_core_iam"', tenants_tf
        )
        self.assertNotIn(
            'resource "google_folder_iam_binding" "tenant_self_iam"', tenants_tf
        )


if __name__ == "__main__":
    unittest.main()
