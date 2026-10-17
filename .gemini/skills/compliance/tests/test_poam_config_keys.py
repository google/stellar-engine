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

"""POA&M configuration keys survive extraction and are read from the documented place."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from compliance_engine import extract_system_data
from compliance_engine import poam_rules
from compliance_engine import security_scanner_bridge as ssb

_TF = 'resource "google_storage_bucket" "b" {\n  name     = "b"\n  location = "US"\n}\n'
_BROKEN = 'resource "google_compute_instance" "vm" {\n  name = "vm\n  zone = [[[\n'


def _extract(cfg: str):
    tmp = tempfile.TemporaryDirectory()
    target = Path(tmp.name) / "blueprints" / "il5" / "t"
    target.mkdir(parents=True)
    (target / "main.tf").write_text(_TF, encoding="utf-8")
    (target / "broken.tf").write_text(_BROKEN, encoding="utf-8")
    (target / "compliance_config.yaml").write_text("system_information:\n  system_name: Demo\n  impact_level: IL5\n" + cfg, encoding="utf-8")
    with mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "1"}):
        inventory = extract_system_data.extract_system_inventory(str(target))
    return tmp, target, inventory


class PoamConfigKeysTest(unittest.TestCase):
    """include_unparsed_blueprints_in_poam and include_scanner_failures_in_poam."""

    def _unparsed_items(self, inventory, target):
        return [i for i in poam_rules.derive_poam_findings(inventory, target_dir=str(target)) if "could not be parsed" in str(i.get("title"))]

    def test_include_unparsed_false(self) -> None:
        tmp, target, inventory = _extract("")
        with tmp:
            self.assertTrue(inventory["infrastructure_components"]["unparsed_terraform_files"], "fixture must yield an unparsed file")
            self.assertTrue(self._unparsed_items(inventory, target))
        tmp, target, inventory = _extract("include_unparsed_blueprints_in_poam: false\n")
        with tmp:
            self.assertIs(inventory.get("include_unparsed_blueprints_in_poam"), False)
            self.assertEqual(self._unparsed_items(inventory, target), [])

    def test_include_scanner_failures_nested(self) -> None:
        for inventory in (
            {"security_scanners": {"include_scanner_failures_in_poam": True}},
            {"include_scanner_failures_in_poam": True},
        ):
            with self.subTest(inventory=inventory), tempfile.TemporaryDirectory() as tmp:
                with mock.patch.object(ssb, "scan_and_derive_poam_items", return_value=[]) as spy, \
                        mock.patch.object(poam_rules, "scan_and_derive_poam_items", spy):
                    poam_rules.derive_poam_findings(inventory, target_dir=tmp)
                self.assertTrue(spy.call_args.kwargs["config"]["include_scanner_failures_in_poam"])


if __name__ == "__main__":
    unittest.main()
