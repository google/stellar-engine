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

"""Every file under templates/ is consumed or documented as reference-only, and 5 scenario runbooks export."""

import json
from pathlib import Path
import tempfile
import unittest

from compliance_engine import generate_compliance_artifacts
from compliance_engine import validate_compliance_artifacts

_SKILL_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATES_DIR = _SKILL_ROOT / "templates"


class TemplateInventoryTest(unittest.TestCase):
    """Verifies dead YAML templates are removed and blank runbook template is reference-only."""

    def test_every_template_consumed_or_reference(self) -> None:
        """No dead HWSW/POAM/PPSM YAML templates remain, and every template is accounted for."""
        for dead_rel in (
            "hwsw/HWSW_Template.yaml",
            "poam/POAM_Template.yaml",
            "ppsm/PPSM_Template.yaml",
        ):
            self.assertFalse(
                (_TEMPLATES_DIR / dead_rel).exists(),
                f"Dead YAML template should be removed: {dead_rel}",
            )

        # Reference-only template must remain documented in runbooks_skill.md
        runbook_ref = _TEMPLATES_DIR / "runbooks" / "Incident_Response_Runbook_Template.md"
        self.assertTrue(runbook_ref.is_file())
        runbooks_skill = (_SKILL_ROOT / "subskills" / "runbooks_skill.md").read_text(encoding="utf-8")
        self.assertIn("Incident_Response_Runbook_Template.md", runbooks_skill)

    def test_runbook_set(self) -> None:
        """Exported Incident_Response_Runbooks contains exactly the 5 scenario runbooks (no blank template)."""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "bp"
            target.mkdir()
            inv = {
                "system_information": {
                    "system_name": "RunbookSetTest",
                    "system_abbreviation": "RST",
                    "impact_level": "IL5",
                    "compliance_baseline": "NIST SP 800-53 Rev. 5 / DoD IL5",
                    "organization": "Example Org",
                    "primary_location": "us-east4",
                },
                "personnel_roles": {
                    "authorizing_official": {"name": "AO"},
                    "system_owner": {"name": "SO"},
                    "issm": {"name": "ISSM"},
                    "isso": {"name": "ISSO"},
                },
                "infrastructure_components": {"services_enabled": ["compute.googleapis.com"]},
                "network_architecture": {},
                "application_components": {},
            }
            (target / "system_inventory.json").write_text(json.dumps(inv), encoding="utf-8")
            generate_compliance_artifacts.generate_ato_artifacts(
                str(target), policy_format="markdown", data_format="yaml", oscal_format="none"
            )
            rb_dir = target / "ato_artifacts" / "Incident_Response_Runbooks"
            md_files = sorted(f.name for f in rb_dir.glob("*.md"))
            self.assertEqual(
                md_files,
                [
                    "IR_Compute_Resource_Compromise_Runbook.md",
                    "IR_IAM_Compromised_Credentials_Runbook.md",
                    "IR_KMS_CMEK_Compromise_Runbook.md",
                    "IR_Network_Intrusion_Runbook.md",
                    "IR_VPC_Service_Controls_Violation_Runbook.md",
                ],
            )
            results = validate_compliance_artifacts._audit_runbooks_presence(str(target / "ato_artifacts"))
            self.assertEqual(len(results), 5)
            self.assertTrue(all(r["status"] == "PASS" for r in results), results)


if __name__ == "__main__":
    unittest.main()
