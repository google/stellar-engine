# Copyright 2026 Google LLC
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

"""Unit tests for the gem4gov CLI."""

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from click.testing import CliRunner
import gem4gov
import yaml


class TestGem4GovPrivateKnowledgeGraph(unittest.TestCase):
    """Verify Private Knowledge Graph disabling across regulated regimes."""

    @staticmethod
    def _mock_discovery_and_aiplatform():
        de_service = MagicMock()
        engines = de_service.projects().locations().collections().engines()
        engines.create.return_value.execute.return_value = {
            "name": "projects/proj-1/locations/us/engines/eng-1"
        }
        engines.patch.return_value.execute.return_value = {}
        engines.widgetConfigs().get.return_value.execute.return_value = {
            "configId": "cfg-123"
        }

        ai_service = MagicMock()
        update_cache = ai_service.projects().updateCacheConfig
        update_cache.return_value.execute.return_value = {}
        return de_service, ai_service

    def test_configure_regime_disables_private_kg_for_frh_il4_il5(self):
        """Ensure FedRAMP High, IL4, and IL5 patch knowledgeGraphConfig."""
        mock_creds = MagicMock()
        for fn, expected_label in (
            (
                gem4gov.configure_gemini_enterprise_for_fedramp_high,
                "FedRAMP High",
            ),
            (gem4gov.configure_gemini_enterprise_for_il4, "IL4"),
            (gem4gov.configure_gemini_enterprise_for_il5, "IL5"),
        ):
            with self.subTest(regime=expected_label):
                de_service, ai_service = self._mock_discovery_and_aiplatform()

                def build_side_effect(api, *_args, **_kwargs):
                    if api == "discoveryengine":
                        return de_service
                    if api == "aiplatform":
                        return ai_service
                    return MagicMock()

                ok_proc = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="tok\n", stderr=""
                )
                with (
                    patch.object(
                        gem4gov, "build", side_effect=build_side_effect
                    ),
                    patch.object(gem4gov, "disable_user_event_collection"),
                    patch.object(
                        gem4gov.subprocess, "run", return_value=ok_proc
                    ),
                ):
                    fn(mock_creds, "proj-1", "eng-1")

                patch_call = (
                    de_service.projects()
                    .locations()
                    .collections()
                    .engines()
                    .patch
                )
                patch_call.assert_called_once()
                kwargs = patch_call.call_args.kwargs
                self.assertEqual(
                    kwargs["updateMask"], "features,knowledgeGraphConfig"
                )
                self.assertEqual(
                    kwargs["body"]["knowledgeGraphConfig"],
                    {
                        "enablePrivateKnowledgeGraph": False,
                        "enableCloudKnowledgeGraph": False,
                    },
                )
                self.assertIn("features", kwargs["body"])

    def test_configure_regime_keeps_features_mask_for_fedramp_moderate(self):
        """Ensure FedRAMP Moderate keeps features-only updateMask."""
        mock_creds = MagicMock()
        de_service, ai_service = self._mock_discovery_and_aiplatform()

        def build_side_effect(api, *_args, **_kwargs):
            return de_service if api == "discoveryengine" else ai_service

        ok_proc = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="tok\n", stderr=""
        )
        with (
            patch.object(gem4gov, "build", side_effect=build_side_effect),
            patch.object(gem4gov, "disable_user_event_collection"),
            patch.object(gem4gov.subprocess, "run", return_value=ok_proc),
        ):
            gem4gov.configure_gemini_enterprise_for_regime(
                mock_creds, "proj-1", "eng-1", "FedRAMP Moderate"
            )

        kwargs = (
            de_service.projects()
            .locations()
            .collections()
            .engines()
            .patch.call_args.kwargs
        )
        self.assertEqual(kwargs["updateMask"], "features")
        self.assertNotIn("knowledgeGraphConfig", kwargs["body"])

    def test_create_engine_sets_knowledge_graph_config_by_regime(self):
        """Ensure create_engine disables Private KG for FRH, IL4, and IL5."""
        mock_creds = MagicMock()
        for regime, expect_kg in (
            ("1", True),
            ("FEDRAMP_HIGH", True),
            ("3", True),
            ("IL4", True),
            ("4", True),
            ("IL5", True),
            ("2", False),
            ("FEDRAMP_MODERATE", False),
            ("5", False),
            ("NONE", False),
        ):
            with self.subTest(regime=regime):
                de_service, _ = self._mock_discovery_and_aiplatform()
                with patch.object(gem4gov, "build", return_value=de_service):
                    gem4gov.create_engine(
                        mock_creds,
                        "proj-1",
                        "eng-1",
                        "My Engine",
                        "Agency",
                        [],
                        compliance_regime=regime,
                    )

                body = (
                    de_service.projects()
                    .locations()
                    .collections()
                    .engines()
                    .create.call_args.kwargs["body"]
                )
                if expect_kg:
                    self.assertEqual(
                        body["knowledgeGraphConfig"],
                        {
                            "enablePrivateKnowledgeGraph": False,
                            "enableCloudKnowledgeGraph": False,
                        },
                    )
                else:
                    self.assertNotIn("knowledgeGraphConfig", body)

    def test_update_compliance_cli_banners_and_dispatch(self):
        """Verify update-compliance prints accurate unauthorized lists."""
        runner = CliRunner()
        mock_creds = MagicMock()
        for regime, expect_ma in (
            ("FEDRAMP_HIGH", False),
            ("IL4", True),
            ("IL5", True),
        ):
            with self.subTest(regime=regime):
                with (
                    patch.object(
                        gem4gov, "get_credentials", return_value=mock_creds
                    ),
                    patch.object(
                        gem4gov, "configure_gemini_enterprise_for_regime"
                    ) as mock_cfg,
                    patch.object(
                        gem4gov, "get_widget_config_id", return_value="cfg-1"
                    ),
                ):
                    result = runner.invoke(
                        gem4gov.cli,
                        [
                            "app",
                            "update-compliance",
                            "--project-id",
                            "proj-1",
                            "--engine-id",
                            "eng-1",
                            "--compliance-regime",
                            regime,
                        ],
                    )
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn(
                    "Knowledge Graph / People Connectors", result.output
                )
                if expect_ma:
                    self.assertIn("Model Armor", result.output)
                else:
                    self.assertNotIn("Model Armor", result.output)
                mock_cfg.assert_called_once()


