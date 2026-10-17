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

"""Per-key FIPS attribution for Cloud KMS keys."""

from pathlib import Path
import re
import unittest

import yaml

from compliance_engine import file_helpers
from compliance_engine import generate_compliance_artifacts


def _inventory(keys):
    return {
        "system_information": {"system_name": "Demo", "system_abbreviation": "DMO", "impact_level": "IL5"},
        "infrastructure_components": {"kms_keys": keys},
        "network_architecture": {},
    }


class CryptoAttributionTest(unittest.TestCase):
    """Attribution follows protection_level and version_template.algorithm only."""

    def _hwsw_kms_rows(self, keys):
        doc = yaml.safe_load(generate_compliance_artifacts.generate_hwsw_inventory_yaml(_inventory(keys)))
        text = yaml.safe_dump(doc)
        return doc, text

    def test_software_key_row(self) -> None:
        key = {"name": "soft", "protection_level": "SOFTWARE"}
        self.assertEqual(file_helpers.kms_key_fips_attribute(key), file_helpers.KMS_SOFTWARE_FIPS)
        _, text = self._hwsw_kms_rows([key])
        self.assertNotIn("Level 3", text)
        self.assertNotIn("HSM Key", text)

    def test_hsm_key_row(self) -> None:
        key = {"name": "hsm", "protection_level": "HSM", "algorithm": "EC_SIGN_P256_SHA256"}
        self.assertEqual(file_helpers.kms_key_fips_attribute(key), "FIPS 140-2 Level 3 (Cloud HSM)")
        self.assertEqual(file_helpers.kms_key_fips_attribute({"protection_level": "EXTERNAL_VPC"}), file_helpers.KMS_EXTERNAL_FIPS)
        self.assertEqual(file_helpers.kms_key_fips_attribute({}), file_helpers.NOT_DETERMINED)

    def test_algorithm_not_fabricated(self) -> None:
        key = {"name": "hsm", "protection_level": "HSM", "algorithm": "EC_SIGN_P256_SHA256"}
        self.assertEqual(file_helpers.kms_key_algorithm(key), "EC_SIGN_P256_SHA256")
        self.assertEqual(file_helpers.kms_key_algorithm({"protection_level": "HSM"}), file_helpers.NOT_DETERMINED)
        summary = file_helpers.summarize_kms_protection([key])
        self.assertNotIn("RSA-4096", summary)
        self.assertNotIn("140-3", summary)
        _, text = self._hwsw_kms_rows([key])
        self.assertNotIn("RSA-4096", text)

    def test_no_hsm_140_3_strings_in_src(self) -> None:
        pkg = Path(file_helpers.__file__).parent
        pattern = re.compile(r"140-3.{0,60}(HSM|Level 3)|(HSM|Level 3).{0,60}140-3")
        hits = [
            f"{p.name}:{n}"
            for p in sorted(pkg.glob("*.py"))
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if pattern.search(line)
        ]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
