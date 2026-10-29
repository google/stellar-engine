# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for Gemini Enterprise compliance and deployment script fixes."""

import ast
import pathlib
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import gem4gov

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
GEM4GOV_PATH = REPO_ROOT / "blueprints/gemini-enterprise/gem4gov-cli/gem4gov.py"


class TestGeminiEnterpriseFixes(unittest.TestCase):
    """Verify Gemini Enterprise CLI, Terraform, and deploy.sh fixes."""

    def test_engine_patch_omits_immutable_disable_analytics(self):
        """Ensure update-compliance PATCH omits disableAnalytics (#259)."""
        content = GEM4GOV_PATH.read_text(encoding="utf-8")
        tree = ast.parse(content)
        self.assertNotIn(
            'engine_update_mask = "features,disableAnalytics"',
            content,
            "engine_update_mask must not include immutable disableAnalytics",
        )

        func_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "configure_gemini_enterprise_for_regime"
        )
        func_src = ast.get_source_segment(content, func_node)
        self.assertIn('engine_update_mask = "features"', func_src)
        self.assertNotIn('"disableAnalytics": True', func_src)
        self.assertIn("sys.exit(1)", func_src)

        for wrapper_name in (
            "configure_gemini_enterprise_for_fedramp_high",
            "configure_gemini_enterprise_for_il4",
            "configure_gemini_enterprise_for_il5",
        ):
            wrapper_node = next(
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == wrapper_name
            )
            wrapper_src = ast.get_source_segment(content, wrapper_node)
            self.assertIn(
                "configure_gemini_enterprise_for_regime(", wrapper_src
            )
            self.assertNotIn('"disableAnalytics": True', wrapper_src)

    def test_compliance_regime_respected_in_terraform_and_cli(self):
        """Ensure discovery-engine.tf and gem4gov.py respect regime (#190)."""
        tf_path = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-0/discovery-engine.tf"
        )
        tf_content = tf_path.read_text(encoding="utf-8")
        self.assertIn("features = merge(", tf_content)
        self.assertIn('var.compliance_regime != "NONE" ? {', tf_content)

        py_content = GEM4GOV_PATH.read_text(encoding="utf-8")
        create_engine = next(
            node
            for node in ast.parse(py_content).body
            if isinstance(node, ast.FunctionDef)
            and node.name == "create_engine"
        )
        self.assertEqual(
            [arg.arg for arg in create_engine.args.args],
            [
                "credentials",
                "project_id",
                "engine_id",
                "display_name",
                "company_name",
                "data_store_list",
                "enable_audit_logs",
                "compliance_regime",
            ],
        )
        self.assertEqual(
            [ast.literal_eval(d) for d in create_engine.args.defaults],
            [False, None],
        )
        self.assertIn(
            'is_regulated = compliance_regime not in ("5", "NONE")', py_content
        )
        self.assertNotIn("updateMask=agentConfigs", py_content)

    def test_deploy_sh_validates_observability_and_assistant_patch(self):
        """Ensure deploy.sh validates HTTP status on PATCH (#182)."""
        deploy_sh = (
            REPO_ROOT / "blueprints/gemini-enterprise/deploy.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("OBS_RESPONSE=$(curl -s -w", deploy_sh)
        self.assertIn(".observabilityConfig.sensitiveLoggingEnabled", deploy_sh)
        self.assertIn("ASST_RESPONSE=$(curl -s -w", deploy_sh)

    def test_time_access_level_timezone_and_preservation(self):
        """Ensure time access level and deploy.sh use access_time_zone."""
        access_policy_tf = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-0/access_policy.tf"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'title  = "Business Hours (${var.access_time_zone})"',
            access_policy_tf,
        )
        self.assertNotIn("Business Hours East Coast", access_policy_tf)

        variables_tf = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-0/variables.tf"
        ).read_text(encoding="utf-8")
        self.assertIn("configured access_time_zone", variables_tf)

        deploy_sh = (
            REPO_ROOT / "blueprints/gemini-enterprise/deploy.sh"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "grep '^access_time_zone' gemini-stage-0/terraform.tfvars",
            deploy_sh,
        )
        self.assertIn(
            "grep '^access_expiration_timestamp' "
            "gemini-stage-0/terraform.tfvars",
            deploy_sh,
        )

    def test_deploy_sh_prioritizes_tenant_iac_state_bucket(self):
        """Ensure deploy.sh checks tenant IaC state bucket first (#230)."""
        deploy_sh = (
            REPO_ROOT / "blueprints/gemini-enterprise/deploy.sh"
        ).read_text(encoding="utf-8")
        iac_var = 'IAC_STATE_BUCKET="${PREFIX}-${ENVIRONMENT}-${TENANT}-iac-0"'
        core_var = (
            'LEGACY_CORE_BUCKET="${PREFIX}-tn-${ENVIRONMENT}-${TENANT}-0"'
        )
        iac_idx = deploy_sh.find(iac_var)
        core_idx = deploy_sh.find(core_var)
        self.assertNotEqual(iac_idx, -1)
        self.assertNotEqual(core_idx, -1)
        self.assertIn(
            'if gcloud storage buckets describe "gs://${IAC_STATE_BUCKET}"',
            deploy_sh,
        )
        self.assertIn(
            'elif gcloud storage buckets describe "gs://${LEGACY_CORE_BUCKET}"',
            deploy_sh,
        )

    def test_deploy_sh_uses_existing_compatible_terraform_before_tfenv(self):
        """Ensure check_dependencies uses compatible terraform >= 1.7.4."""
        deploy_sh = (
            REPO_ROOT / "blueprints/gemini-enterprise/deploy.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('local tf_compatible="false"', deploy_sh)
        self.assertIn(
            'printf "%s\\n1.7.4\\n" "$tf_ver" | sort -V | head -n 1', deploy_sh
        )
        self.assertIn('if [[ "$tf_compatible" != "true" ]]; then', deploy_sh)

    def test_cloudarmor_and_cli_token_handling(self):
        """Ensure Cloud Armor rules deny matches and CLI uses stdin tokens."""
        cloudarmor_tf = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-0/cloudarmor.tf"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            'action   = "allow"\n      priority = rules.value.priority',
            cloudarmor_tf,
        )
        self.assertIn(
            'action   = "deny(403)"\n      priority = rules.value.priority',
            cloudarmor_tf,
        )

        py_content = GEM4GOV_PATH.read_text(encoding="utf-8")
        self.assertNotRegex(
            py_content, r'"-H",\s*f"Authorization: Bearer \{access_token\}"'
        )
        self.assertRegex(py_content, r'"-H",\s*"@-"')

    def test_relocation_and_multi_regime_compliance_support(self):
        """Ensure gemini-enterprise supports target regimes (#99, #102, #18)."""
        self.assertTrue(
            (REPO_ROOT / "blueprints/gemini-enterprise").is_dir(),
            "blueprints/gemini-enterprise directory must exist",
        )
        self.assertFalse(
            (REPO_ROOT / "blueprints/fedramp-high/gemini-enterprise").exists(),
            "blueprints/fedramp-high/gemini-enterprise must be relocated",
        )

        expected_regimes = (
            "FEDRAMP_MODERATE",
            "FEDRAMP_HIGH",
            "IL4",
            "IL5",
            "NONE",
        )
        variables_tf = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-0/variables.tf"
        ).read_text(encoding="utf-8")
        deploy_sh = (
            REPO_ROOT / "blueprints/gemini-enterprise/deploy.sh"
        ).read_text(encoding="utf-8")
        py_content = GEM4GOV_PATH.read_text(encoding="utf-8")

        for regime in expected_regimes:
            self.assertIn(f'"{regime}"', variables_tf)
            self.assertIn(regime, deploy_sh)
            self.assertIn(f'"{regime}"', py_content)

        self.assertIn("1) FedRAMP High", py_content)
        self.assertIn("2) FedRAMP Moderate", py_content)
        self.assertIn("3) IL4", py_content)
        self.assertIn("4) IL5", py_content)
        self.assertIn("5) None", py_content)

        main_tf = (
            REPO_ROOT / "blueprints/gemini-enterprise/gemini-stage-0/main.tf"
        ).read_text(encoding="utf-8")
        model_armor_tf = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-0/model_armor.tf"
        ).read_text(encoding="utf-8")
        il_guard = '!contains(["IL4", "IL5"], var.compliance_regime)'
        self.assertIn(il_guard, main_tf)
        self.assertIn(il_guard, model_armor_tf)
        self.assertIn('_STATE_PROTECTION_LEVEL="software"', deploy_sh)
        self.assertLess(
            deploy_sh.index("--- Compliance Regime (Assured Workloads) ---"),
            deploy_sh.index("if ! ensure_prerequisites; then"),
        )

    def test_brownfield_cmek_discovery_and_stage1_hardening(self):
        """Verify Brownfield CMEK discovery and Stage 1 preconditions."""
        deploy_sh = (
            REPO_ROOT / "blueprints/gemini-enterprise/deploy.sh"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'POTENTIAL_SEC_PROJECT="${PREFIX}-${ENVIRONMENT}-sec-core-0"',
            deploy_sh,
        )
        kr_loop = (
            'for CANDIDATE_KR in "${ENVIRONMENT}-us" '
            '"${CAP_ENV}-${TENANT}-keyring"; do'
        )
        self.assertIn(kr_loop, deploy_sh)
        self.assertNotIn(
            "2. User Role Groups: Created admin/user groups", deploy_sh
        )
        self.assertIn("CONFIRM_IDENTITY_GROUPS", deploy_sh)
        self.assertIn(
            "1) Provision a new regional SSL certificate via Terraform",
            deploy_sh,
        )
        self.assertIn(
            'ssl_certificate_path = "${SSL_CERTIFICATE_PATH}"', deploy_sh
        )
        self.assertIn(
            'ssl_private_key_path = "${SSL_PRIVATE_KEY_PATH}"', deploy_sh
        )
        self.assertIn(
            'for CANDIDATE_REG_KR in "${ENVIRONMENT}-${REGION}"', deploy_sh
        )
        self.assertIn(
            'SSL_CERTIFICATE_PATH="$(realpath "$SSL_CERTIFICATE_PATH")"',
            deploy_sh,
        )

        lb_tf = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-1/load_balancer.tf"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "try(trimspace(data.terraform_remote_state.stage_0.outputs"
            ".network_project_id)",
            lb_tf,
        )
        self.assertIn(
            'resource "google_compute_region_ssl_certificate" '
            '"gemini_enterprise_uploaded_cert"',
            lb_tf,
        )
        self.assertIn("name_prefix =", lb_tf)
        self.assertIn("create_before_destroy = true", lb_tf)
        self.assertIn(
            "When Stage 0 use_shared_vpc is true, network_project_id and "
            "shared_vpc_network_name must be present",
            lb_tf,
        )

        stage1_vars = (
            REPO_ROOT
            / "blueprints/gemini-enterprise/gemini-stage-1/variables.tf"
        ).read_text(encoding="utf-8")
        self.assertIn('variable "ssl_certificate_path"', stage1_vars)
        self.assertIn('variable "ssl_private_key_path"', stage1_vars)

    def test_gem4gov_cli_subcommands_for_bigquery_and_licenses(self):
        """Verify gem4gov BigQuery import and license subcommands."""
        content = GEM4GOV_PATH.read_text(encoding="utf-8")
        self.assertIn("--dataset-id", content)
        self.assertIn("--table-id", content)
        self.assertIn("--id-field", content)
        self.assertIn('@license.command(name="retract")', content)
        self.assertIn('@license.command(name="assign")', content)
        self.assertIn('@license.command(name="unassign")', content)

        mock_creds = MagicMock()
        with (
            patch.object(
                gem4gov, "validate_data_store", return_value={"valid": True}
            ),
            patch.object(gem4gov, "import_bq_documents") as mock_import_bq,
        ):
            gem4gov.import_documents_helper(
                mock_creds,
                project_id="proj-1",
                source_type="bigquery",
                data_store_id="ds-1",
                dataset_id="my_ds",
                table_id="my_tbl",
                id_field="record_uuid",
            )
            mock_import_bq.assert_called_once_with(
                mock_creds,
                "proj-1",
                "ds-1",
                "my_ds",
                "my_tbl",
                {"id": "record_uuid"},
            )

        with patch.object(gem4gov, "build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_ba = (
                mock_service.billingAccounts().billingAccountLicenseConfigs()
            )
            cfg_name = (
                "billingAccounts/012345-6789AB-CDEF01/"
                "billingAccountLicenseConfigs/cfg-main"
            )
            mock_ba.list.return_value.execute.return_value = {
                "billingAccountLicenseConfigs": [
                    {
                        "name": cfg_name,
                        "licenseConfigDistributions": {
                            (
                                "projects/111/locations/us/"
                                "licenseConfigs/lic-111"
                            ): 10,
                            (
                                "projects/222/locations/us/"
                                "licenseConfigs/lic-222"
                            ): 5,
                        },
                    }
                ]
            }
            mock_ba.retractLicenseConfig.return_value.execute.return_value = {
                "retracted": True
            }

            gem4gov._retract_project_licenses(
                mock_creds,
                billing_account="012345-6789AB-CDEF01",
                config_id="cfg-main",
                target_project_numbers="111,222",
                location="us",
                retract_all=True,
            )
            self.assertEqual(mock_ba.retractLicenseConfig.call_count, 2)
            first_call_kwargs = mock_ba.retractLicenseConfig.call_args_list[0][
                1
            ]
            self.assertEqual(
                first_call_kwargs["billingAccountLicenseConfig"], cfg_name
            )
            first_call_body = first_call_kwargs["body"]
            self.assertEqual(
                first_call_body["licenseConfig"],
                "projects/111/locations/us/licenseConfigs/lic-111",
            )
            self.assertTrue(first_call_body["fullRetract"])

        with patch.object(gem4gov, "build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_us = mock_service.projects().locations().userStores()
            batch_update = mock_us.batchUpdateUserLicenses
            batch_update.return_value.execute.return_value = {
                "name": "operations/batch-op-1"
            }

            gem4gov._batch_update_user_licenses(
                mock_creds,
                project_id="proj-1",
                location="us",
                users="alice@example.gov,bob@example.gov",
                license_config_id="lic-abc",
                unassign=False,
            )
            assign_kwargs = mock_us.batchUpdateUserLicenses.call_args[1]
            self.assertEqual(
                assign_kwargs["parent"],
                "projects/proj-1/locations/us/userStores/default_user_store",
            )
            self.assertFalse(
                assign_kwargs["body"]["deleteUnassignedUserLicenses"]
            )
            self.assertEqual(
                len(assign_kwargs["body"]["inlineSource"]["userLicenses"]), 2
            )
            self.assertEqual(
                assign_kwargs["body"]["inlineSource"]["userLicenses"][0][
                    "licenseConfig"
                ],
                "projects/proj-1/locations/us/licenseConfigs/lic-abc",
            )

            gem4gov._batch_update_user_licenses(
                mock_creds,
                project_id="proj-1",
                location="us",
                users="alice@example.gov",
                license_config_id=None,
                unassign=True,
            )
            unassign_kwargs = mock_us.batchUpdateUserLicenses.call_args[1]
            self.assertTrue(
                unassign_kwargs["body"]["deleteUnassignedUserLicenses"]
            )
            self.assertEqual(
                unassign_kwargs["body"]["inlineSource"]["updateMask"],
                "userPrincipal,licenseConfig",
            )


if __name__ == "__main__":
    unittest.main()