class TestGem4GovLicenseAssign(unittest.TestCase):
    """Verify project-number resolution on gem4gov license assign (#445)."""

    def test_bare_license_config_id_resolves_project_number_via_cli(self):
        """Ensure bare --license-config-id expands using project number."""
        runner = CliRunner()
        mock_creds = MagicMock()
        mock_creds.with_quota_project.return_value = mock_creds
        de_service = MagicMock()
        crm_service = MagicMock()
        crm_service.projects().get.return_value.execute.return_value = {
            "projectNumber": "987654321098"
        }
        batch_update = (
            de_service.projects()
            .locations()
            .userStores()
            .batchUpdateUserLicenses
        )
        batch_update.return_value.execute.return_value = {
            "name": "operations/assign-1"
        }

        def build_side_effect(api_name, *_args, **_kwargs):
            return (
                crm_service
                if api_name == "cloudresourcemanager"
                else de_service
            )

        with (
            patch.object(gem4gov, "get_credentials", return_value=mock_creds),
            patch.object(gem4gov, "build", side_effect=build_side_effect),
        ):
            result = runner.invoke(
                gem4gov.cli,
                [
                    "license",
                    "assign",
                    "--project-id",
                    "my-project",
                    "--users",
                    "user@example.com",
                    "--license-config-id",
                    "free_trial_gemini",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        crm_service.projects().get.assert_called_once_with(
            projectId="my-project"
        )
        kwargs = batch_update.call_args.kwargs
        self.assertEqual(
            kwargs["parent"],
            "projects/my-project/locations/us/userStores/default_user_store",
        )
        self.assertEqual(
            kwargs["body"]["inlineSource"]["userLicenses"],
            [
                {
                    "userPrincipal": "user@example.com",
                    "licenseConfig": (
                        "projects/987654321098/locations/us"
                        "/licenseConfigs/free_trial_gemini"
                    ),
                }
            ],
        )

    def test_full_license_config_name_skips_project_number_lookup(self):
        """Ensure full projects/... resource name passes through directly."""
        mock_creds = MagicMock()
        de_service = MagicMock()
        batch_update = (
            de_service.projects()
            .locations()
            .userStores()
            .batchUpdateUserLicenses
        )
        batch_update.return_value.execute.return_value = {"name": "op-2"}
        full_name = (
            "projects/111222333444/locations/us/licenseConfigs/custom_cfg"
        )

        with (
            patch.object(gem4gov, "get_project_number") as mock_proj_num,
            patch.object(gem4gov, "build", return_value=de_service),
        ):
            gem4gov._batch_update_user_licenses(
                mock_creds,
                project_id="my-project",
                location="us",
                users="user@example.com",
                license_config_id=full_name,
                unassign=False,
            )

        mock_proj_num.assert_not_called()
        entry = batch_update.call_args.kwargs["body"]["inlineSource"][
            "userLicenses"
        ][0]
        self.assertEqual(entry["licenseConfig"], full_name)

    def test_missing_project_number_exits_with_error(self):
        """Ensure failed project number lookup exits cleanly."""
        mock_creds = MagicMock()
        with (
            patch.object(gem4gov, "get_project_number", return_value=None),
            patch.object(gem4gov, "build") as mock_build,
            self.assertRaises(SystemExit) as ctx,
        ):
            gem4gov._batch_update_user_licenses(
                mock_creds,
                project_id="my-project",
                location="us",
                users="user@example.com",
                license_config_id="free_trial_gemini",
                unassign=False,
            )

        self.assertEqual(ctx.exception.code, 1)
        mock_build.assert_not_called()

    def test_unassign_skips_project_number_lookup(self):
        """Ensure --unassign does not query Cloud Resource Manager."""
        mock_creds = MagicMock()
        de_service = MagicMock()
        batch_update = (
            de_service.projects()
            .locations()
            .userStores()
            .batchUpdateUserLicenses
        )
        batch_update.return_value.execute.return_value = {"name": "op-3"}

        with (
            patch.object(gem4gov, "get_project_number") as mock_proj_num,
            patch.object(gem4gov, "build", return_value=de_service),
        ):
            gem4gov._batch_update_user_licenses(
                mock_creds,
                project_id="my-project",
                location="us",
                users="user@example.com",
                license_config_id=None,
                unassign=True,
            )

        mock_proj_num.assert_not_called()
        entry = batch_update.call_args.kwargs["body"]["inlineSource"][
            "userLicenses"
        ][0]
        self.assertNotIn("licenseConfig", entry)


class TestGem4GovDefaultsAndValidation(unittest.TestCase):
    """Verify #543 gem4gov-cli defaults, KMS check, schema patch, packaging."""

    def test_engine_features_yaml_disables_agent_sharing(self):
        """Ensure disable-agent-sharing is FEATURE_STATE_ON in config."""
        features = gem4gov._load_engine_features()["features"]
        self.assertEqual(features["disable-agent-sharing"], "FEATURE_STATE_ON")
        self.assertEqual(
            features["agent-sharing-without-admin-approval"],
            "FEATURE_STATE_OFF",
        )

    def test_load_engine_features_falls_back_to_data_prefix(self):
        """Ensure _load_engine_features falls back to sys.prefix/share."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix_dir = Path(tmpdir) / "prefix"
            share_dir = prefix_dir / "share" / "gem4gov"
            share_dir.mkdir(parents=True)
            yaml_file = share_dir / "engine_features.yaml"
            yaml_file.write_text(
                yaml.safe_dump(
                    {"features": {"disable-agent-sharing": "FEATURE_STATE_ON"}}
                ),
                encoding="utf-8",
            )
            fake_script = str(Path(tmpdir) / "site-packages" / "gem4gov.py")
            with (
                patch.object(gem4gov, "__file__", fake_script),
                patch.object(gem4gov.sys, "prefix", str(prefix_dir)),
                patch.object(
                    gem4gov.sysconfig,
                    "get_path",
                    return_value=str(prefix_dir),
                ),
                patch.object(gem4gov.site, "USER_BASE", ""),
            ):
                loaded = gem4gov._load_engine_features()
        self.assertEqual(
            loaded["features"]["disable-agent-sharing"], "FEATURE_STATE_ON"
        )

    def test_setup_py_and_manifest_package_engine_features(self):
        """Ensure setup.py and MANIFEST.in include engine_features.yaml."""
        cli_dir = (
            Path(__file__).resolve().parent.parent
            / "blueprints"
            / "gemini-enterprise"
            / "gem4gov-cli"
        )
        setup_text = (cli_dir / "setup.py").read_text(encoding="utf-8")
        manifest_text = (cli_dir / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("data_files=", setup_text)
        self.assertIn("engine_features.yaml", setup_text)
        self.assertIn("include engine_features.yaml", manifest_text)

    def test_license_distribute_and_retract_default_location_to_us(self):
        """Ensure license distribute and retract default --location to us."""
        runner = CliRunner()
        mock_creds = MagicMock()
        mock_creds.with_quota_project.return_value = mock_creds
        de_service = MagicMock()
        ba_configs = de_service.billingAccounts().billingAccountLicenseConfigs()
        dist_cfg = ba_configs.distributeLicenseConfig
        dist_cfg.return_value.execute.return_value = {}
        ba_configs.retractLicenseConfig.return_value.execute.return_value = {}

        with (
            patch.object(gem4gov, "get_credentials", return_value=mock_creds),
            patch.object(
                gem4gov, "build", return_value=de_service
            ) as mock_build,
        ):
            res_dist = runner.invoke(
                gem4gov.cli,
                [
                    "license",
                    "distribute",
                    "--billing-account",
                    "BA-1",
                    "--config-id",
                    "cfg-1",
                    "--target-project-number",
                    "123456",
                    "--count",
                    "5",
                ],
            )
            res_retract = runner.invoke(
                gem4gov.cli,
                [
                    "license",
                    "retract",
                    "--billing-account",
                    "BA-1",
                    "--config-id",
                    "cfg-1",
                    "--target-project-number",
                    "123456",
                    "--count",
                    "2",
                    "--license-config-id",
                    "lic-1",
                ],
            )

        self.assertEqual(res_dist.exit_code, 0, res_dist.output)
        self.assertEqual(res_retract.exit_code, 0, res_retract.output)
        dist_body = ba_configs.distributeLicenseConfig.call_args.kwargs["body"]
        self.assertEqual(dist_body["location"], "us")
        for call in mock_build.call_args_list:
            self.assertEqual(
                call.kwargs["client_options"].api_endpoint,
                "https://us-discoveryengine.googleapis.com",
            )

    def test_validate_kms_key_checks_locations_segment_strictly(self):
        """Reject substring matches like project 'custom' or 'us-central1'."""
        cases = (
            (
                "projects/custom-proj/locations/us/keyRings/kr/cryptoKeys/k",
                True,
            ),
            (
                "projects/custom-proj/locations/us-central1/keyRings/kr/cryptoKeys/k",
                False,
            ),
            (
                "projects/us-proj/locations/europe-west1/keyRings/kr/cryptoKeys/k",
                False,
            ),
        )
        for resource_name, expected in cases:
            with self.subTest(resource_name=resource_name):
                kms_service = MagicMock()
                keys = (
                    kms_service.projects().locations().keyRings().cryptoKeys()
                )
                keys.get.return_value.execute.return_value = {
                    "name": resource_name,
                    "purpose": "ENCRYPT_DECRYPT",
                    "versionTemplate": {
                        "algorithm": "GOOGLE_SYMMETRIC_ENCRYPTION"
                    },
                }
                with patch.object(gem4gov, "build", return_value=kms_service):
                    self.assertEqual(
                        gem4gov.validate_kms_key(MagicMock(), resource_name),
                        expected,
                    )

    def test_bigquery_import_patches_default_schema_before_import(self):
        """Ensure BQ import calls create_data_store_schema before import."""
        mock_creds = MagicMock()
        sample_bq_schema = {
            "fields": [
                {"name": "doc_id", "type": "STRING"},
                {"name": "body", "type": "STRING"},
            ]
        }
        call_order = []

        def record_schema(*args, **kwargs):
            call_order.append(("schema", args, kwargs))

        def record_import(*args, **kwargs):
            call_order.append(("import", args, kwargs))

        with (
            patch.object(
                gem4gov, "validate_data_store", return_value={"valid": True}
            ),
            patch.object(
                gem4gov, "get_bq_schema", return_value=sample_bq_schema
            ),
            patch.object(
                gem4gov, "create_data_store_schema", side_effect=record_schema
            ),
            patch.object(
                gem4gov, "import_bq_documents", side_effect=record_import
            ),
        ):
            gem4gov.import_documents_helper(
                mock_creds,
                project_id="proj-1",
                source_type="bigquery",
                data_store_id="ds-1",
                dataset_id="ds",
                table_id="tbl",
                id_field="doc_id",
            )

        self.assertEqual([c[0] for c in call_order], ["schema", "import"])
        patched_schema = call_order[0][1][3]
        self.assertIn("doc_id", patched_schema["properties"])
        self.assertIn("body", patched_schema["properties"])

    def test_bigquery_import_handles_missing_schema_gracefully(self):
        """Skip schema patch when get_bq_schema returns None."""
        mock_creds = MagicMock()
        with (
            patch.object(
                gem4gov, "validate_data_store", return_value={"valid": True}
            ),
            patch.object(gem4gov, "get_bq_schema", return_value=None),
            patch.object(
                gem4gov, "create_data_store_schema"
            ) as mock_create_schema,
            patch.object(gem4gov, "import_bq_documents") as mock_import_bq,
        ):
            gem4gov.import_documents_helper(
                mock_creds,
                project_id="proj-1",
                source_type="bigquery",
                data_store_id="ds-1",
                dataset_id="ds",
                table_id="tbl",
                id_field="auto",
            )

        mock_create_schema.assert_not_called()
        mock_import_bq.assert_called_once()


if __name__ == "__main__":
    unittest.main()
