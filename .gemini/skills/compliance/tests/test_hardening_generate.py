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
    format_firewall_matrix,
    format_service_accounts,
    format_separation_of_duties_table,
    generate_hwsw_inventory_yaml,
)


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
            "impact_level": "IL4",
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

if __name__ == "__main__":
    unittest.main()
