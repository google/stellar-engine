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

"""Scanner and SARIF scope is the target directory, never the operator CWD."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from compliance_engine import extract_system_data
from compliance_engine import generate_compliance_artifacts
from compliance_engine import poam_rules
from compliance_engine import security_scanner_bridge as ssb

_TF = 'resource "google_storage_bucket" "b" {\n  name     = "b"\n  location = "US"\n}\n'
_SARIF = {
    "version": "2.1.0",
    "runs": [{
        "tool": {"driver": {"name": "demo", "rules": [{"id": "OUTSIDE_MARKER_RULE", "shortDescription": {"text": "OUTSIDE_MARKER"}}]}},
        "results": [{"ruleId": "OUTSIDE_MARKER_RULE", "level": "error", "message": {"text": "OUTSIDE_MARKER finding"},
                     "locations": [{"physicalLocation": {"artifactLocation": {"uri": "outside.py"}, "region": {"startLine": 1}}}]}],
    }],
}


class ScannerScopeTest(unittest.TestCase):
    """derive_poam_findings needs an explicit target and reads nothing above it."""

    def test_derive_poam_findings_requires_target_dir(self) -> None:
        with self.assertRaises(TypeError):
            poam_rules.derive_poam_findings({})  # pylint: disable=missing-kwoa

    def test_scanners_receive_target_not_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            (parent / "outside.sarif").write_text(json.dumps(_SARIF), encoding="utf-8")
            (parent / "outside.tf").write_text(_TF, encoding="utf-8")
            target = parent / "child"
            target.mkdir()
            (target / "main.tf").write_text(_TF, encoding="utf-8")
            cwd = os.getcwd()
            os.chdir(parent)
            try:
                items = poam_rules.derive_poam_findings({"system_information": {"workspace_path": "."}}, target_dir=str(target))
                no_target = poam_rules.derive_poam_findings({"system_information": {"workspace_path": "."}}, target_dir=None)
            finally:
                os.chdir(cwd)
            self.assertNotIn("OUTSIDE_MARKER", json.dumps(items))
            self.assertNotIn("OUTSIDE_MARKER", json.dumps(no_target))
            (target / "inside.sarif").write_text(json.dumps(_SARIF).replace("OUTSIDE_MARKER", "INSIDE_MARKER"), encoding="utf-8")
            self.assertIn("INSIDE_MARKER", json.dumps(poam_rules.derive_poam_findings({}, target_dir=str(target))))

    def test_inventory_has_no_workspace_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "t"
            target.mkdir()
            (target / "main.tf").write_text(_TF, encoding="utf-8")
            with mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "1"}):
                inventory = extract_system_data.extract_system_inventory(str(target))
            self.assertNotIn("workspace_path", inventory["system_information"])

    def test_scanner_derivation_runs_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "blueprints" / "il5" / "t"
            target.mkdir(parents=True)
            (target / "main.tf").write_text(_TF, encoding="utf-8")
            with mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "1", "COMPLIANCE_OFFLINE": "1"}):
                extract_system_data.extract_system_inventory(str(target))
                real = ssb.scan_and_derive_poam_items
                with mock.patch.object(ssb, "scan_and_derive_poam_items", side_effect=real) as spy, \
                        mock.patch.object(poam_rules, "scan_and_derive_poam_items", side_effect=real) as spy2:
                    generate_compliance_artifacts.generate_ato_artifacts(
                        str(target), policy_format="markdown", data_format="both", oscal_format="json"
                    )
            calls = spy.call_args_list + spy2.call_args_list
            self.assertEqual(len(calls), 1, calls)
            self.assertEqual(Path(calls[0].args[0]).resolve(), target.resolve())


if __name__ == "__main__":
    unittest.main()
