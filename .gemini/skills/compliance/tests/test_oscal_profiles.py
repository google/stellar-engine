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

"""OSCAL import-profile selection by regime."""

import unittest

from compliance_engine import oscal_generator


def _inventory(impact: str, baseline: str = "") -> dict:
    return {
        "system_information": {"system_name": "Test", "system_abbreviation": "TST", "impact_level": impact, "compliance_baseline": baseline},
        "infrastructure_components": {},
        "network_architecture": {},
    }


class OscalProfileTest(unittest.TestCase):
    """FedRAMP Rev. 5 High profile for FedRAMP High and DoD IL5 (IL5 with a remark)."""

    def test_import_profile_by_regime(self) -> None:
        cases = [
            ("IL6", "FedRAMP_rev5_HIGH-baseline_profile.json", "fedramp"),
            ("IL5", "FedRAMP_rev5_HIGH-baseline_profile.json", "fedramp"),
            ("IL4", "FedRAMP_rev5_MODERATE-baseline_profile.json", "fedramp"),
            ("IL2", "FedRAMP_rev5_MODERATE-baseline_profile.json", "fedramp"),
            ("FedRAMP High", "FedRAMP_rev5_HIGH-baseline_profile.json", "fedramp"),
            ("FedRAMP Moderate", "FedRAMP_rev5_MODERATE-baseline_profile.json", "fedramp"),
            ("FedRAMP Low", "FedRAMP_rev5_LOW-baseline_profile.json", "fedramp"),
            ("FISMA High", "NIST_SP-800-53_rev5_HIGH-baseline_profile.json", "nist"),
            ("FISMA Moderate", "NIST_SP-800-53_rev5_MODERATE-baseline_profile.json", "nist"),
            ("FISMA Low", "NIST_SP-800-53_rev5_LOW-baseline_profile.json", "nist"),
            ("CJIS", "NIST_SP-800-53_rev5_MODERATE-baseline_profile.json", "nist"),
        ]
        for impact, suffix, expected_org in cases:
            with self.subTest(impact=impact):
                ssp = oscal_generator.generate_oscal_ssp(_inventory(impact))["system-security-plan"]
                href = ssp["import-profile"]["href"]
                self.assertTrue(href.endswith(suffix), href)
                self.assertIn(expected_org, href.lower())

    def test_unsupported_regimes_fail_closed(self) -> None:
        from compliance_engine.file_helpers import UnsupportedRegimeError

        for impact in ("GovRAMP High", "StateRAMP Moderate", "FedRAMP Tailored LI-SaaS", "DoD", "FISMA", "FedRAMP", ""):
            with self.subTest(impact=impact):
                with self.assertRaises(UnsupportedRegimeError):
                    oscal_generator.generate_oscal_ssp(_inventory(impact))

    def test_il5_profile_carries_overlay_remark(self) -> None:
        for dod_level in ("IL2", "IL4", "IL5", "IL6"):
            ssp = oscal_generator.generate_oscal_ssp(_inventory(dod_level))["system-security-plan"]
            self.assertIn("SRG", ssp["import-profile"].get("remarks", ""))
        cjis_ssp = oscal_generator.generate_oscal_ssp(_inventory("CJIS"))["system-security-plan"]
        self.assertIn("CJIS Security Policy", cjis_ssp["import-profile"].get("remarks", ""))
        for civ_level in ("FedRAMP High", "FedRAMP Moderate", "FISMA High"):
            civ = oscal_generator.generate_oscal_ssp(_inventory(civ_level))["system-security-plan"]
            self.assertNotIn("remarks", civ["import-profile"])

    def test_profile_table_covers_supported_regimes(self) -> None:
        from compliance_engine.file_helpers import SUPPORTED_REGIMES

        for regime in SUPPORTED_REGIMES:
            self.assertIn(regime, oscal_generator.OSCAL_PROFILE_BY_REGIME)


if __name__ == "__main__":
    unittest.main()
