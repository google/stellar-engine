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

"""Single regime classifier: supported regimes, fail-closed regimes and derived helpers."""

import unittest

from compliance_engine import file_helpers
from compliance_engine.file_helpers import Regime


def _info(impact: str = "", baseline: str = "", regime: str = "") -> dict:
    return {"impact_level": impact, "compliance_baseline": baseline, "governance_regime": regime}


class RegimeClassificationTest(unittest.TestCase):
    """classify_regime() is the only place regime strings are interpreted."""

    def test_regime_matrix(self) -> None:
        cases = [
            (_info("IL5"), Regime.DOD_IL5),
            (_info("IL-5"), Regime.DOD_IL5),
            (_info("DOD_IL5"), Regime.DOD_IL5),
            (_info("", "NIST SP 800-53 Rev. 5 / DoD IL5"), Regime.DOD_IL5),
            (_info("Impact Level 5"), Regime.DOD_IL5),
            (_info("IL4"), Regime.DOD_IL4),
            (_info("IL-4"), Regime.DOD_IL4),
            (_info("IL2"), Regime.DOD_IL2),
            (_info("IL-2"), Regime.DOD_IL2),
            (_info("Impact Level 2"), Regime.DOD_IL2),
            (_info("", "NIST SP 800-53 Rev. 5 / DoD IL2"), Regime.DOD_IL2),
            (_info("IL6"), Regime.DOD_IL6),
            (_info("IL-6"), Regime.DOD_IL6),
            (_info("", "", "DoD"), Regime.UNKNOWN),
            (_info("FedRAMP"), Regime.UNKNOWN),
            (_info("FedRAMP High"), Regime.FEDRAMP_HIGH),
            (_info("", "NIST SP 800-53 Rev. 5 / FedRAMP High"), Regime.FEDRAMP_HIGH),
            (_info("FedRAMP Moderate"), Regime.FEDRAMP_MODERATE),
            (_info("FedRAMP Low"), Regime.FEDRAMP_LOW),
            (_info("FedRAMP Moderate", "NIST SP 800-53 Rev. 5 / CJIS Security Policy"), Regime.CJIS),
            (_info("StateRAMP High", "NIST SP 800-53 Rev. 5 / StateRAMP"), Regime.GOVRAMP),
            (_info("GovRAMP Moderate"), Regime.GOVRAMP),
            (_info("", "FISMA Moderate"), Regime.FISMA_MODERATE),
            (_info("FISMA High"), Regime.FISMA_HIGH),
            (_info("", "NIST SP 800-53 Rev. 5 / FISMA Low"), Regime.FISMA_LOW),
            (_info("", "FISMA"), Regime.UNKNOWN),
            (_info(), Regime.UNKNOWN),
            ("IL5", Regime.DOD_IL5),
            ("FedRAMP High", Regime.FEDRAMP_HIGH),
            (None, Regime.UNKNOWN),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(file_helpers.classify_regime(source), expected)

    def test_supported_set_matches_d6_tiers(self) -> None:
        self.assertEqual(set(file_helpers.REGIME_SUPPORT), set(Regime))
        for supported_r in (
            Regime.FEDRAMP_LOW,
            Regime.FEDRAMP_MODERATE,
            Regime.FEDRAMP_HIGH,
            Regime.FISMA_LOW,
            Regime.FISMA_MODERATE,
            Regime.FISMA_HIGH,
            Regime.DOD_IL2,
            Regime.DOD_IL4,
            Regime.DOD_IL5,
            Regime.DOD_IL6,
            Regime.CJIS,
        ):
            self.assertTrue(file_helpers.REGIME_SUPPORT[supported_r], supported_r)
        for unsupported_r in (Regime.GOVRAMP, Regime.UNKNOWN):
            self.assertFalse(file_helpers.REGIME_SUPPORT[unsupported_r], unsupported_r)
        for regime in Regime:
            self.assertEqual(file_helpers.is_supported_regime(regime), file_helpers.REGIME_SUPPORT[regime])

    def test_dod_precedes_fisma_and_tailored_fails_closed(self) -> None:
        """DoD IL2/IL4/IL5/IL6 take precedence over FISMA/FedRAMP; Tailored/LI-SaaS fails closed as UNKNOWN."""
        self.assertEqual(
            file_helpers.classify_regime(_info("IL4", "FISMA / DoD RMF")),
            Regime.DOD_IL4,
        )
        self.assertEqual(
            file_helpers.classify_regime(_info("IL5", "FISMA High / DoD RMF")),
            Regime.DOD_IL5,
        )
        self.assertEqual(
            file_helpers.classify_regime(_info("IL6", "FISMA High")),
            Regime.DOD_IL6,
        )
        self.assertEqual(
            file_helpers.classify_regime(_info("IL2", "FedRAMP Moderate")),
            Regime.DOD_IL2,
        )
        self.assertEqual(
            file_helpers.classify_regime(_info("Impact Level 2", "FedRAMP Low")),
            Regime.DOD_IL2,
        )
        self.assertEqual(
            file_helpers.classify_regime(_info("FedRAMP Tailored for Low Impact SaaS (LI-SaaS)")),
            Regime.UNKNOWN,
        )
        self.assertEqual(
            file_helpers.classify_regime(_info("High", "FedRAMP Moderate / High")),
            Regime.FEDRAMP_HIGH,
        )
        # High C/I override on a Moderate-ceiling baseline must fail closed per DISA CSP SRG V1R7 Table 3-1
        for mod_regime_info in (
            {"impact_level": "IL2", "compliance_baseline": "DoD IL2", "confidentiality_impact": "High"},
            {"impact_level": "IL4", "compliance_baseline": "DoD IL4", "confidentiality_impact": "High"},
            {"impact_level": "CJIS", "compliance_baseline": "CJIS", "integrity_impact": "High"},
            {"impact_level": "FedRAMP Moderate", "integrity_impact": "High"},
            {"impact_level": "FISMA Moderate", "availability_impact": "High"},
        ):
            with self.subTest(mod_regime_info=mod_regime_info):
                with self.assertRaises(file_helpers.UnsupportedRegimeError):
                    file_helpers.require_supported_regime(mod_regime_info)
        # Moderate C/I override on DoD IL2 is permitted (Moderate ceiling)
        self.assertEqual(
            file_helpers.require_supported_regime(
                {"impact_level": "IL2", "compliance_baseline": "DoD IL2", "confidentiality_impact": "Moderate"}
            ),
            Regime.DOD_IL2,
        )

    def test_support_follows_table(self) -> None:
        """Every regime classifies from a sample string and fails closed exactly when the table says so."""
        samples = {
            Regime.FEDRAMP_HIGH: "FedRAMP High", Regime.FEDRAMP_MODERATE: "FedRAMP Moderate", Regime.FEDRAMP_LOW: "FedRAMP Low",
            Regime.FISMA_HIGH: "FISMA High", Regime.FISMA_MODERATE: "FISMA Moderate", Regime.FISMA_LOW: "FISMA Low",
            Regime.GOVRAMP: "GovRAMP Moderate", Regime.DOD_IL2: "IL2", Regime.DOD_IL4: "IL4", Regime.DOD_IL5: "IL5",
            Regime.DOD_IL6: "IL6", Regime.CJIS: "CJIS", Regime.UNKNOWN: "",
        }
        self.assertEqual(set(samples), set(Regime))
        for regime, text in samples.items():
            with self.subTest(regime=regime):
                info = _info(text)
                self.assertEqual(file_helpers.classify_regime(info), regime)
                if file_helpers.REGIME_SUPPORT[regime]:
                    self.assertEqual(file_helpers.require_supported_regime(info), regime)
                else:
                    with self.assertRaises(file_helpers.UnsupportedRegimeError):
                        file_helpers.require_supported_regime(info)

    def test_il4_fails_closed(self) -> None:
        if file_helpers.REGIME_SUPPORT[Regime.DOD_IL4]:
            self.skipTest("IL4 enabled in REGIME_SUPPORT")
        with self.assertRaises(file_helpers.UnsupportedRegimeError):
            file_helpers.require_supported_regime(_info("IL4"))

    def test_require_supported_regime_fails_closed(self) -> None:
        for info in (
            _info("GovRAMP High"),
            _info("StateRAMP Moderate"),
            _info("FedRAMP Tailored"),
            _info("LI-SaaS"),
            _info("", "", "DoD"),
            _info("", "FISMA"),
            _info("FedRAMP"),
            _info(),
        ):
            with self.subTest(info=info):
                with self.assertRaises(file_helpers.UnsupportedRegimeError) as ctx:
                    file_helpers.require_supported_regime(info)
                message = str(ctx.exception)
                self.assertIn("FedRAMP High", message)
                self.assertIn("DoD IL5", message)
                self.assertNotIn("\n", message)
        self.assertEqual(file_helpers.require_supported_regime(_info("IL6")), Regime.DOD_IL6)
        self.assertEqual(file_helpers.require_supported_regime(_info("IL5")), Regime.DOD_IL5)
        self.assertEqual(file_helpers.require_supported_regime(_info("IL4")), Regime.DOD_IL4)
        self.assertEqual(file_helpers.require_supported_regime(_info("IL2")), Regime.DOD_IL2)
        self.assertEqual(file_helpers.require_supported_regime(_info("CJIS")), Regime.CJIS)
        self.assertEqual(file_helpers.require_supported_regime(_info("FedRAMP Moderate")), Regime.FEDRAMP_MODERATE)

    def test_dod_and_high_baseline_helpers(self) -> None:
        self.assertTrue(file_helpers.is_dod_regime(_info("IL2")))
        self.assertTrue(file_helpers.is_dod_regime(_info("IL-4")))
        self.assertTrue(file_helpers.is_dod_regime(_info("IL5")))
        self.assertTrue(file_helpers.is_dod_regime(_info("IL6")))
        self.assertFalse(file_helpers.is_dod_regime(_info("FedRAMP High")))
        self.assertFalse(file_helpers.is_dod_regime(_info("", "CJIS")))
        self.assertTrue(file_helpers.is_high_baseline_regime(_info("IL6")))
        self.assertTrue(file_helpers.is_high_baseline_regime(_info("IL5")))
        self.assertTrue(file_helpers.is_high_baseline_regime(_info("FedRAMP High")))
        self.assertTrue(file_helpers.is_high_baseline_regime(_info("FISMA High")))
        self.assertFalse(file_helpers.is_high_baseline_regime(_info("IL2")))
        self.assertFalse(file_helpers.is_high_baseline_regime(_info("IL4")))
        self.assertFalse(file_helpers.is_high_baseline_regime(_info("CJIS")))
        self.assertFalse(file_helpers.is_high_baseline_regime(_info("FedRAMP Moderate")))

    def test_derive_fips_199_impacts(self) -> None:
        self.assertEqual(file_helpers.derive_fips_199_impacts(_info("IL6")), ("High", "High", "High"))
        self.assertEqual(file_helpers.derive_fips_199_impacts(_info("IL5")), ("High", "High", "High"))
        self.assertEqual(file_helpers.derive_fips_199_impacts(_info("FedRAMP High")), ("High", "High", "High"))
        self.assertEqual(file_helpers.derive_fips_199_impacts(_info("IL4")), ("Moderate", "Moderate", "Moderate"))
        self.assertEqual(file_helpers.derive_fips_199_impacts(_info("CJIS")), ("Moderate", "Moderate", "Moderate"))
        self.assertEqual(file_helpers.derive_fips_199_impacts(_info("IL2")), ("Low", "Low", "Low"))
        self.assertEqual(file_helpers.derive_fips_199_impacts(_info("FISMA Low")), ("Low", "Low", "Low"))
        explicit = dict(_info("IL5"), confidentiality_impact="Moderate", integrity_impact="High", availability_impact="Low")
        self.assertEqual(file_helpers.derive_fips_199_impacts(explicit), ("Moderate", "High", "Low"))
        unknown = file_helpers.derive_fips_199_impacts(_info())
        self.assertTrue(all(v.startswith("[CONFIG_REQUIRED") for v in unknown), unknown)

    def test_no_regime_string_matching_outside_file_helpers(self) -> None:
        import re
        from pathlib import Path

        pattern = re.compile(r"\"IL5\" in|'IL5' in|\"DOD\" in|\[\"IL4\", \"IL5\"|\(\"IL4\", \"IL5\"|\"IL5\", \"IL6\"")
        pkg = Path(file_helpers.__file__).parent
        hits = [
            f"{p.name}:{n}"
            for p in sorted(pkg.glob("*.py"))
            if p.name != "file_helpers.py"
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if pattern.search(line)
        ]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
