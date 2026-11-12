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
_RESMAN_DIR = _REPO_ROOT / "fast/stages-aw/1-resman"


class TestBootstrapResmanFixes(unittest.TestCase):
    def test_restrict_firewall_ranges_uses_exists_and_blocks_ipv6(self):
        networking_yaml = (
            _BOOTSTRAP_DIR / "data/custom-constraint-policies/networking.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("action_type: DENY", networking_yaml)
        self.assertNotIn("sourceRanges.all(", networking_yaml)
        self.assertIn(
            "resource.sourceRanges.exists("
            "range, range == '0.0.0.0/0' || range == '::/0')",
            networking_yaml,
        )

    def test_storage_viewer_custom_role_is_read_only(self):
        role_yaml = (
            _BOOTSTRAP_DIR / "data/custom-roles/storage_viewer.yaml"
        ).read_text(encoding="utf-8")
        perms = [
            line.strip().removeprefix("- ").strip()
            for line in role_yaml.splitlines()
            if line.strip().startswith("- ")
        ]
        self.assertTrue(perms)
        self.assertNotIn("storage.objects.create", perms)
        for perm in perms:
            action = perm.rsplit(".", 1)[-1]
            self.assertTrue(
                action.startswith(("get", "list")),
                f"Unexpected non-read permission in storage_viewer: {perm}",
            )

    def test_stage0_and_stage1_gcs_buckets_configure_cmek_and_force_destroy(
        self,
    ):
        outputs_tf = (_BOOTSTRAP_DIR / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn("gcs = module.gcs-kms.keys.gcs.id", outputs_tf)

        resman_vars = (_RESMAN_DIR / "variables.tf").read_text(encoding="utf-8")
        self.assertIn("kms_keys = optional(object({", resman_vars)

        resman_kms = (_RESMAN_DIR / "kms.tf").read_text(encoding="utf-8")
        self.assertIn("crypto_key_id = var.automation.kms_keys.gcs", resman_kms)

        bucket_checks = (
            (
                _BOOTSTRAP_DIR / "checklist.tf",
                'module "automation-tf-checklist-gcs"',
            ),
            (
                _RESMAN_DIR / "branch-data-platform.tf",
                'module "branch-dp-dev-gcs"',
            ),
            (
                _RESMAN_DIR / "branch-data-platform.tf",
                'module "branch-dp-prod-gcs"',
            ),
            (_RESMAN_DIR / "branch-gcve.tf", 'module "branch-gcve-dev-gcs"'),
            (_RESMAN_DIR / "branch-gcve.tf", 'module "branch-gcve-prod-gcs"'),
            (_RESMAN_DIR / "branch-gke.tf", 'module "branch-gke-dev-gcs"'),
            (_RESMAN_DIR / "branch-gke.tf", 'module "branch-gke-prod-gcs"'),
            (
                _RESMAN_DIR / "branch-project-factory.tf",
                'module "branch-pf-dev-gcs"',
            ),
            (
                _RESMAN_DIR / "branch-project-factory.tf",
                'module "branch-pf-prod-gcs"',
            ),
            (_RESMAN_DIR / "branch-sandbox.tf", 'module "branch-sandbox-gcs"'),
            (_RESMAN_DIR / "branch-teams.tf", 'module "branch-teams-gcs"'),
            (_RESMAN_DIR / "branch-teams.tf", 'module "branch-teams-team-gcs"'),
        )
        for tf_path, header in bucket_checks:
            with self.subTest(file=tf_path.name, module=header):
                content = tf_path.read_text(encoding="utf-8")
                match = re.search(
                    re.escape(header) + r"\s*\{[\s\S]*?\n\}", content
                )
                self.assertIsNotNone(match, f"Block not found: {header}")
                block = match.group(0)
                self.assertIn("force_destroy  = var.force_destroy", block)
                self.assertIn("encryption_key =", block)

    def test_branch_tenants_consolidates_folder_iam_and_keys_by_env_tenant(
        self,
    ):
        branch_tenants = (_RESMAN_DIR / "branch-tenants.tf").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("each.value.tenant.name", branch_tenants)
        self.assertNotIn('module "tenant-core-folders-iam"', branch_tenants)
        self.assertNotIn('module "tenant-self-folders-iam"', branch_tenants)
        self.assertNotIn("removed {", branch_tenants)
        self.assertIn('module "tenant-top-folders-iam"', branch_tenants)
        self.assertIn("local.tenant_iam[k]", branch_tenants)
        for base_role in (
            "roles/cloudasset.owner",
            "roles/compute.xpnAdmin",
            "roles/logging.admin",
            "roles/owner",
            "roles/resourcemanager.folderAdmin",
            "roles/resourcemanager.projectCreator",
            "roles/resourcemanager.tagUser",
            "roles/viewer",
        ):
            self.assertIn(f'"{base_role}"', branch_tenants)

    def test_gitlab_workflow_templates_and_team_cicd_outputs(self):
        gitlab_templates = (
            _BOOTSTRAP_DIR / "templates/workflow-gitlab.yaml",
            _RESMAN_DIR / "templates/workflow-gitlab.yaml",
            _REPO_ROOT / "fast/assets/templates/workflow-gitlab.yaml",
        )
        for tpl_path in gitlab_templates:
            with self.subTest(template=str(tpl_path.relative_to(_REPO_ROOT))):
                content = tpl_path.read_text(encoding="utf-8")
                self.assertNotIn("0-bootstrap-providers.tf", content)
                self.assertNotIn("0-bootstrap-r-providers.tf", content)
                self.assertIn(
                    "TF_PROVIDERS_FILE: ${tf_providers_files.apply}", content
                )
                self.assertIn(
                    "TF_PROVIDERS_FILE: ${tf_providers_files.plan}", content
                )

        outputs_tf = (_RESMAN_DIR / "outputs.tf").read_text(encoding="utf-8")
        attrs_match = re.search(
            r"team_cicd_workflow_attrs\s*=\s*\{[\s\S]*?\n  \}", outputs_tf
        )
        self.assertIsNotNone(attrs_match)
        attrs_block = attrs_match.group(0)
        self.assertIn("service_accounts = {", attrs_block)
        self.assertIn("tf_providers_files = {", attrs_block)

        workflows_match = re.search(
            r"team_cicd_workflows\s*=\s*\{[\s\S]*?\n  \}", outputs_tf
        )
        self.assertIsNotNone(workflows_match)
        self.assertIn("audiences = try(", workflows_match.group(0))

        self.assertNotIn(
            "local.team_cicd_workflow_attrs[k].service_account\n", outputs_tf
        )
        self.assertIn(
            "service_account = "
            "local.team_cicd_workflow_attrs[k].service_accounts",
            outputs_tf,
        )


if __name__ == "__main__":
    unittest.main()
