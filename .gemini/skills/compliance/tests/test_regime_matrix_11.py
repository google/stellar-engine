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

"""Unit tests for 11-regime classification and third-party framework rejection."""

import unittest

from compliance_engine import file_helpers
from compliance_engine.file_helpers import Regime


class RegimeMatrix11Test(unittest.TestCase):
    """Verifies all 11 supported regimes and rejection of third-party frameworks."""

    def test_all_11_supported_regimes_classify_cleanly(self) -> None:
        cases = (
            ({"impact_level": "FedRAMP Low"}, Regime.FEDRAMP_LOW),
            ({"impact_level": "FedRAMP Moderate"}, Regime.FEDRAMP_MODERATE),
            ({"impact_level": "FedRAMP High"}, Regime.FEDRAMP_HIGH),
            ({"compliance_baseline": "FISMA Low"}, Regime.FISMA_LOW),
            ({"compliance_baseline": "FISMA Moderate"}, Regime.FISMA_MODERATE),
            ({"compliance_baseline": "FISMA High"}, Regime.FISMA_HIGH),
            ({"impact_level": "IL2"}, Regime.DOD_IL2),
            ({"impact_level": "IL4"}, Regime.DOD_IL4),
            ({"impact_level": "IL5"}, Regime.DOD_IL5),
            ({"impact_level": "IL6"}, Regime.DOD_IL6),
            ({"compliance_baseline": "CJIS Security Policy"}, Regime.CJIS),
        )
        for sys_info, expected in cases:
            with self.subTest(sys_info=sys_info):
                self.assertEqual(file_helpers.classify_regime(sys_info), expected)
                self.assertEqual(file_helpers.require_supported_regime(sys_info), expected)

    def test_third_party_frameworks_rejected_as_unknown(self) -> None:
        third_party_frameworks = (
            "SOC 2 Type II",
            "SOC2",
            "ISO 27001",
            "ISO27001",
            "HIPAA",
            "PCI-DSS",
            "PCI DSS",
            "GDPR",
        )
        for fw in third_party_frameworks:
            for impact in ("High", "Moderate", "Low", ""):
                for field in ("compliance_baseline", "governance_regime"):
                    sys_info = {"impact_level": impact, field: fw}
                    with self.subTest(sys_info=sys_info):
                        self.assertEqual(file_helpers.classify_regime(sys_info), Regime.UNKNOWN)
                        with self.assertRaises(file_helpers.UnsupportedRegimeError):
                            file_helpers.require_supported_regime(sys_info)
            with self.subTest(bare=fw):
                self.assertEqual(file_helpers.classify_regime(fw), Regime.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
