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

import json
import os
import sys
import unittest
import tempfile
from typing import Any, Dict
from unittest import mock
from pathlib import Path

skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(skill_root, "scripts"))

from generate_compliance_artifacts import (
    build_incident_escalation_implementation_narrative,
    build_threat_detection_implementation_narrative,
    format_firewall_matrix,
    format_service_accounts,
    format_separation_of_duties_table,
    generate_hwsw_inventory_yaml,
    generate_poam_matrix_yaml,
)
from compliance_engine import oscal_generator


def _schema_valid_inventory() -> Dict[str, Any]:
    """Returns the minimum inventory that clears ``validate_system_inventory_schema``.

    The OSCAL stage runs near the end of the pipeline, so a stub inventory would
    abort at schema validation and never reach it -- making a fail-closed test
    pass for entirely the wrong reason.
    """
    return {
        "system_information": {
            "system_name": "Hardening Test System",
            "organization": "Test Organization",
            "impact_level": "IL5",
            "compliance_baseline": "NIST SP 800-53 Rev. 5 Moderate",
        },
        "personnel_roles": {
            "authorizing_official": {"name": "AO", "email": "ao@example.gov"},
            "system_owner": {"name": "SO", "email": "so@example.gov"},
            "issm": {"name": "ISSM", "email": "issm@example.gov"},
            "isso": {"name": "ISSO", "email": "isso@example.gov"},
        },
        "infrastructure_components": {"services_enabled": []},
    }


