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

"""Unconfigured packages carry configuration tokens, never invented identifiers or vendors."""

import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock
import zipfile

from compliance_engine import extract_system_data
from compliance_engine import file_helpers
from compliance_engine import generate_compliance_artifacts

_FORBIDDEN = re.compile(
    r"DITPR-|EMASS-[A-Z0-9]|OMB-[A-Z]+-20[0-9]{2}|CSSP-MOA-ACTIVE|UII-(GCP|IAC|APP|CTR|LIB)-|Splunk|CrowdStrike|ServiceNow|"
    r"GitLab|Tenable|Enterprise Master Agreement"
)
_TF = (
    'resource "google_storage_bucket" "b" {\n  name     = "b"\n  location = "US"\n}\n'
    'resource "google_kms_crypto_key" "k" {\n  name = "k"\n  version_template {\n    protection_level = "SOFTWARE"\n  }\n}\n'
    'resource "google_compute_instance" "vm" {\n  name = "vm"\n  machine_type = "e2-small"\n  zone = "us-east4-a"\n}\n'
)


class TruthfulDefaultsTest(unittest.TestCase):
    """Generated package for a target without compliance_config.yaml."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.target = Path(cls._tmp.name) / "blueprints" / "il5" / "demo"
        cls.target.mkdir(parents=True)
        (cls.target / "main.tf").write_text(_TF, encoding="utf-8")
        user_items = "poam_items:\n  - weakness_name: W\n    control_identifier: AC-2\n    scheduled_completion_date: '2030-01-01'\n"
        (cls.target / "compliance_config.yaml").write_text("system_information:\n  impact_level: IL5\n" + user_items, encoding="utf-8")
        with mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "1", "COMPLIANCE_OFFLINE": "1"}):
            extract_system_data.extract_system_inventory(str(cls.target))
            generate_compliance_artifacts.generate_ato_artifacts(str(cls.target), policy_format="markdown", data_format="both", oscal_format="json")
        cls.texts = {}
        for path in [cls.target / "system_inventory.json", *(cls.target / "ato_artifacts").rglob("*")]:
            if path.suffix in (".xlsm", ".docx"):
                with zipfile.ZipFile(path) as zf:
                    cls.texts[str(path)] = " ".join(zf.read(n).decode("utf-8", "ignore") for n in zf.namelist() if n.endswith(".xml"))
            elif path.is_file():
                cls.texts[str(path)] = path.read_text(encoding="utf-8", errors="ignore")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_no_fabricated_identifiers_without_config(self) -> None:
        hits = {p: _FORBIDDEN.search(t).group(0) for p, t in self.texts.items() if _FORBIDDEN.search(t)}
        self.assertEqual(hits, {})

    def test_hwsw_status_pending(self) -> None:
        for name in ("Hardware_Software_Inventory.yaml", "PPSM_Ports_Protocols_Services.yaml"):
            texts = [t for p, t in self.texts.items() if p.endswith(name)]
            self.assertTrue(texts, name)
            self.assertNotIn('"Approved"', texts[0])
        import openpyxl  # pylint: disable=import-outside-toplevel

        path = next(self.target.rglob("Hardware_Software_Inventory.xlsm"))
        wb = openpyxl.load_workbook(path, keep_vba=True)
        statuses = [wb["Hardware"].cell(row=r, column=20).value for r in range(8, 31)]
        statuses += [wb["Software"].cell(row=r, column=25).value for r in range(8, 31)]
        wb.close()
        filled = [v for v in statuses if v]
        self.assertTrue(filled)
        self.assertNotIn("Approved", filled)
        self.assertTrue(all(v == "Pending Assessment" for v in filled), filled)

    def test_poam_funding_not_fabricated(self) -> None:
        import openpyxl  # pylint: disable=import-outside-toplevel

        path = next(self.target.rglob("Plan_of_Action_and_Milestones.xlsm"))
        wb = openpyxl.load_workbook(path, keep_vba=True)
        values = {str(c.value) for row in wb["POA&M"].iter_rows(min_row=8) for c in row if c.value is not None}
        wb.close()
        self.assertTrue(values)
        self.assertFalse(values & {"Funded", "$0.00", "40"}, values & {"Funded", "$0.00", "40"})

    def test_csp_package_label_per_regime(self) -> None:
        self.assertEqual(file_helpers.DEFAULT_CSP_PATO_PACKAGE_ID, "FR1805751477")
        for text in self.texts.values():
            self.assertNotRegex(text, r"(DoD|IL5) (Provisional Authorization|PA) (ID|Number)[^\n]{0,40}FR1805751477")


if __name__ == "__main__":
    unittest.main()
