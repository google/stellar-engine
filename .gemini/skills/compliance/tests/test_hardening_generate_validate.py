#!/usr/bin/env python3
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

"""Regression tests for export boundary safety, placeholder hydration, and validator gates."""

import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import docx_generator
import excel_hydrator
import poam_rules
import semantic_linter
import template_engine
import validate_compliance_artifacts


class TestHardeningGenerateValidate(unittest.TestCase):
    """Covers export boundary safety, placeholder hydration, and validator gates."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sec_b_f1_validator_pta_docx_symlink_rejected(self) -> None:
        """Planted symlink at Path_to_Authorization.docx must be rejected."""
        outside_target = self.root / "outside_victim.docx"
        outside_target.write_bytes(b"ORIGINAL_VICTIM_CONTENT")

        ws = self.root / "workspace"
        ato_dir = ws / "ato_artifacts"
        ato_dir.mkdir(parents=True)
        (ws / "system_inventory.json").write_text(
            '{"system_information": {"system_name": "TestSys"}}',
            encoding="utf-8",
        )
        os.symlink(outside_target, ato_dir / "Path_to_Authorization.docx")

        with self.assertRaises(PermissionError):
            validate_compliance_artifacts.validate_compliance_package(
                str(ws), run_linter=False
            )
        self.assertEqual(outside_target.read_bytes(), b"ORIGINAL_VICTIM_CONTENT")

    def test_sec_b_f2_backup_artifact_package_skips_symlinks_and_uses_microseconds(self) -> None:
        """_backup_artifact_package must skip symlinks and avoid 1s collisions."""
        secret_file = self.root / "secret_outside.txt"
        secret_file.write_text("TOP_SECRET_DO_NOT_COPY", encoding="utf-8")

        ato_dir = self.root / "ato_artifacts"
        ato_dir.mkdir()
        (ato_dir / "legit.md").write_text("# Legit", encoding="utf-8")
        os.symlink(secret_file, ato_dir / "planted_link.md")

        b1 = validate_compliance_artifacts._backup_artifact_package(str(ato_dir))
        b2 = validate_compliance_artifacts._backup_artifact_package(str(ato_dir))
        self.assertNotEqual(b1, b2)
        self.assertTrue((Path(b1) / "legit.md").exists())
        self.assertFalse((Path(b1) / "planted_link.md").exists())

    def test_sec_b_f3_excel_zip_bomb_rejected(self) -> None:
        """audit_excel_workbooks must reject archives exceeding uncompressed size limits."""
        ato_dir = self.root / "ato_artifacts"
        ato_dir.mkdir()
        xl_path = ato_dir / "Hardware_Software_Inventory.xlsm"
        with zipfile.ZipFile(xl_path, "w") as zf:
            zf.writestr("xl/workbook.xml", "<workbook/>")

        fake_info = MagicMock()
        fake_info.filename = "xl/worksheets/sheet1.xml"
        fake_info.file_size = 150 * 1024 * 1024
        fake_info.compress_size = 100
        with patch("zipfile.ZipFile.infolist", return_value=[fake_info]):
            results = validate_compliance_artifacts.audit_excel_workbooks(str(ato_dir))
        self.assertEqual(len(results), 1)
        self.assertIn(results[0]["status"], ("FAIL", "UNVERIFIED"))
        self.assertTrue(
            any("exceeds safe size/compression limits" in i for i in results[0]["issues"])
        )

    def test_sec_b_f4_f5_hyperlink_schemes_and_relative_paths(self) -> None:
        """Reject scheme-less relative files, triple-slash http:/// and malformed mailto:."""
        mgr = docx_generator.DocxRelationshipManager()
        self.assertEqual(mgr.add_hyperlink("../secret.docx"), "")
        self.assertEqual(mgr.add_hyperlink("sub/doc.pdf"), "")
        self.assertEqual(mgr.add_hyperlink("http:///etc/passwd"), "")
        self.assertEqual(mgr.add_hyperlink("https:///etc/passwd"), "")
        self.assertEqual(mgr.add_hyperlink("mailto:not-an-email/../../path"), "")
        self.assertTrue(mgr.add_hyperlink("#valid-anchor").startswith("rId"))
        self.assertTrue(mgr.add_hyperlink("https://cloud.google.com/security").startswith("rId"))
        self.assertTrue(mgr.add_hyperlink("mailto:isso@agency.gov").startswith("rId"))

    def test_code_b_01_05_template_engine_unfilled_placeholders_and_yaml_quoting(self) -> None:
        """Bracketed sample placeholders and single-pass YAML replacement."""
        self.assertTrue(template_engine.is_unfilled_placeholder("[YOUR_ORG_NAME]"))
        self.assertTrue(template_engine.is_unfilled_placeholder("[YYYY-MM-DD]"))
        self.assertTrue(template_engine.is_unfilled_placeholder("FR-XXXXXXXX"))
        self.assertTrue(template_engine.is_unfilled_placeholder("FR9999999999"))
        self.assertFalse(template_engine.is_unfilled_placeholder("FR1805751477"))

        yaml_text = 'owner: "[CONFIG_REQUIRED: Owner Name]"\nstatus: [CONFIG_REQUIRED: Status]\n'
        hydrated = template_engine.TemplateEngine.hydrate_legacy_placeholders(
            yaml_text, is_yaml=True
        )
        self.assertNotIn('""[EXAMPLE_DATA_REQUIRED:', hydrated)
        self.assertIn('owner: "[EXAMPLE_DATA_REQUIRED: Owner Name]"', hydrated)

    def test_code_b_02_sctm_hydrator_expands_narrative_macros(self) -> None:
        """SCTM Excel hydration must expand {{ ... }} tokens in control narratives."""
        tpl = (
            Path(SCRIPTS_DIR).parent
            / "templates"
            / "sctm"
            / "ControlInfoExport_Template.xlsm"
        )
        out_xl = self.root / "SCTM_Test.xlsm"
        inv = {
            "system_information": {
                "system_name": "MacroTestSystem",
                "system_abbreviation": "MTS",
                "organization": "TestOrg",
                "impact_level": "IL5",
            },
            "security_operations": {"scc_enabled": False},
        }
        hydrator = excel_hydrator.SCTMHydrator(str(tpl))
        hydrator.hydrate(inv, str(out_xl), allowed_boundary=str(self.root))

        audit_dir = self.root / "audit_sctm"
        audit_dir.mkdir()
        shutil.copy2(out_xl, audit_dir / "SCTM_Control_Matrix.xlsm")
        res = validate_compliance_artifacts.audit_excel_workbooks(str(audit_dir))
        self.assertEqual(len(res), 1)
        token_issues = [i for i in res[0]["issues"] if "Unresolved macro token" in i]
        self.assertEqual(token_issues, [])

    def test_code_c_03_validate_returns_false_on_unresolved_tokens_when_strict(self) -> None:
        """validate_compliance_package fails closed on unresolved tokens and packaging failures."""
        ws = self.root / "ws_strict"
        ato_dir = ws / "ato_artifacts"
        ato_dir.mkdir(parents=True)
        (ws / "system_inventory.json").write_text(
            '{"system_information": {"system_name": "StrictSys"}}',
            encoding="utf-8",
        )
        (ato_dir / "broken.md").write_text(
            "# Broken\nUnresolved {{ UNKNOWN_MACRO_TOKEN }} here.\n",
            encoding="utf-8",
        )
        self.assertFalse(
            validate_compliance_artifacts.validate_compliance_package(
                str(ws), run_linter=False, linter_strict=True
            )
        )
        self.assertFalse(
            validate_compliance_artifacts.validate_compliance_package(
                str(ws), run_linter=False, linter_strict=False
            )
        )

        # Packaging failure (missing word/document.xml) with zero unresolved tokens must also return False
        ws_pkg = self.root / "ws_pkg_fail"
        ato_pkg = ws_pkg / "ato_artifacts"
        (ato_pkg / "Policies_and_Procedures").mkdir(parents=True)
        (ws_pkg / "system_inventory.json").write_text(
            '{"system_information": {"system_name": "StrictSys"}}',
            encoding="utf-8",
        )
        with zipfile.ZipFile(ato_pkg / "Policies_and_Procedures" / "Broken_Policy.docx", "w") as zf:
            zf.writestr("not_word.xml", "<empty/>")
        self.assertFalse(
            validate_compliance_artifacts.validate_compliance_package(
                str(ws_pkg), run_linter=False, linter_strict=True
            )
        )
        self.assertFalse(
            validate_compliance_artifacts.validate_compliance_package(
                str(ws_pkg), run_linter=False, linter_strict=False
            )
        )

    def test_pta_honors_policy_format(self) -> None:
        """Validator honors policy_format and all template sections when writing PTA; legacy block removed."""
        ws = self.root / "ws_pta_fmt"
        ato_dir = ws / "ato_artifacts"
        (ato_dir / "SSP").mkdir(parents=True)
        (ato_dir / "POAM").mkdir(parents=True)
        (ws / "system_inventory.json").write_text(
            '{"system_information": {"system_name": "PtaFmtSys", "system_abbreviation": "PFS", '
            '"organization": "Org", "impact_level": "IL5", "compliance_baseline": "DoD IL5"}, '
            '"personnel_roles": {"authorizing_official": {"name": "AO"}, "system_owner": {"name": "SO"}, '
            '"issm": {"name": "ISSM"}, "isso": {"name": "ISSO"}}, "infrastructure_components": {}}',
            encoding="utf-8",
        )
        (ato_dir / "SSP" / "SSP_System_Security_Plan.md").write_text(
            "# SSP\n\n### AC-17 Remote Access\nCloud IAP over TLS 1.3.\n",
            encoding="utf-8",
        )
        (ato_dir / "POAM" / "Plan_of_Action_and_Milestones.yaml").write_text(
            "poam_items: []\n",
            encoding="utf-8",
        )
        with patch("validate_compliance_artifacts.run_bounded_command") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            ok = validate_compliance_artifacts.validate_compliance_package(
                str(ws),
                fix_drift=True,
                policy_format="markdown",
                run_linter=False,
            )
        self.assertTrue(ok)
        self.assertTrue((ato_dir / "Path_to_Authorization.md").exists())
        self.assertFalse((ato_dir / "Path_to_Authorization.docx").exists())

        pta_text = (ato_dir / "Path_to_Authorization.md").read_text(encoding="utf-8")
        self.assertIn('ACAS Vulnerability Scan "Good Data" Verification Rules', pta_text)

        vca_src = Path(validate_compliance_artifacts.__file__).read_text(encoding="utf-8")
        self.assertNotIn("ai_validation_report.json", vca_src)
        self.assertNotIn("VALIDATION_REPORT.md", vca_src)

    def test_code_c_04_05_06_07_and_cat_10_12(self) -> None:
        """Substance check, firewall helper, past-due POA&M, and control ID normalization."""
        # Single word 'baseline' must not pass ATC substance check
        ok, status, _ = semantic_linter.evaluate_control_substance(
            "AC-17", "Implemented per baseline requirements inside the enclave boundary."
        )
        self.assertFalse(ok)
        self.assertIn("Incomplete AC-17", status)

        # Firewall helper ignores DENY rules, avoids substring match ('22' in '2222'), and handles ranges/'all'
        deny_rule = {
            "name": "deny-all",
            "direction": "INGRESS",
            "action": "DENY",
            "source_ranges": ["0.0.0.0/0"],
            "ports": ["22"],
        }
        self.assertEqual(poam_rules.firewall_rule_exposes_ports(deny_rule, {22}), [])

        port_2222_rule = {
            "name": "allow-2222",
            "direction": "INGRESS",
            "action": "ALLOW",
            "source_ranges": ["0.0.0.0/0"],
            "ports": ["2222"],
        }
        self.assertEqual(poam_rules.firewall_rule_exposes_ports(port_2222_rule, {22}), [])

        range_rule = {
            "name": "allow-range",
            "direction": "INGRESS",
            "action": "ALLOW",
            "source_ranges": ["0.0.0.0/0"],
            "ports": ["20-25"],
        }
        self.assertEqual(poam_rules.firewall_rule_exposes_ports(range_rule, {22, 3389}), [22])

        # Past-due scheduled completion date preserved on preserve_past_due or Delayed status
        delayed_item = poam_rules.normalize_poam_item(
            {
                "control": "AC-02",
                "weakness_name": "Overdue item",
                "status": "Delayed",
                "scheduled_completion_date": "2020-01-15",
            },
            sys_abbr="SYS",
            counter=1,
            eff_date="2026-01-01",
        )
        self.assertEqual(delayed_item["sched_date"], "2020-01-15")

        # CAT-12: Control ID normalization
        self.assertEqual(poam_rules.normalize_control_id("AC-02(01)"), "AC-2(1)")
        self.assertEqual(
            poam_rules.extract_normalized_control_ids("AC-02 / IA-05(02)"),
            ["AC-2", "IA-5(2)", "IA-5"],
        )

        # CAT-10: KMS key without rotation_period triggers DRIFT-KMS-ROT when cryptoperiod policy is configured
        inv_no_rot = {
            "system_information": {"system_name": "KmsSys"},
            "compliance_config": {"max_kms_rotation_days": 365},
            "infrastructure_components": {
                "kms_keys": [{"name": "key-no-rot", "rotation_period": ""}],
                "storage_buckets": [{"name": "b1", "cmek_encrypted": True}],
            },
        }
        ssp_rot = self.root / "ssp_rot.md"
        ssp_rot.write_text("Data is protected with Cloud KMS CMEK.\n", encoding="utf-8")
        drift = semantic_linter.evaluate_architectural_drift(
            inv_no_rot, ssp_path=ssp_rot
        )
        self.assertTrue(any(f.finding_id == "DRIFT-KMS-ROT-key-no-rot" for f in drift))

        # CAT-10: Mandatory SC-28 heading with explicit non-CMEK narrative does not trigger DRIFT-KMS-001
        inv_no_cmek = {
            "system_information": {"system_name": "NoCmekSys"},
            "infrastructure_components": {"kms_keys": [], "storage_buckets": []},
        }
        ssp_no_cmek = self.root / "ssp_no_cmek.md"
        ssp_no_cmek.write_text(
            "### SC-28 Protection of Information at Rest\nGoogle-managed default encryption (no CMEK discovered).\n",
            encoding="utf-8",
        )
        drift_clean = semantic_linter.evaluate_architectural_drift(
            inv_no_cmek,
            ssp_path=ssp_no_cmek,
        )
        self.assertFalse(any(f.finding_id == "DRIFT-KMS-001" for f in drift_clean))


if __name__ == "__main__":
    unittest.main()
