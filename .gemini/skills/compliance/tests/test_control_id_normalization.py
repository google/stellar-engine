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

"""Control identifiers are compared by normalized base id, never by string prefix."""

import unittest

from compliance_engine import poam_rules
from compliance_engine import semantic_linter

_VAGUE_IA2 = "Accounts are protected by the organization password policy and periodic reviews of logins."


class ControlIdNormalizationTest(unittest.TestCase):
    """base_control_id() and the linter rule lookup."""

    def test_base_control_id(self) -> None:
        cases = {
            "IA-2": "IA-2",
            "IA-02": "IA-2",
            "ia-2(1)": "IA-2",
            "[r5] SC-07(05)": "SC-7",
            "IA-20": "IA-20",
            "SI-22": "SI-22",
            "AU-02": "AU-2",
            "": "",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(poam_rules.base_control_id(raw), expected)

    def test_linter_does_not_prefix_match(self) -> None:
        ok, _, _ = semantic_linter.evaluate_control_substance("IA-2", _VAGUE_IA2, {})
        self.assertFalse(ok)
        for unrelated in ("IA-20", "IA-21", "IA-22"):
            with self.subTest(control=unrelated):
                ok, status, _ = semantic_linter.evaluate_control_substance(unrelated, _VAGUE_IA2, {})
                self.assertTrue(ok, status)
        no_scan = "Issues are handled according to the documented organizational procedure for each system component."
        self.assertFalse(semantic_linter.evaluate_control_substance("SI-2", no_scan, {})[0])
        for unrelated in ("SI-20", "SI-21", "SI-22", "SI-23"):
            with self.subTest(control=unrelated):
                self.assertTrue(semantic_linter.evaluate_control_substance(unrelated, no_scan, {})[0])

    def test_zero_padded_ids_are_evaluated(self) -> None:
        self.assertFalse(semantic_linter.evaluate_control_substance("IA-02", _VAGUE_IA2, {})[0])
        boundary = "Traffic is reviewed by the operations team according to the documented procedure."
        self.assertFalse(semantic_linter.evaluate_control_substance("SC-07", boundary, {})[0])
        self.assertFalse(semantic_linter.evaluate_control_substance("SC-7(5)", boundary, {})[0])


if __name__ == "__main__":
    unittest.main()