class TestHardeningGenerate(unittest.TestCase):
    def test_oscal_failure_is_explicit(self):
        """A failed OSCAL export must abort the run, not yield a partial package.

        Silently continuing would emit an ATO package that looks complete but is
        missing its machine-readable SSP, which downstream GRC intake would accept
        without noticing the gap.

        ``export_oscal_artifacts`` is imported inside the body of
        ``generate_ato_artifacts``, so it must be patched on ``oscal_generator``
        (its definition site); patching the ``generate_compliance_artifacts``
        module attribute has no effect at all.
        """
        import generate_compliance_artifacts as gca
        import oscal_generator

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "system_inventory.json").write_text(
                json.dumps(_schema_valid_inventory()), encoding="utf-8"
            )
            with mock.patch.object(
                oscal_generator,
                "export_oscal_artifacts",
                side_effect=RuntimeError("simulated OSCAL schema failure"),
            ):
                with self.assertRaises(RuntimeError) as ctx:
                    gca.generate_ato_artifacts(str(target), oscal_format="json")

        # Assert on the wrapper message so the test cannot be satisfied by an
        # unrelated RuntimeError raised earlier in the pipeline.
        self.assertIn("OSCAL generation failed", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)

    def test_format_firewall_matrix_no_fabrication(self):
        result = format_firewall_matrix([])
        self.assertNotIn("allow-internal-https", result)
        self.assertIn("[NOT DETERMINED FROM SOURCE]", result)

    def test_format_service_accounts_no_fabrication(self):
        result = format_service_accounts([])
        self.assertNotIn("Standard Service Accounts", result)
        self.assertIn("[NOT DETERMINED FROM SOURCE]", result)

    def test_format_separation_of_duties_table_no_fabrication(self):
        result = format_separation_of_duties_table({})
        self.assertNotIn("gcp-network-admins", result)
        self.assertIn("[NOT DETERMINED FROM SOURCE]", result)

    def test_hardcoded_ips_removed(self):
        result = generate_hwsw_inventory_yaml({"system_information": {}, "network_architecture": {}})
        self.assertNotIn("10.0.0.0/16", result)
        self.assertNotIn("100.127.4.0/24", result)
        self.assertIn("[NOT DETERMINED FROM SOURCE]", result)

    def test_oscal_uses_resolve_system_identity_when_unconfigured(self):
        """Unconfigured system_name/system_abbreviation must not fall back to CFP."""
        unconfigured_inv = {
            "system_information": {
                "impact_level": "IL5",
                "compliance_baseline": "DoD IL5",
            },
            "infrastructure_components": {},
            "network_architecture": {},
        }
        ssp = oscal_generator.generate_oscal_ssp(unconfigured_inv)["system-security-plan"]
        comp_def = oscal_generator.generate_oscal_component_definition(unconfigured_inv)["component-definition"]
        ssp_json = json.dumps(ssp)
        comp_json = json.dumps(comp_def)
        self.assertNotIn("Cloud Foundation Platform", ssp_json)
        self.assertNotIn("CFP", ssp_json)
        self.assertNotIn("Cloud Foundation Platform", comp_json)
        self.assertNotIn("CFP", comp_json)
        self.assertEqual(ssp["system-characteristics"]["system-name"], "[CONFIG_REQUIRED: System Name]")
        self.assertEqual(ssp["system-characteristics"]["system-name-short"], "[CONFIG_REQUIRED: System Abbreviation]")
        self.assertIn("[CONFIG_REQUIRED: System Name]", ssp["metadata"]["title"])
        self.assertIn("[CONFIG_REQUIRED: System Abbreviation]", comp_def["metadata"]["title"])

    def test_dod_ir_narrative_categories(self):
        """DoD escalation narrative matches CJCSM 6510.01B Table B-A-2 and Table C-A-1."""
        inv = {"system_information": {"impact_level": "IL5", "compliance_baseline": "DoD IL5"}}
        narrative = build_incident_escalation_implementation_narrative(inv)
        siem_narrative = build_threat_detection_implementation_narrative(inv)
        for expected in (
            "Root Level Intrusion",
            "User Level Intrusion",
            "Unsuccessful Activity Attempt",
            "Denial of Service",
            "Malicious Logic",
            "Investigating",
            "Table C-A-1",
            "15 minutes",
        ):
            self.assertIn(expected, narrative)
        self.assertNotIn("Category 4 (Investigative", narrative)
        self.assertNotIn("Category 2 (User-Level Compromise / Malicious Logic)", narrative)
        import re
        self.assertIsNone(re.search(r"\b(?:2|24|48)\s*(?:hours?|h)\b", narrative))
        self.assertIsNone(re.search(r"\b(?:2|24|48)\s*(?:hours?|h)\b", siem_narrative))

    def test_fedramp_ir_narrative_channels(self):
        """Non-DoD narrative cites CISA form and fedramp_security@, not soc@cisa.gov or info@fedramp.gov."""
        inv = {"system_information": {"impact_level": "High", "compliance_baseline": "FedRAMP High"}}
        narrative = build_incident_escalation_implementation_narrative(inv)
        self.assertIn("fedramp_security@", narrative)
        self.assertIn("cisa.gov/forms/report", narrative)
        self.assertNotIn("info@fedramp.gov", narrative)
        self.assertNotIn("soc@cisa.gov", narrative)
        self.assertNotIn("4 hours", narrative)

    def test_poam_banner_factual(self):
        """POA&M banner states counts only, with no 'compliant' or '100%' wording."""
        empty_inv = {
            "system_information": {"impact_level": "IL5", "compliance_baseline": "DoD IL5"},
            "infrastructure_components": {},
        }
        yaml_empty = generate_poam_matrix_yaml(empty_inv)
        self.assertNotIn("compliant", yaml_empty.lower())
        self.assertNotIn("100%", yaml_empty)
        self.assertIn("automated_iac_coverage_status:", yaml_empty)
        self.assertIn("0 open POA&M item(s)", yaml_empty)

    def test_audit_log_failure_not_swallowed(self):
        """Symlinked audit-log path raises PermissionError instead of being swallowed."""
        import generate_compliance_artifacts as gca

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "system_inventory.json").write_text(
                json.dumps(_schema_valid_inventory()), encoding="utf-8"
            )
            ato_dir = target / "ato_artifacts"
            ato_dir.mkdir()
            os.symlink("/tmp/nonexistent_outside_audit_sink.jsonl", str(ato_dir / "compliance_engine_audit.jsonl"))
            with self.assertRaises(PermissionError):
                gca.generate_ato_artifacts(str(target), policy_format="markdown", data_format="yaml", oscal_format="none")

    def test_next_step_banner_installed(self):
        """Next-step banner prints 'compliance-validate' when run from an installed wheel without scripts/."""
        import generate_compliance_artifacts as gca

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "system_inventory.json").write_text(
                json.dumps(_schema_valid_inventory()), encoding="utf-8"
            )
            fake_scripts = str(target / "nonexistent_wheel_scripts")
            with mock.patch.object(gca, "SCRIPTS_DIR", fake_scripts), self.assertLogs(gca.logger, level="INFO") as cm:
                gca.generate_ato_artifacts(str(target), policy_format="markdown", data_format="yaml", oscal_format="none")
            log_text = "\n".join(cm.output)
            self.assertIn("compliance-validate", log_text)
            self.assertNotIn("validate_compliance_artifacts.py", log_text)

    def test_b3b_characterization_before_and_after_decomp(self):
        """Characterization test pinning B3b generator/exporter outputs before and after decomposition."""
        import generate_compliance_artifacts as gca
        from excel_hydrator import resolve_exact_sw_type

        inv = _schema_valid_inventory()
        inv["infrastructure_components"] = {
            "services_enabled": ["bigquery.googleapis.com", "kms.googleapis.com"],
            "compute_instances": [{"name": "vm-01", "zone": "us-east4-a", "machine_type": "e2-medium"}],
            "databases": [{"name": "db-01", "type": "google_sql_database_instance", "database_version": "POSTGRES_15"}],
            "kms_keys": [{"name": "key-01", "protection_level": "HSM"}],
            "service_accounts": [{"account_id": "sa-01", "email": "sa-01@proj.iam.gserviceaccount.com", "roles": ["roles/viewer"]}],
        }
        inv["network_architecture"] = {
            "vpcs": ["vpc-main"],
            "subnets_cidrs": ["10.10.0.0/24"],
            "firewall_rules": [{"name": "deny-all", "direction": "INGRESS", "action": "DENY", "ranges": ["0.0.0.0/0"]}],
        }
        sod = gca.format_separation_of_duties_table(inv)
        self.assertIn("serviceAccount:sa-01", sod)
        desc = gca.build_dynamic_system_description(inv)
        self.assertIn("Hardening Test System", desc)
        hwsw_yaml = gca.generate_hwsw_inventory_yaml(inv)
        self.assertIn("vm-01", hwsw_yaml)
        self.assertIn("Google BigQuery", hwsw_yaml)
        ppsm_yaml = gca.generate_ppsm_matrix_yaml(inv)
        self.assertIn("443", ppsm_yaml)
        populated = gca.populate_placeholders("System: {{ SYSTEM_NAME }} | {{ ORGANIZATION }}", inv)
        self.assertIn("Hardening Test System", populated)
        ssp = oscal_generator.generate_oscal_ssp(inv)["system-security-plan"]
        self.assertEqual(ssp["system-characteristics"]["system-name"], "Hardening Test System")
        self.assertEqual(resolve_exact_sw_type("postgres"), "PostgreSQL")
        self.assertEqual(resolve_exact_sw_type("terraform"), "Terraform")

    def test_b3b_functions_within_loc_and_cc_limits(self):
        """No function in B3b files exceeds 150 LOC or CC 30, and duplicate _raw_scrub_sensitive_data is removed."""
        import ast
        from compliance_engine import docx_generator

        self.assertFalse(hasattr(docx_generator, "_raw_scrub_sensitive_data"))
        src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "compliance_engine"))
        b3b_files = (
            "generate_compliance_artifacts.py",
            "oscal_generator.py",
            "excel_hydrator.py",
            "docx_generator.py",
            "template_engine.py",
            "export_strategies.py",
            "runbook_hydration.py",
            "service_catalog.py",
        )
        branch_nodes = (
            ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
            ast.With, ast.AsyncWith, ast.Assert, ast.IfExp, ast.comprehension,
        )
        violations = []
        for mod_name in b3b_files:
            mod_path = os.path.join(src_dir, mod_name)
            with open(mod_path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    loc = node.end_lineno - node.lineno + 1
                    cc = 1
                    for child in ast.walk(node):
                        if isinstance(child, branch_nodes):
                            cc += 1
                        elif isinstance(child, ast.BoolOp):
                            cc += len(child.values) - 1
                    if loc > 150 or cc > 30:
                        violations.append(f"{mod_name}:{node.name} (LOC={loc}, CC={cc})")
        self.assertEqual(violations, [], f"Oversized/complex functions remain in B3b files: {violations}")


if __name__ == "__main__":
    unittest.main()
