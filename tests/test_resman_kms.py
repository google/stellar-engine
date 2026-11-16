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

"""Checks Stage 1 tenant KMS configuration reads locations from tenant_info."""

import pathlib
import re
import unittest

_KMS_TF = (
    pathlib.Path(__file__).resolve().parents[1]
    / "fast/stages-aw/1-resman/kms.tf"
)


class TestResmanTenantKmsLocation(unittest.TestCase):
    def setUp(self):
        self.text = _KMS_TF.read_text(encoding="utf-8")

    def test_no_direct_each_value_locations_lookup(self):
        self.assertNotIn("each.value.locations.kms", self.text)

    def test_keyring_and_keys_read_tenant_info_locations_kms(self):
        matches = re.findall(
            r"try\(each\.value\.tenant_info\.locations\.kms\s*!=\s*\"\",\s*false\)\s*\?\s*"
            r"each\.value\.tenant_info\.locations\.kms\s*:\s*var\.regions\.primary",
            self.text,
        )
        self.assertEqual(len(matches), 3)


if __name__ == "__main__":
    unittest.main()
