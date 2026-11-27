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

import subprocess
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from click.testing import CliRunner
import gem4gov


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


if __name__ == "__main__":
    unittest.main()
