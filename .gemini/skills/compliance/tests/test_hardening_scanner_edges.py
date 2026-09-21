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

"""Automated edge-case and negative tests for scanner bridges and POA&M normalization.

Covers failure conditions, timeouts, and boundary mocking in ``security_scanner_bridge.py``
and ``poam_rules.py``:
- Subprocess timeout handling: TimeoutExpired mapped to CA-02 / RA-05 assessment gaps.
- Malformed / corrupted scanner output: JSONDecodeError handled cleanly.
- Non-zero subprocess exit codes: stderr scrubbed, flattened, and surfaced as structured findings.
- SARIF ingestion edge cases: empty files, malformed JSON, missing runs/results, path boundaries.
- POA&M normalization: date fallbacks, non-dict inputs, status and severity mappings,
  and unparsed Terraform file gap generation.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Dict
import unittest
from unittest.mock import MagicMock, patch

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import poam_rules
import security_scanner_bridge as ssb


class TestScannerSubprocessNegativeEdges(unittest.TestCase):
    """Negative testing for scanner timeouts, corrupted stdout, and execution errors."""

    def setUp(self) -> None:
        ssb.reset_scan_cache()
        self._tmp = tempfile.TemporaryDirectory()
        self.target = self._tmp.name
        Path(self.target, "main.tf").write_text('resource "google_storage_bucket" "b" {}', encoding="utf-8")

    def tearDown(self) -> None:
        ssb.reset_scan_cache()
        self._tmp.cleanup()

    @patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/checkov")
    @patch("security_scanner_bridge._safe_run_subprocess")
    def test_checkov_timeout_mapped_to_assessment_gap(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Checkov timeout must not crash and must produce a CA-02 / RA-05 finding."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["checkov"], timeout=120)
        findings = ssb.run_checkov_scan(self.target, timeout_seconds=120)

        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding["check_id"], "CKV_SCANNER_TIMEOUT")
        self.assertEqual(finding["cwe"], "CA-02 / RA-05")
        self.assertEqual(finding["severity"], "High")
        self.assertTrue(ssb.is_scanner_failure_check_id(finding["check_id"]))

    @patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/semgrep")
    @patch("security_scanner_bridge._safe_run_subprocess")
    def test_semgrep_timeout_mapped_to_assessment_gap(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Semgrep timeout must produce a SEMGREP_SCANNER_TIMEOUT finding."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["semgrep"], timeout=90)
        findings = ssb.run_semgrep_scan(self.target, timeout_seconds=90)

        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding["check_id"], "SEMGREP_SCANNER_TIMEOUT")
        self.assertEqual(finding["cwe"], "CA-02 / RA-05")
        self.assertTrue(ssb.is_scanner_failure_check_id(finding["check_id"]))

    @patch("security_scanner_bridge.resolve_preinstalled_scanner_binary", return_value="/usr/bin/trivy")
    @patch("security_scanner_bridge._safe_run_subprocess")
    def test_trivy_timeout_mapped_to_assessment_gap(self, mock_run: MagicMock, mock_res: MagicMock) -> None:
        """Trivy timeout must produce a TRIVY_SCANNER_TIMEOUT finding."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["trivy"], timeout=60)
        findings = ssb.run_trivy_scan(self.target, timeout_seconds=60)

        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding["check_id"], "TRIVY_SCANNER_TIMEOUT")
        self.assertEqual(finding["cwe"], "CA-02 / RA-05")

    @patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/checkov")
    @patch("security_scanner_bridge._safe_run_subprocess")
    def test_checkov_corrupted_json_output_handled_gracefully(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Malformed JSON stdout from Checkov is caught and mapped to a scanner error finding."""
        mock_run.return_value = MagicMock(returncode=0, stdout="<HTML>502 Bad Gateway</HTML>", stderr="")
        findings = ssb.run_checkov_scan(self.target)

        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding["check_id"], "CKV_SCANNER_ERROR")
        self.assertIn("could not be parsed as JSON", finding["message"])
        self.assertEqual(finding["cwe"], "CA-02 / RA-05")

    @patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/checkov")
    @patch("security_scanner_bridge._safe_run_subprocess")
    def test_checkov_nonzero_exit_surfaces_diagnostic(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Non-zero exit (e.g. code 2) captures flattened diagnostic in message."""
        mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="Fatal: syntax error in config\n  at line 4")
        findings = ssb.run_checkov_scan(self.target)

        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding["check_id"], "CKV_SCANNER_ERROR")
        self.assertNotIn("\n", finding["message"])
        self.assertIn("syntax error", finding["message"])


