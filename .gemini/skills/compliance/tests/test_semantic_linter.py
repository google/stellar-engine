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

"""Unit test suite for semantic_linter.py.

Tests:
1. Public Sector Security Engineer persona & system prompt rules.
2. Rejection of vague boilerplate & untailored placeholders.
3. Substantive control evaluation (AC-17, IA-2, SC-7, SC-28, IR-4, AU-2).
4. Architectural drift detection against Terraform state (CMEK, 0.0.0.0/0 ingress, multi-region, SIEM logging).
5. Semantic artifact validators (SSP, 20 Policy Manuals, POA&M).
6. SemanticLinterReport metrics, properties, and markdown rendering.
7. End-to-end run_semantic_linter orchestration.
"""

import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict
import unittest

SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
SKILL_BASE: str = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SRC_DIR: str = os.path.join(SKILL_BASE, "src")

for _p in (SRC_DIR, SCRIPT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from compliance_engine.file_helpers import _bootstrap_environment, write_json_file, write_text_file
_bootstrap_environment()

from compliance_engine.semantic_linter import (
    SemanticLinterReport,
    ArtifactSemanticResult,
    SemanticFinding,
    _extract_cat_level,
    evaluate_architectural_drift,
    evaluate_control_substance,
    run_semantic_linter,
    validate_poam_semantics,
)


class TestAIValidator(unittest.TestCase):
    """Unit test suite for the Deterministic Semantic Compliance Linter & Drift Engine."""

    def test_public_sector_security_engineer_criteria(self) -> None:
        """Verifies the deterministic linter encodes the strict Trust But Verify criteria."""
        # 1. Reject vague statements
        ok, status, _ = evaluate_control_substance("AC-2", "Access is granted as appropriate using reasonable precautions.", {})
        self.assertFalse(ok)
        self.assertIn("Vague Boilerplate", status)

        # 2. Reject untailored parameters
        ok, status, _ = evaluate_control_substance("AC-2", "Account review occurs every [Assignment: frequency].", {})
        self.assertFalse(ok)
        self.assertIn("Untailored Parameters", status)

        # 3. Reject insufficient length
        ok, status, _ = evaluate_control_substance("AC-2", "Short.", {})
        self.assertFalse(ok)
        self.assertIn("Insufficient Length", status)

        # 4. Accept substantive, concrete implementation statement
        ok, status, _ = evaluate_control_substance(
            "SC-28",
            "Data is encrypted at rest using AES-256-GCM CMEK via Cloud KMS with 90-day automated rotation.",
            {},
        )
        self.assertTrue(ok)

    def test_vague_boilerplate_rejection(self) -> None:
        """Tests that evaluate_control_substance rejects ambiguous, un-prescriptive phrases."""
        inventory: Dict[str, Any] = {"system_information": {"compliance_baseline": "NIST SP 800-53 Rev. 5"}}

        vague_statements = [
            "We implement appropriate security measures across all cloud compute nodes.",
            "Access to the administration portal is granted as needed upon email request.",
            "The engineering team takes reasonable precautions to secure databases.",
            "Passwords must be strong and contain alphanumeric characters.",
            "Security logs are regularly reviewed by the operations team.",
            "Perimeter firewalls are periodically audited by third-party assessors.",
            "We follow industry standards for symmetric key encryption.",
            "Access is granted according to need following supervisor approval.",
            "All software flaws will be resolved in a timely manner.",
            "Dual authorization is implemented where feasible across administrative functions.",
        ]

        for stmt in vague_statements:
            is_substantive, status, detail = evaluate_control_substance("AC-17", stmt, inventory)
            self.assertFalse(
                is_substantive,
                f"Expected statement to be rejected as vague, but passed: '{stmt}'",
            )
            self.assertIn("Vague Boilerplate", status)

    def test_untailored_parameter_rejection(self) -> None:
        """Tests that untailored NIST parameter placeholders are strictly rejected."""
        inventory: Dict[str, Any] = {}

        untailored_samples = [
            ("AC-2", "The system enforces account reviews [Assignment: organization-defined frequency]."),
            ("AC-17", "Remote access uses [Selection: VPN; Cloud IAP; Direct Connect] with TLS encryption."),
            ("SC-28", "All data at rest is encrypted using Cloud KMS with rotation every {{ KMS_ROTATION_DAYS }} days."),
            ("AU-2", "Audit events are retained for [CONFIG_REQUIRED: Log Retention Duration] in Cloud Storage."),
        ]

        for ctrl_id, text in untailored_samples:
            is_substantive, status, detail = evaluate_control_substance(ctrl_id, text, inventory)
            self.assertFalse(is_substantive, f"Expected '{text}' to be rejected for untailored parameters")
            self.assertIn("Untailored Parameters", status)

    def test_substantive_control_evaluations(self) -> None:
        """Tests substantive validation across specific NIST SP 800-53 controls."""
        inventory: Dict[str, Any] = {}

        # 1. AC-17 Remote Access
        substantive_ac17 = (
            "Remote access is mediated exclusively via Google Cloud Identity-Aware Proxy (IAP) "
            "zero-trust encrypted tunnels over TLS 1.3 with FIPS 140-3 validated cryptographic cipher suites. "
            "Direct SSH/RDP ingress from 0.0.0.0/0 is blocked by default-deny perimeter firewall rules. "
            "Sessions terminate automatically after 15 minutes of inactivity."
        )
        is_sub, status, _ = evaluate_control_substance("AC-17", substantive_ac17, inventory)
        self.assertTrue(is_sub, f"Substantive AC-17 rejected: {status}")

        incomplete_ac17 = "Users can connect to virtual machines using standard administrative login accounts."
        is_sub, status, _ = evaluate_control_substance("AC-17", incomplete_ac17, inventory)
        self.assertFalse(is_sub)
        self.assertIn("Incomplete AC-17 Specification", status)

        # 2. IA-2 Multi-Factor Authentication
        substantive_ia2 = (
            "All administrative access requires mandatory hardware token multi-factor authentication (MFA) "
            "via FIDO2 / WebAuthn security keys or DoD Common Access Cards (CAC) / PIV tokens. "
            "Single-factor password login and local administrative account bypass are strictly prohibited."
        )
        is_sub, status, _ = evaluate_control_substance("IA-2", substantive_ia2, inventory)
        self.assertTrue(is_sub, f"Substantive IA-2 rejected: {status}")

        incomplete_ia2 = "Administrative users authenticate using single-factor username and password credentials."
        is_sub, status, _ = evaluate_control_substance("IA-2", incomplete_ia2, inventory)
        self.assertFalse(is_sub)
        self.assertIn("Incomplete IA-2 Specification", status)

        # 3. SC-28 Cryptographic Protection at Rest
        substantive_sc28 = (
            "All persistent storage buckets, disks, and databases are encrypted at rest using "
            "Customer-Managed Encryption Keys (CMEK) via Google Cloud KMS with automated key rotation "
            "every 90 days (7776000s) and FIPS 140-3 validated HSM protection."
        )
        is_sub, status, _ = evaluate_control_substance("SC-28", substantive_sc28, inventory)
        self.assertTrue(is_sub, f"Substantive SC-28 rejected: {status}")

        incomplete_sc28 = "Data is encrypted using default Google-managed keys without customer key management."
        is_sub, status, _ = evaluate_control_substance("SC-28", incomplete_sc28, inventory)
        self.assertFalse(is_sub)
        self.assertIn("Incomplete SC-28 Specification", status)

    def test_architectural_drift_detection(self) -> None:
        """Tests cross-referencing documentation claims against live Terraform state."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ssp_path = Path(tmp_dir) / "SSP.md"

            # Scenario 1: Claims CMEK, but Terraform has zero KMS keys -> CAT I Drift
            ssp_content = "All workload data is protected by Customer-Managed Encryption Keys (CMEK) under SC-28."
            write_text_file(str(ssp_path), ssp_content)

            inv_no_kms: Dict[str, Any] = {
                "infrastructure_components": {"kms_keys": [], "storage_buckets": []},
                "network_architecture": {"firewall_rules": []},
            }
            findings = evaluate_architectural_drift(inv_no_kms, ssp_path=ssp_path)
            drift_ids = [f.finding_id for f in findings]
            self.assertIn("DRIFT-KMS-001", drift_ids)
            self.assertTrue(any("CAT I" in f.severity for f in findings if f.finding_id == "DRIFT-KMS-001"))

            # Scenario 2: KMS Key rotation period exceeds configured threshold -> CAT II Drift
            inv_slow_rot: Dict[str, Any] = {
                "compliance_config": {"max_kms_rotation_days": 365},
                "infrastructure_components": {
                    "kms_keys": [{"name": "storage-key", "rotation_period": "63072000s"}],  # 2 years
                    "storage_buckets": [],
                },
                "network_architecture": {"firewall_rules": []},
            }
            findings = evaluate_architectural_drift(inv_slow_rot, ssp_path=ssp_path)
            drift_ids = [f.finding_id for f in findings]
            self.assertIn("DRIFT-KMS-ROT-storage-key", drift_ids)

            # Scenario 3: Claims zero-trust, but firewall permits 0.0.0.0/0 SSH/RDP -> CAT I Drift
            ssp_iap = "Remote access is mediated exclusively via Cloud Identity-Aware Proxy (IAP) zero-trust tunnels."
            write_text_file(str(ssp_path), ssp_iap)
            inv_open_fw: Dict[str, Any] = {
                "infrastructure_components": {"kms_keys": [], "storage_buckets": []},
                "network_architecture": {
                    "firewall_rules": [
                        {"name": "allow-public-ssh", "source_ranges": ["0.0.0.0/0"], "ports": ["22"]},
                    ]
                },
            }
            findings = evaluate_architectural_drift(inv_open_fw, ssp_path=ssp_path)
            drift_ids = [f.finding_id for f in findings]
            self.assertIn("DRIFT-FW-INGRESS-allow-public-ssh", drift_ids)
            cat1_fw = [f for f in findings if f.finding_id == "DRIFT-FW-INGRESS-allow-public-ssh"]
            self.assertIn("CAT I", cat1_fw[0].severity)

            # Scenario 4: Claims dual-region failover, but subnets only in 1 region -> CAT II Drift
            ssp_dual = "The architecture provides high availability with dual-region active-passive failover under CP-2."
            write_text_file(str(ssp_path), ssp_dual)
            inv_single_reg: Dict[str, Any] = {
                "system_information": {"primary_location": "us-east4"},
                "infrastructure_components": {"kms_keys": [], "storage_buckets": []},
                "network_architecture": {
                    "firewall_rules": [],
                    "subnets": [{"name": "sub-1", "region": "us-east4"}, {"name": "sub-2", "region": "us-east4"}],
                },
            }
            findings = evaluate_architectural_drift(inv_single_reg, ssp_path=ssp_path)
            drift_ids = [f.finding_id for f in findings]
            self.assertIn("DRIFT-REGION-001", drift_ids)

            # Scenario 5: Claims external SIEM streaming, but zero logging sinks -> CAT II Drift
            ssp_siem = "All audit trails stream to external CSOC SIEM endpoints in real time under AU-6."
            write_text_file(str(ssp_path), ssp_siem)
            inv_no_sinks: Dict[str, Any] = {
                "infrastructure_components": {"kms_keys": [], "storage_buckets": [], "logging_sinks": []},
                "network_architecture": {"firewall_rules": []},
            }
            findings = evaluate_architectural_drift(inv_no_sinks, ssp_path=ssp_path)
            drift_ids = [f.finding_id for f in findings]
            self.assertIn("DRIFT-LOG-001", drift_ids)

            # Scenario 6: Clean state matching claims -> 0 drift findings
            ssp_clean = "System implements standard role-based access control."
            write_text_file(str(ssp_path), ssp_clean)
            inv_clean: Dict[str, Any] = {
                "infrastructure_components": {"kms_keys": [], "storage_buckets": []},
                "network_architecture": {"firewall_rules": []},
            }
            findings = evaluate_architectural_drift(inv_clean, ssp_path=ssp_path)
            self.assertEqual(len(findings), 0)

    def test_semantic_linter_report_properties_and_metrics(self) -> None:
        """Tests SemanticLinterReport scoring, properties, serialization, and markdown rendering."""
        report = SemanticLinterReport("/workspace/test-env", "NIST SP 800-53 Rev. 5")
        self.assertEqual(report.cat_1_count, 0)
        self.assertEqual(report.overall_status, "PASS")

        # Record clean artifact
        art1 = ArtifactSemanticResult("SSP.md")
        art1.status = "PASS"
        report.record_artifact_result(art1)
        self.assertIn("PASS", report.overall_status)
        self.assertEqual(report.summary["passed_count"], 1)
        self.assertEqual(report.summary["compliance_score_percent"], 100.0)

        # Record artifact with CAT I finding
        art2 = ArtifactSemanticResult("Policies/AC_Policy.md")
        art2.status = "REJECTED"
        art2.add_finding(
            SemanticFinding(
                finding_id="LINT-TEST-CAT1",
                severity="CAT I (Critical)",
                category="Missing Deliverable",
                artifact="AC_Policy.md",
                description="Test CAT I blocker finding.",
                remediation="Fix blocker.",
            )
        )
        report.record_artifact_result(art2)
        self.assertEqual(report.cat_1_count, 1)
        self.assertFalse(report.passed)
        self.assertIn("REJECTED", report.overall_status)
        self.assertEqual(report.summary["cat_1_findings_count"], 1)
        self.assertEqual(report.summary["passed_count"], 1)
        self.assertEqual(report.summary["total_artifacts_evaluated"], 2)
        self.assertEqual(report.summary["compliance_score_percent"], 50.0)

        # Verify all_findings aggregates findings
        self.assertEqual(len(report.all_findings), 1)
        self.assertEqual(report.all_findings[0].finding_id, "LINT-TEST-CAT1")

        # Verify serialization
        as_dict = report.to_dict()
        self.assertEqual(as_dict["cat_1_count"], 1)
        self.assertEqual(as_dict["summary"]["verdict"], report.overall_status)

        # Verify Markdown rendering
        md_text = report.to_markdown()
        self.assertIn("Lead Assessor Semantic Linter & Architectural Drift Audit", md_text)
        self.assertIn("TRUST BUT VERIFY", md_text)
        self.assertIn("LINT-TEST-CAT1", md_text)

    def test_validate_poam_semantics(self) -> None:
        """Tests semantic validation of Plan of Action and Milestones (POA&M)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            poam_file = Path(tmp_dir) / "POAM.yaml"

            # 1. Missing file
            missing_res = validate_poam_semantics(Path(tmp_dir) / "nonexistent.yaml", {}, "NIST SP 800-53")
            self.assertEqual(missing_res.status, "REJECTED")
            self.assertEqual(len(missing_res.findings), 1)
            self.assertIn("CAT I", missing_res.findings[0].severity)

            # 2. File with truncated mitigation and missing date
            poam_data = {
                "poam_items": [
                    {
                        "poam_id": "POA-001",
                        "weakness_name": "Test Weakness",
                        "planned_mitigation": "Will fix.",  # < 15 chars
                        "scheduled_completion_date": "YYYY-MM-DD",
                    }
                ]
            }
            write_text_file(str(poam_file), json.dumps(poam_data))
            res = validate_poam_semantics(poam_file, {}, "NIST SP 800-53")
            f_ids = [f.finding_id for f in res.findings]
            self.assertIn("LINT-POAM-MIT-POA-001", f_ids)
            self.assertIn("LINT-POAM-DATE-POA-001", f_ids)

    def test_cat_severity_discrimination(self) -> None:
        """Word-boundary extraction prevents CAT II and CAT III from matching CAT I."""
        self.assertEqual(_extract_cat_level("CAT I (Critical)"), 1)
        self.assertEqual(_extract_cat_level("CAT II (Medium)"), 2)
        self.assertEqual(_extract_cat_level("CAT III (Low)"), 3)
        self.assertEqual(_extract_cat_level("Critical Blocker"), 1)
        self.assertEqual(_extract_cat_level("Moderate Risk"), 2)
        self.assertEqual(_extract_cat_level("Advisory Item"), 3)

        # Ensure report does not misclassify CAT II as CAT I
        report = SemanticLinterReport("/test", "NIST SP 800-53")
        art = ArtifactSemanticResult("test.md")
        art.add_finding(
            SemanticFinding(
                finding_id="F-01",
                severity="CAT II (Medium)",
                category="Policy Weakness",
                artifact="test.md",
                description="Medium finding",
                remediation="Fix it",
            )
        )
        report.record_artifact_result(art)
        self.assertEqual(report.cat_1_count, 0)
        self.assertEqual(report.cat_2_count, 1)
        self.assertEqual(report.cat_3_count, 0)
        self.assertEqual(art.status, "ACTION_REQUIRED")
        self.assertTrue(report.passed)

    def test_poam_item_id_and_milestones(self) -> None:
        """POA&M items with item_id and milestone descriptions are recognized without false positives."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            poam_file = Path(tmp_dir) / "POAM.yaml"
            poam_data = {
                "poam_items": [
                    {
                        "item_id": "POAM-C2T-001",
                        "control_identifier": "SC-28",
                        "weakness_name": "KMS protection test",
                        "severity_risk_level": "Moderate",
                        "scheduled_completion_date": "2026-12-31",
                        "milestones": [
                            {
                                "step": 1,
                                "description": "Remediate KMS crypto key deletion protection in Terraform.",
                                "target_date": "2026-12-31",
                                "status": "Open",
                            }
                        ],
                    }
                ]
            }
            write_text_file(str(poam_file), json.dumps(poam_data))
            res = validate_poam_semantics(poam_file, {}, "NIST SP 800-53")
            # Should have no missing mitigation or date findings
            self.assertEqual(len(res.findings), 0)
            self.assertEqual(res.status, "PASS")

    def test_end_to_end_ai_validation_orchestrator(self) -> None:
        """Tests run_semantic_linter on a simulated target folder."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir)
            ato_path = target_path / "ato_artifacts"
            ssp_dir = ato_path / "SSP"
            pol_dir = ato_path / "Policies_and_Procedures"
            poam_dir = ato_path / "POAM"

            ssp_dir.mkdir(parents=True)
            pol_dir.mkdir(parents=True)
            poam_dir.mkdir(parents=True)

            # Create sample files
            write_text_file(
                str(ssp_dir / "SSP_System_Security_Plan.md"),
                "# System Security Plan\n\n### AC-17 Remote Access\nCloud IAP zero-trust tunnels with TLS 1.3.",
            )
            write_text_file(
                str(pol_dir / "Access_Control_Policy_and_Procedures.md"),
                (
                    "# Access Control Policy\n\n## Purpose\nMandate.\n\n## Scope\nBoundary.\n\n"
                    "## Roles and Responsibilities\nISSM.\n\n## Compliance and Enforcement\nRules."
                ),
            )
            write_text_file(
                str(poam_dir / "Plan_of_Action_and_Milestones.yaml"),
                (
                    "poam_items:\n  - poam_id: POAM-001\n    weakness_name: Flaw\n"
                    "    planned_mitigation: Deploy Cloud Armor WAF\n    scheduled_completion_date: '2026-10-01'"
                ),
            )
            inv: Dict[str, Any] = {
                "system_information": {"system_name": "TestFoundation"},
                "infrastructure_components": {"kms_keys": [], "storage_buckets": []},
                "network_architecture": {"firewall_rules": []},
            }
            write_json_file(str(target_path / "system_inventory.json"), inv)

            report = run_semantic_linter(target_path, inventory=inv)
            self.assertIsInstance(report, SemanticLinterReport)
            self.assertTrue(report.passed)

            # Verify semantic_linter_report.json exists
            linter_json = ato_path / "semantic_linter_report.json"
            self.assertTrue(linter_json.exists())
            with open(linter_json, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertIn("summary", saved)
            self.assertEqual(saved["summary"]["cat_1_findings_count"], 0)

    def test_rotation_not_mandated_by_default(self) -> None:
        """FedRAMP High inventory with SOFTWARE keys and 365-day rotation produces no linter/POA&M finding by default."""
        from compliance_engine import poam_rules
        with tempfile.TemporaryDirectory() as tmp_dir:
            ssp_path = Path(tmp_dir) / "SSP.md"
            write_text_file(str(ssp_path), "All data at rest uses Customer-Managed Encryption Keys (CMEK) under SC-28.")
            inv: Dict[str, Any] = {
                "system_information": {
                    "system_name": "FedRampSys",
                    "impact_level": "FedRAMP High",
                    "compliance_baseline": "FedRAMP High",
                },
                "infrastructure_components": {
                    "kms_keys": [
                        {"name": "sw-key-365", "protection_level": "SOFTWARE", "rotation_period": "31536000s"},
                    ],
                    "storage_buckets": [],
                },
                "network_architecture": {"firewall_rules": []},
            }
            drift = evaluate_architectural_drift(inv, ssp_path=ssp_path)
            self.assertEqual([f.finding_id for f in drift], [])
            poam = poam_rules.derive_poam_findings(inv, target_dir=None)
            self.assertEqual(poam, [])

            # When policy flag max_kms_rotation_days=90 is configured, 365-day key produces a finding with SP 800-57 wording
            inv_policy = json.loads(json.dumps(inv))
            inv_policy["compliance_config"] = {"max_kms_rotation_days": 90}
            drift_pol = evaluate_architectural_drift(inv_policy, ssp_path=ssp_path)
            self.assertTrue(any(f.finding_id == "DRIFT-KMS-ROT-sw-key-365" for f in drift_pol))
            self.assertTrue(any("800-57" in f.description for f in drift_pol))
            self.assertFalse(any("mandated for DoD IL5 / FedRAMP High" in f.description for f in drift_pol))

    def test_hsm_upgrade_rule_opt_in(self) -> None:
        """HSM-upgrade POA&M rule for SOFTWARE keys is opt-in via organizational policy flag."""
        from compliance_engine import poam_rules
        inv: Dict[str, Any] = {
            "system_information": {
                "system_name": "Il5Sys",
                "impact_level": "IL5",
                "compliance_baseline": "DoD IL5",
            },
            "infrastructure_components": {
                "kms_keys": [{"name": "sw-key", "protection_level": "SOFTWARE", "rotation_period": "7776000s"}],
            },
        }
        self.assertEqual(poam_rules.derive_poam_findings(inv, target_dir=None), [])
        inv_opt_in = json.loads(json.dumps(inv))
        inv_opt_in["compliance_config"] = {"require_cloud_hsm_keys": True}
        items = poam_rules.derive_poam_findings(inv_opt_in, target_dir=None)
        self.assertEqual(len(items), 1)
        self.assertIn("recommend", items[0]["desc"].lower())

    def test_report_paths_relative(self) -> None:
        """semantic_linter_report.json serializes target_dir as '.' and artifact paths relative to target."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir).resolve()
            ato_path = target_path / "ato_artifacts"
            (ato_path / "SSP").mkdir(parents=True)
            (ato_path / "POAM").mkdir(parents=True)
            write_text_file(
                str(ato_path / "SSP" / "SSP_System_Security_Plan.md"),
                "# SSP\n\n### AC-17 Remote Access\nCloud IAP tunnels over TLS 1.3.\n",
            )
            write_text_file(
                str(ato_path / "POAM" / "Plan_of_Action_and_Milestones.yaml"),
                "poam_items: []\n",
            )
            run_semantic_linter(target_path, inventory={"system_information": {"system_name": "RelSys"}})
            report_text = (ato_path / "semantic_linter_report.json").read_text(encoding="utf-8")
            self.assertNotIn(str(Path.home()), report_text)
            self.assertNotIn(str(target_path), report_text)
            saved = json.loads(report_text)
            self.assertEqual(saved["target_dir"], ".")
            for k, v in saved["artifact_results"].items():
                self.assertFalse(os.path.isabs(k), k)
                self.assertFalse(os.path.isabs(v["artifact_path"]), v["artifact_path"])


if __name__ == "__main__":
    unittest.main()
