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

"""Config keys in compliance_config.yaml.example are honored by the engine."""

import json
from pathlib import Path
import tempfile
import unittest
import yaml

from compliance_engine import extract_system_data
from compliance_engine import generate_compliance_artifacts

_SKILL_ROOT = Path(__file__).resolve().parents[1]


class ConfigKeyUsageTest(unittest.TestCase):
    """Every key in compliance_config.yaml.example is honored; dead keys are removed."""

    def test_example_keys_used(self) -> None:
        """document_versions.policies.Incident_Response sets runbook version; cssp_agreement_id/cssp_endpoint are removed."""
        example_path = _SKILL_ROOT / "config" / "compliance_config.yaml.example"
        example_text = example_path.read_text(encoding="utf-8")
        example_cfg = yaml.safe_load(example_text)

        secops = example_cfg.get("security_operations", {})
        self.assertNotIn("cssp_agreement_id", secops)
        self.assertNotIn("cssp_endpoint", secops)

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "bp"
            target.mkdir()
            (target / "main.tf").write_text(
                'resource "google_project_service" "s" {\n  service = "compute.googleapis.com"\n}\n',
                encoding="utf-8",
            )
            inv = extract_system_data.extract_system_inventory(target)
            self.assertNotIn("cssp_agreement_id", inv.get("security_operations", {}))
            self.assertNotIn("cssp_endpoint", inv.get("security_operations", {}))

            inv["document_versions"] = {"policies": {"Incident_Response": "4.2.9"}}
            (target / "system_inventory.json").write_text(json.dumps(inv), encoding="utf-8")
            generate_compliance_artifacts.generate_ato_artifacts(
                str(target), policy_format="markdown", data_format="yaml", oscal_format="none"
            )
            rb_file = (
                target
                / "ato_artifacts"
                / "Incident_Response_Runbooks"
                / "IR_Compute_Resource_Compromise_Runbook.md"
            )
            self.assertIn("4.2.9", rb_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
