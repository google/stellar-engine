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

"""Unit tests for Markdown newline and table-pipe injection sanitization."""

from pathlib import Path
import tempfile
import unittest
import zipfile

from compliance_engine import docx_generator
from compliance_engine import generate_compliance_artifacts
from compliance_engine import safe_xml as ET
from compliance_engine import validate_compliance_artifacts


class MarkdownInjectionTest(unittest.TestCase):
    """Verifies organization newline injection and table pipe escaping are neutralized."""

    def test_organization_newline_injection_neutralized_in_narratives_and_pta(self) -> None:
        inv = {
            "system_information": {
                "organization": "AgencyA\n# InjectedHeading",
                "system_name": "SysB\n# InjectedSys",
                "system_abbreviation": "SB",
                "impact_level": "FedRAMP High",
                "compliance_baseline": "FedRAMP High",
            },
            "infrastructure_components": {},
            "network_architecture": {},
            "security_operations": {"scc_enabled": False, "secops_enabled": False},
            "external_systems": {},
        }
        builders = (
            generate_compliance_artifacts.build_dynamic_system_description,
            generate_compliance_artifacts.build_threat_detection_implementation_narrative,
            generate_compliance_artifacts.build_audit_and_siem_implementation_narrative,
            generate_compliance_artifacts.build_incident_escalation_implementation_narrative,
            generate_compliance_artifacts.build_vulnerability_management_implementation_narrative,
            generate_compliance_artifacts.build_identity_and_access_implementation_narrative,
        )
        for builder in builders:
            with self.subTest(builder=builder.__name__):
                text = builder(inv)
                for line in text.splitlines():
                    self.assertFalse(
                        line.lstrip().startswith("# Injected"),
                        f"Newline heading injection survived in {builder.__name__}: {line!r}",
                    )

        gov = validate_compliance_artifacts._extract_pta_governance_metadata(inv)
        self.assertNotIn("\n", gov["org_name"])
        self.assertNotIn("\r", gov["org_name"])
        self.assertNotIn("\n", gov["sys_name"])

    def test_pta_placeholder_table_pipes_escaped_without_docx_backticks(self) -> None:
        bundle = {
            "unresolved_tokens": [],
            "config_required_vars": [
                {
                    "file": "Incident_Response_Runbooks/IR_Network_Intrusion_Runbook.docx",
                    "line": 12,
                    "variable": "[CONFIG_REQUIRED: Triage: 15m | Containment: 45m]",
                }
            ],
            "rmf_action_items": [],
            "senior_audit": {"cat_1_findings": [], "cat_2_findings": [], "cat_3_findings": []},
            "stigs_required": [],
        }
        gov = validate_compliance_artifacts._extract_pta_governance_metadata({})
        lines = validate_compliance_artifacts._render_pta_variables_and_memo(gov, bundle, {})
        md_text = "\n".join(lines)
        self.assertIn(r"[CONFIG_REQUIRED: Triage: 15m \| Containment: 45m]", md_text)

        with tempfile.TemporaryDirectory() as td:
            out_docx = Path(td) / "pta.docx"
            docx_generator.convert_markdown_to_docx(md_text, str(out_docx), allowed_boundary=td)
            with zipfile.ZipFile(out_docx, "r") as zf:
                doc_xml = zf.read("word/document.xml").decode("utf-8")
            root = ET.fromstring(doc_xml)
            w_t = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
            for el in root.iter(w_t):
                self.assertNotIn("`", el.text or "", f"Orphaned backtick in <w:t>: {el.text!r}")


if __name__ == "__main__":
    unittest.main()
