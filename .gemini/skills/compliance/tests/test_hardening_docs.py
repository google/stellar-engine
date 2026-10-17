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

"""Regression tests for DOCX and Template Engine hardening."""

import os
import sys
import unittest
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from template_engine import evaluate_template_conditionals
from docx_generator import DocxRelationshipManager, trim_trailing_punctuation, convert_markdown_to_docx
from audit_log import configure_audit_log, reset_audit_log


class TestHardeningDocs(unittest.TestCase):

    def test_evaluate_template_conditionals_single_pass(self):
        """Verify nested conditionals are evaluated correctly without ReDoS tricks."""
        template = """
<!-- IF A -->
line1
<!-- IF B -->
line2
<!-- ENDIF B -->
line3
<!-- ENDIF A -->
"""
        # A True, B True
        res1 = evaluate_template_conditionals(template, {"A": True, "B": True})
        self.assertIn("line1", res1)
        self.assertIn("line2", res1)
        self.assertIn("line3", res1)

        # A True, B False
        res2 = evaluate_template_conditionals(template, {"A": True, "B": False})
        self.assertIn("line1", res2)
        self.assertNotIn("line2", res2)
        self.assertIn("line3", res2)

        # A False, B True (should omit all)
        res3 = evaluate_template_conditionals(template, {"A": False, "B": True})
        self.assertNotIn("line1", res3)
        self.assertNotIn("line2", res3)
        self.assertNotIn("line3", res3)

    def test_docx_hyperlink_evasion(self):
        """Verify whitespace/control chars cannot bypass URL scheme checks."""
        mgr = DocxRelationshipManager()

        # Bypass via embedded space
        res1 = mgr.add_hyperlink("java script:alert(1)")
        self.assertEqual(res1, "")

        # Bypass via control char
        res2 = mgr.add_hyperlink("java\nscript:alert(1)")
        self.assertEqual(res2, "")

        # Bypass via relative path trick
        res3 = mgr.add_hyperlink("java script:alert(1)#.html")
        self.assertEqual(res3, "")

        # Valid link works
        res4 = mgr.add_hyperlink("https://example.com")
        self.assertNotEqual(res4, "")

    def test_trim_trailing_punctuation_performance(self):
        """Verify O(n^2) fix in trim_trailing_punctuation."""
        url = "http://example.com" + ")" * 1000
        clean, trailing = trim_trailing_punctuation(url)
        self.assertEqual(clean, "http://example.com")
        self.assertEqual(trailing, ")" * 1000)

    def test_docx_audit_logging(self):
        """Verify that zip creation emits an audit log event."""
        with tempfile.TemporaryDirectory() as td:
            log_path = os.path.join(td, "audit.jsonl")
            configure_audit_log(sink_path=log_path, component="test")
            # The sink is process-wide; drop it before `td` is removed, or later
            # events in this interpreter would recreate the deleted directory.
            self.addCleanup(reset_audit_log)

            out_path = os.path.join(td, "out.docx")
            convert_markdown_to_docx("# Test", out_path)

            with open(log_path, "r") as f:
                logs = f.read()
            self.assertIn("artifact.generated", logs)
            self.assertIn("out.docx", logs)
            self.assertIn("docx", logs)

    def test_supported_regimes_match_engine(self):
        """Skill documentation matches file_helpers.SUPPORTED_REGIMES."""
        from compliance_engine.file_helpers import SUPPORTED_REGIMES

        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        expected_supported = {r.value for r in SUPPORTED_REGIMES}
        self.assertEqual(
            expected_supported,
            {
                "FedRAMP Low",
                "FedRAMP Moderate",
                "FedRAMP High",
                "FISMA Low",
                "FISMA Moderate",
                "FISMA High",
                "DoD IL2",
                "DoD IL4",
                "DoD IL5",
                "DoD IL6",
                "CJIS",
            },
        )
        for doc_path in (
            os.path.join(skill_root, "SKILL.md"),
            os.path.join(skill_root, "README.md"),
            os.path.join(skill_root, "validate_skill.md"),
        ):
            with open(doc_path, encoding="utf-8") as fh:
                content = fh.read()
            for r_name in (
                "FedRAMP Low",
                "FedRAMP Moderate",
                "FedRAMP High",
                "DoD IL2",
                "DoD IL4",
                "DoD IL5",
                "DoD IL6",
                "CJIS",
            ):
                self.assertIn(r_name, content, f"{doc_path} missing supported regime {r_name}")
            # Must document that GovRAMP fails closed
            self.assertIn("GovRAMP", content, f"{doc_path} missing GovRAMP fail-closed documentation")
            self.assertIn("fail closed", content, f"{doc_path} missing fail-closed statement")

    def test_no_unsupported_oscal_outputs(self):
        """OSCAL XML, SAP, SAR, and oscal_poam are not promised in docs or config example."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        config_example_path = os.path.join(skill_root, "config", "compliance_config.yaml.example")
        poam_skill_path = os.path.join(skill_root, "subskills", "poam_skill.md")

        with open(config_example_path, encoding="utf-8") as fh:
            config_content = fh.read()
        with open(poam_skill_path, encoding="utf-8") as fh:
            poam_content = fh.read()

        self.assertNotIn("oscal_poam", config_content)
        self.assertNotIn("oscal_poam", poam_content)
        self.assertNotIn("Generates .json, .xml, and .yaml for SSP, SAP, SAR, and POA&M", config_content)
        self.assertNotIn("SAP, SAR, and POA&M", config_content)
        self.assertNotIn(".xml", config_content.split("oscal_formats:")[1].split("=")[0])
        self.assertNotIn("NIST OSCAL formats", poam_content)

    def test_oscal_version_key_location(self):
        """oscal_version in compliance_config.yaml.example is under export_preferences, not document_versions."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        config_example_path = os.path.join(skill_root, "config", "compliance_config.yaml.example")

        with open(config_example_path, encoding="utf-8") as fh:
            content = fh.read()

        import yaml
        parsed = yaml.safe_load(content)

        doc_versions = parsed.get("document_versions", {})
        self.assertNotIn(
            "oscal_version",
            doc_versions,
            "document_versions.oscal_version is never read by runtime; remove from example.",
        )

        export_prefs = parsed.get("export_preferences", {})
        self.assertIn(
            "oscal_version",
            export_prefs,
            "export_preferences.oscal_version should be documented in example configuration.",
        )

    def test_semgrep_config_docs(self):
        """semgrep_config accepts local in-boundary paths and p/ r/ refs only; no https:// claim or absolute path."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        skill_md_path = os.path.join(skill_root, "SKILL.md")
        config_example_path = os.path.join(skill_root, "config", "compliance_config.yaml.example")

        with open(skill_md_path, encoding="utf-8") as fh:
            skill_content = fh.read()
        with open(config_example_path, encoding="utf-8") as fh:
            config_content = fh.read()

        self.assertNotIn(
            "an https:// URL",
            skill_content,
            "SKILL.md must not claim semgrep_config accepts https:// URLs (code refuses all URL schemes).",
        )
        self.assertNotIn(
            "/opt/security/semgrep-rules",
            config_content,
            "compliance_config.yaml.example must not use /opt/security/semgrep-rules (fails closed).",
        )
        self.assertIn("--semgrep-config", skill_content)
        self.assertIn("COMPLIANCE_SEMGREP_CONFIG", skill_content)

    def test_validate_flags_parity(self):
        """validate_skill.md documents actual CLI flags and omits nonexistent --no-example-labels."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        validate_doc_path = os.path.join(skill_root, "validate_skill.md")

        with open(validate_doc_path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertNotIn("--no-example-labels", content)
        for flag in (
            "--fix",
            "--fill-example-data",
            "--no-fill-example-data",
            "--policy-format",
            "--data-format",
            "--oscal-format",
            "--oscal-version",
            "--update-stigs",
            "--stigs-mode",
            "--stigs-catalog",
            "--run-scanners",
            "--no-linter",
            "--no-linter-strict",
        ):
            self.assertIn(flag, content, f"validate_skill.md missing documented flag: {flag}")

    def test_module_visibility_claim(self):
        """SKILL.md and ssp/hwsw subskills describe actual local child module parsing without false invisibility claims."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        for rel_path in ("SKILL.md", "subskills/ssp_skill.md", "subskills/hwsw_skill.md"):
            doc_path = os.path.join(skill_root, rel_path)
            with open(doc_path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertNotIn(
                "Resources created inside `module` blocks are not visible to HCL parsing",
                content,
                f"{rel_path} still has stale module block invisibility claim.",
            )
            self.assertNotIn(
                "resources inside `module` blocks are not visible",
                content.lower(),
                f"{rel_path} still has stale module block invisibility claim.",
            )

    def test_extract_flags_documented(self):
        """extract_system_data.py CLI arguments and terraform plan execution warning are documented in SKILL.md."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        skill_md_path = os.path.join(skill_root, "SKILL.md")

        with open(skill_md_path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("--allow-terraform-plan", content)
        self.assertIn("--allow-scanners", content)
        self.assertIn("--module-root", content)
        # Warning about terraform plan executing code
        self.assertIn("executes", content.lower())

    def test_env_vars_indexed(self):
        """Implemented environment variables are indexed in SKILL.md and README.md."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        skill_md_path = os.path.join(skill_root, "SKILL.md")
        readme_path = os.path.join(skill_root, "README.md")

        with open(skill_md_path, encoding="utf-8") as fh:
            skill_content = fh.read()
        with open(readme_path, encoding="utf-8") as fh:
            readme_content = fh.read()

        combined = skill_content + "\n" + readme_content
        for ev in (
            "COMPLIANCE_OFFLINE",
            "SEMGREP_OFFLINE",
            "COMPLIANCE_DISABLE_LIVE_SCANNERS",
            "COMPLIANCE_ALLOW_LIVE_CLOUD_TELEMETRY",
            "COMPLIANCE_AUDIT_HMAC_KEY",
            "COMPLIANCE_SEMGREP_CONFIG",
            "COMPLIANCE_STRICT_DEPS",
            "COMPLIANCE_ALLOW_BORROWED_DEPS",
            "COMPLIANCE_SITE_PACKAGES",
            "COMPLIANCE_MAX_HCL_BYTES",
            "COMPLIANCE_MAX_XML_BYTES",
        ):
            self.assertIn(ev, combined, f"Environment variable {ev} must be documented in SKILL.md or README.md")

    def test_config_keys_in_example(self):
        """Accepted config keys (iam_groups, run_trivy, sarif_reports) and deliverable counts are documented."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        config_example_path = os.path.join(skill_root, "config", "compliance_config.yaml.example")
        skill_md_path = os.path.join(skill_root, "SKILL.md")
        readme_path = os.path.join(skill_root, "README.md")

        with open(config_example_path, encoding="utf-8") as fh:
            config_content = fh.read()
        with open(skill_md_path, encoding="utf-8") as fh:
            skill_content = fh.read()
        with open(readme_path, encoding="utf-8") as fh:
            readme_content = fh.read()

        self.assertIn("iam_groups", config_content)
        self.assertIn("run_trivy", config_content)
        self.assertIn("sarif_reports", config_content)

        # 69 deliverables + 2 auxiliary files (audit log, semantic linter report)
        combined = skill_content + "\n" + readme_content
        self.assertIn("69", combined)
        self.assertIn("compliance_engine_audit.jsonl", combined)
        self.assertIn("semantic_linter_report.json", combined)

    def test_example_stig_overrides(self):
        """STIG override examples in compliance_config.yaml.example do not carry stale versions."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        config_example_path = os.path.join(skill_root, "config", "compliance_config.yaml.example")

        with open(config_example_path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertNotIn("v1R12", content)
        self.assertNotIn("v3R4", content)

    def test_packaging_console_scripts_and_description(self):
        """Verify pyproject.toml defines console scripts and matches approved D6 scope."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        pyproject_path = os.path.join(skill_root, "pyproject.toml")

        with open(pyproject_path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("compliance-extract = ", content)
        self.assertIn("compliance-generate = ", content)
        self.assertIn("compliance-validate = ", content)
        self.assertNotIn("GovRAMP", content)
        self.assertIn("DoD IL2/IL4/IL5/IL6", content)
        self.assertIn("CJIS", content)

    def test_atc_qualifier(self):
        """Every ATC connection controls mention qualifies them as the engine's boundary review subset."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        for rel_path in (
            "templates/pta/Path_to_Authorization_Template.md",
            "subskills/pta_skill.md",
            "validate_skill.md",
        ):
            with open(os.path.join(skill_root, rel_path), encoding="utf-8") as fh:
                content = fh.read()
            self.assertNotIn(
                "must confirm the 12 core cloud/enclave boundary connection controls",
                content,
                f"{rel_path} still presents the 12 ATC controls as a fixed requirement without qualifier",
            )
            self.assertNotIn(
                "the 12 NIST SP 800-53 Rev. 5 Authorization to Connect (ATC) controls",
                content,
                f"{rel_path} still presents the 12 ATC controls without qualifier",
            )
            self.assertTrue(
                "review subset" in content.lower() or "cloud connection process guide" in content.lower(),
                f"{rel_path} missing ATC review subset / DISA Cloud Connection Process Guide qualifier",
            )

    def test_no_cac_claim_for_disa_stigs(self):
        """No deliverable or validator text claims DISA STIG downloads require CAC authentication."""
        skill_root = os.path.abspath(os.path.join(TESTS_DIR, ".."))
        for rel_path in (
            "templates/pta/Path_to_Authorization_Template.md",
            "src/compliance_engine/validate_compliance_artifacts.py",
        ):
            with open(os.path.join(skill_root, rel_path), encoding="utf-8") as fh:
                content = fh.read()
            self.assertNotIn(
                "requires CAC authentication",
                content,
                f"{rel_path} still claims DISA STIG downloads require CAC authentication",
            )


if __name__ == "__main__":
    unittest.main()