class TestSarifIngestionEdges(unittest.TestCase):
    """Negative and boundary tests for SARIF report file parsing."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_empty_sarif_file_returns_empty_list(self) -> None:
        sarif_file = self.root / "empty.sarif"
        sarif_file.write_text("", encoding="utf-8")
        findings = ssb.parse_sarif_file(str(sarif_file), allowed_boundary=self.root)
        self.assertEqual(findings, [])

    def test_invalid_json_sarif_file_returns_empty_list(self) -> None:
        sarif_file = self.root / "corrupted.sarif"
        sarif_file.write_text("NOT_JSON_DATA", encoding="utf-8")
        findings = ssb.parse_sarif_file(str(sarif_file), allowed_boundary=self.root)
        self.assertEqual(findings, [])

    def test_sarif_missing_runs_returns_empty_list(self) -> None:
        sarif_file = self.root / "no_runs.sarif"
        sarif_file.write_text(json.dumps({"version": "2.1.0"}), encoding="utf-8")
        findings = ssb.parse_sarif_file(str(sarif_file), allowed_boundary=self.root)
        self.assertEqual(findings, [])

    def test_sarif_run_without_results_returns_empty_list(self) -> None:
        sarif_file = self.root / "no_results.sarif"
        sarif_file.write_text(json.dumps({"runs": [{"tool": {"driver": {"name": "TestTool"}}}]}), encoding="utf-8")
        findings = ssb.parse_sarif_file(str(sarif_file), allowed_boundary=self.root)
        self.assertEqual(findings, [])

    def test_sarif_results_with_missing_and_sparse_fields(self) -> None:
        """SARIF entries missing ruleId, message, or locations are safely normalized with defaults."""
        sparse_sarif = {
            "runs": [
                {
                    "tool": {"driver": {"name": "SparseAnalyzer"}},
                    "results": [
                        {
                            "level": "error",
                            # ruleId omitted
                            # message omitted
                            # locations omitted
                        },
                        {
                            "ruleId": "CUSTOM_001",
                            "level": "warning",
                            "message": {"text": "Specific alert"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "src/app.py"},
                                        "region": {"startLine": 42},
                                    }
                                }
                            ],
                        },
                    ],
                }
            ]
        }
        sarif_file = self.root / "sparse.sarif"
        sarif_file.write_text(json.dumps(sparse_sarif), encoding="utf-8")
        findings = ssb.parse_sarif_file(str(sarif_file), allowed_boundary=self.root)

        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["check_id"], "RULE_UNKNOWN")
        self.assertEqual(findings[0]["severity"], "High")
        self.assertEqual(findings[0]["location"], "codebase")

        self.assertEqual(findings[1]["check_id"], "CUSTOM_001")
        self.assertEqual(findings[1]["severity"], "Moderate")
        self.assertEqual(findings[1]["location"], "src/app.py:42")

    def test_sarif_path_outside_allowed_boundary_is_rejected(self) -> None:
        outside_file = self.root / ".." / "escaped.sarif"
        findings = ssb.parse_sarif_file(str(outside_file), allowed_boundary=self.root)
        self.assertEqual(findings, [])


class TestPoamRulesAndNormalizationEdges(unittest.TestCase):
    """Testing POA&M item normalization, date fallbacks, and gap handling."""

    def test_normalize_poam_item_non_dict_returns_none(self) -> None:
        for non_dict in (None, "string", 123, []):
            self.assertIsNone(poam_rules.normalize_poam_item(non_dict))

    def test_normalize_poam_item_unparseable_date_falls_back_to_90_days(self) -> None:
        raw = {
            "title": "Invalid Date Finding",
            "status": "Ongoing",
            "sched_date": "not-a-valid-date",
        }
        item = poam_rules.normalize_poam_item(raw, sys_abbr="TST", counter=1, eff_date="2026-09-11")
        self.assertIsNotNone(item)
        self.assertRegex(item["sched_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(item["sched_date"] > "2026-09-11")

    def test_normalize_poam_item_past_date_is_bumped_for_ongoing_items(self) -> None:
        raw = {
            "title": "Stale Ongoing Finding",
            "status": "Ongoing",
            "sched_date": "2020-01-01",
        }
        item = poam_rules.normalize_poam_item(raw, sys_abbr="TST", counter=1, eff_date="2026-09-11")
        self.assertIsNotNone(item)
        self.assertTrue(item["sched_date"] > "2026-09-11")

    def test_normalize_poam_item_severity_mapping_permutations(self) -> None:
        test_cases = [
            ("CRITICAL", "Very High"),
            ("VERY HIGH", "Very High"),
            ("HIGH", "High"),
            ("MEDIUM", "Moderate"),
            ("MODERATE", "Moderate"),
            ("LOW", "Low"),
            ("VERY LOW", "Very Low"),
            ("NONE", "None"),
            ("UNKNOWN_CUSTOM", "Unknown_Custom"),
        ]
        for raw_sev, expected in test_cases:
            item = poam_rules.normalize_poam_item({"severity": raw_sev})
            self.assertEqual(item["severity"], expected)

    def test_unparsed_terraform_file_generates_coverage_gap_finding(self) -> None:
        """Unparsed Terraform files must generate CA-02 / RA-05 POA&M items rather than silently dropping boundary elements."""
        inventory: Dict[str, Any] = {
            "infrastructure_components": {
                "unparsed_terraform_files": [
                    {
                        "path": "modules/net-vpc/firewall.tf",
                        "error": "Syntax error on line 42",
                    }
                ]
            }
        }
        items = poam_rules.derive_poam_findings(
            inventory=inventory,
            eff_date="2026-09-11",
            run_scanners=False,
        )

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertIn("modules/net-vpc/firewall.tf", item["title"])
        self.assertEqual(item["aps"], "CA-02 / RA-05")
        self.assertEqual(item["source"], "IaC Discovery Engine")
        self.assertEqual(item["severity"], "Moderate")

    def test_clean_inventory_evaluates_to_zero_items_without_fake_filler(self) -> None:
        """Clean architecture with no findings or concerns must return an empty list without synthetic filler."""
        inventory: Dict[str, Any] = {
            "system_information": {"system_name": "Clean Platform"},
            "infrastructure_components": {
                "kms_keys": [{"name": "k1", "rotation_period": "7776000s", "protection_level": "HSM"}],
                "storage_buckets": [{"name": "b1", "versioning": True, "cmek_encrypted": True, "uniform_bucket_level_access": True}],
            },
        }
        items = poam_rules.derive_poam_findings(
            inventory=inventory,
            eff_date="2026-09-11",
            run_scanners=False,
        )
        self.assertEqual(items, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
