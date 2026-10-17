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

"""Verifies every POA&M rule control resolves to a non-withdrawn NIST SP 800-53 Rev. 5 control."""

import json
from pathlib import Path
import unittest

from compliance_engine import poam_rules

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "nist_800_53_r5_subset.json"


class TestPoamRuleControls(unittest.TestCase):
    """Validates poam_rules control mappings against the NIST SP 800-53 Rev. 5 catalog."""

    def test_rule_controls_exist_and_not_withdrawn(self) -> None:
        catalog = json.loads(_FIXTURE.read_text(encoding="utf-8"))["controls"]
        # Sanity check: PL-2(1) is withdrawn in Rev. 5
        self.assertEqual(catalog["PL-2(1)"]["status"], "withdrawn")

        rule_ids = {r.rule_id for r in poam_rules.IAC_SECURITY_RULES}
        self.assertNotIn("UNENCRYPTED_STORAGE", rule_ids)

        for rule in poam_rules.IAC_SECURITY_RULES:
            with self.subTest(rule_id=rule.rule_id):
                ctrl_ids = poam_rules.extract_normalized_control_ids(
                    f"{rule.control} {rule.aps}", include_base_control=True
                )
                self.assertTrue(ctrl_ids, f"Rule {rule.rule_id} declares no control IDs")
                for cid in ctrl_ids:
                    self.assertIn(cid, catalog, f"Rule {rule.rule_id} control {cid} missing from Rev. 5 catalog")
                    self.assertNotEqual(
                        catalog[cid]["status"],
                        "withdrawn",
                        f"Rule {rule.rule_id} cites withdrawn Rev. 5 control {cid}",
                    )
                if rule.rule_id == "MISSING_ROLES":
                    self.assertTrue(any(c in ("PL-2", "PM-2", "PS-2") for c in ctrl_ids))
                elif rule.rule_id == "GKE_NO_WIF":
                    self.assertTrue(any(c in ("IA-9", "IA-5") for c in ctrl_ids))
                    self.assertNotIn("IA-2(1)", ctrl_ids)
                elif rule.rule_id == "DATA_GAP":
                    self.assertTrue(any(c in ("CA-7", "CM-8") for c in ctrl_ids))
                    self.assertNotIn("CA-2(1)", ctrl_ids)
                elif rule.rule_id == "DB_NO_BACKUP":
                    self.assertIn("CP-9", ctrl_ids)
                    self.assertNotIn("CP-9(1)", ctrl_ids)


if __name__ == "__main__":
    unittest.main()
