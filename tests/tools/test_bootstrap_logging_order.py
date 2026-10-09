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

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_BOOTSTRAP_DIR = _REPO_ROOT / 'fast/stages-aw/0-bootstrap'


class TestBootstrapLoggingOrder(unittest.TestCase):

  def test_folders_and_workload_depend_on_organization_logging(self):
    org_tf = (_BOOTSTRAP_DIR / 'organization.tf').read_text(encoding='utf-8')
    for block_header in (
        'resource "google_assured_workloads_workload" "primary"',
        'module "no-compliance-folder"',
        'module "branch-common-services-folder"',
    ):
      with self.subTest(block=block_header):
        pattern = re.compile(
            re.escape(block_header) + r'\s*\{[\s\S]*?\n\}', re.MULTILINE
        )
        match = pattern.search(org_tf)
        self.assertIsNotNone(match, f'Block not found: {block_header}')
        self.assertIn(
            'module.organization-logging',
            match.group(0),
            f'{block_header} must depend on module.organization-logging',
        )

  def test_bootstrap_projects_depend_on_organization_logging(self):
    project_blocks = (
        ('log-export.tf', 'module "log-export-project"'),
        ('automation.tf', 'module "automation-project"'),
        ('billing.tf', 'module "billing-export-project"'),
    )
    for filename, block_header in project_blocks:
      with self.subTest(file=filename, block=block_header):
        content = (_BOOTSTRAP_DIR / filename).read_text(encoding='utf-8')
        pattern = re.compile(
            re.escape(block_header) + r'\s*\{[\s\S]*?\n\}', re.MULTILINE
        )
        match = pattern.search(content)
        self.assertIsNotNone(match, f'Block not found: {block_header}')
        self.assertIn(
            'depends_on = [module.organization-logging]',
            match.group(0),
            f'{block_header} in {filename} must depend on'
            ' module.organization-logging',
        )

  def test_org_policy_parameters_not_double_encoded(self):
    org_tf = (_BOOTSTRAP_DIR / 'organization.tf').read_text(encoding='utf-8')
    self.assertNotIn(
        'parameters = try(jsonencode(r.parameters), null)',
        org_tf,
        'org_policies should not unconditionally jsonencode string parameters',
    )
    self.assertIn(
        'try(r.parameters, null) != null',
        org_tf,
    )
    self.assertIn(
        'try(tostring(r.parameters), jsonencode(r.parameters))',
        org_tf,
    )

  def test_log_export_project_settings_provisioned_before_cmek(self):
    log_export_tf = (_BOOTSTRAP_DIR / 'log-export.tf').read_text(
        encoding='utf-8'
    )
    kms_tf = (_BOOTSTRAP_DIR / 'kms.tf').read_text(encoding='utf-8')
    self.assertIn(
        'data "google_logging_project_settings" "log_export"',
        log_export_tf,
    )
    self.assertIn(
        'depends_on = [module.log-export-project]',
        log_export_tf,
    )
    self.assertIn(
        'data.google_logging_project_settings.log_export',
        log_export_tf,
    )
    self.assertIn(
        'data.google_logging_project_settings.log_export[0].kms_service_account_id',
        kms_tf,
    )

  def test_logging_location_avoids_checklist_cycle(self):
    main_tf = (_BOOTSTRAP_DIR / 'main.tf').read_text(encoding='utf-8')
    self.assertNotIn('local.checklist.location', main_tf)
    self.assertIn(
        'logging = var.regions.primary',
        main_tf,
    )

  def test_delegated_iam_conditions_guard_empty_grant_list(self):
    for rel_path in (
        'fast/stages-aw/0-bootstrap/organization.tf',
        'fast/stages-aw/0-bootstrap/automation.tf',
        'fast/stages-aw/3-security/main.tf',
    ):
      content = (_REPO_ROOT / rel_path).read_text(encoding='utf-8')
      self.assertIn(
          "api.getAttribute('iam.googleapis.com/modifiedGrantsByRole', []).size() > 0",
          content,
      )

  def test_automation_project_protects_bootstrap_service_accounts(self):
    automation_tf = (_BOOTSTRAP_DIR / 'automation.tf').read_text(encoding='utf-8')
    self.assertIn('sa_admin_scoped', automation_tf)
    self.assertIn('sa_token_creator_devops', automation_tf)
    self.assertIn(
        "!resource.name.endsWith('/serviceAccounts/%s')",
        automation_tf,
    )



  def test_kms_rotation_constraint_and_regime_oslogin_and_resman_org_policies(self):
    """Verify custom.kmsRotation allows key destruction (#14), requireOsLogin skips IL4/IL5 (#9), and 1-resman supports org_policies (#197)."""
    import yaml

    kms_yaml_path = _REPO_ROOT / "fast/stages-aw/0-bootstrap/data/custom-constraint-policies/cloudkms.yaml"
    kms_data = yaml.safe_load(kms_yaml_path.read_text(encoding="utf-8"))
    self.assertIn("custom.kmsRotation", kms_data)
    self.assertEqual(kms_data["custom.kmsRotation"]["method_types"], ["CREATE"])
    self.assertEqual(
        kms_data["custom.kmsRotation"]["resource_types"],
        ["cloudkms.googleapis.com/CryptoKey"],
    )
    self.assertEqual(kms_data["custom.kmsRotation"]["action_type"], "ALLOW")

    static_compute_path = _REPO_ROOT / "fast/stages-aw/0-bootstrap/data/org-policies/compute_policy.yaml"
    static_compute = yaml.safe_load(static_compute_path.read_text(encoding="utf-8"))
    self.assertNotIn("compute.requireOsLogin", static_compute)
    self.assertIn("compute.requireShieldedVm", static_compute)

    custom_compute_text = (
        _REPO_ROOT / "fast/stages-aw/0-bootstrap/data/custom-org-policies/compute_policy.yaml"
    ).read_text(encoding="utf-8")
    self.assertIn("compute.requireOsLogin:", custom_compute_text)
    for excluded_regime in ["IL4", "IL5", "ASSURED_WORKLOADS_IL4", "ASSURED_WORKLOADS_IL5"]:
      self.assertIn(excluded_regime, custom_compute_text)
    self.assertIn("%{ else ~}\n{}\n%{ endif ~}", custom_compute_text)

    org_tf = (_REPO_ROOT / "fast/stages-aw/0-bootstrap/organization.tf").read_text(encoding="utf-8")
    self.assertIn("try(coalesce(yamldecode(templatefile(", org_tf)

    resman_vars = (_REPO_ROOT / "fast/stages-aw/1-resman/variables.tf").read_text(encoding="utf-8")
    self.assertIn("org_policies_data_path = optional(string)", resman_vars)
    self.assertIn("main_project_org_policies = optional(map(any), {})", resman_vars)

    envs_tf = (_REPO_ROOT / "fast/stages-aw/1-resman/branch-envs.tf").read_text(encoding="utf-8")
    self.assertIn("org_policies = coalesce(try(each.value.org_policies, null), {})", envs_tf)
    self.assertIn("? { org_policies = each.value.org_policies_data_path }", envs_tf)

    tenants_tf = (_REPO_ROOT / "fast/stages-aw/1-resman/branch-tenants.tf").read_text(encoding="utf-8")
    self.assertIn("org_policies = coalesce(try(each.value.tenant_info.org_policies, null), {})", tenants_tf)
    self.assertIn("? { org_policies = each.value.tenant_info.org_policies_data_path }", tenants_tf)


if __name__ == '__main__':
  unittest.main()


