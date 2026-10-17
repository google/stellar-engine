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

"""Scanner findings must map to accurate NIST SP 800-53 controls."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml

from compliance_engine import security_scanner_bridge as ssb


class ScannerControlMappingTest(unittest.TestCase):
    """Semgrep rule metadata and Checkov check classification govern POA&M controls."""

    def test_semgrep_metadata_preferred(self) -> None:
        rules_doc = yaml.safe_load(
            ssb.SEMGREP_BUNDLED_RULES_FILE.read_text(encoding="utf-8")
        )
        rules = rules_doc.get("rules", [])
        self.assertEqual(len(rules), 14)

        raw_results = []
        expected_by_rule = {}
        for idx, rule in enumerate(rules, start=1):
            rule_id = rule["id"]
            metadata = rule.get("metadata", {})
            nist_list = [str(c).strip() for c in metadata.get("nist-800-53", [])]
            expected_by_rule[rule_id] = " / ".join(nist_list)
            raw_results.append({
                "check_id": rule_id,
                "path": "app/main.py",
                "start": {"line": idx},
                "end": {"line": idx},
                "extra": {
                    "message": rule.get("message", "finding"),
                    "severity": rule.get("severity", "ERROR"),
                    "metadata": metadata,
                },
            })

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "app.py").write_text("x = 1\n", encoding="utf-8")
            proc = mock.MagicMock(
                returncode=0,
                stdout=json.dumps({"results": raw_results}),
                stderr="",
            )
            with (
                mock.patch.object(ssb.shutil, "which", return_value="/usr/bin/semgrep"),
                mock.patch.object(ssb, "_safe_run_subprocess", return_value=proc),
            ):
                ssb.reset_scan_cache()
                items = ssb.scan_and_derive_poam_items(
                    tmp,
                    config={"run_semgrep": True, "ingest_sarif": False},
                )

        by_check = {item["checks"]: item for item in items}
        for rule_id, expected_aps in expected_by_rule.items():
            self.assertIn(rule_id, by_check)
            self.assertEqual(
                by_check[rule_id]["aps"],
                expected_aps,
                f"rule {rule_id} mapped to {by_check[rule_id]['aps']} instead of {expected_aps}",
            )

        # Extended CWE_NIST_MAP coverage when rule metadata is absent.
        self.assertEqual(ssb.map_cwe_to_nist("CWE-295")[0], "SC-8")
        self.assertEqual(ssb.map_cwe_to_nist("CWE-330")[0], "SC-13")
        self.assertEqual(ssb.map_cwe_to_nist("CWE-338")[0], "SC-13")
        self.assertEqual(ssb.map_cwe_to_nist("CWE-489")[0], "CM-7")
        self.assertEqual(ssb.map_cwe_to_nist("CWE-95")[0], "SI-10")

    def test_checkov_oslogin_not_audit(self) -> None:
        oslogin_aps, oslogin_title = ssb.map_checkov_to_nist(
            "CKV_GCP_34",
            "Ensure that no instance in the project overrides the project setting for enabling OSLogin",
        )
        self.assertFalse(
            oslogin_aps.startswith("AU-"),
            f"CKV_GCP_34 mapped to audit control {oslogin_aps} ({oslogin_title})",
        )
        self.assertIn("IA-02", oslogin_aps)

        # Encryption in transit must map to SC-08 / SC-13, not SC-28 (at rest).
        transit_aps, _ = ssb.map_checkov_to_nist(
            "CKV_AWS_202",
            "Ensure MemoryDB data is encrypted in transit",
        )
        self.assertEqual(transit_aps, "SC-08 / SC-13")

        # Real audit log checks still map to AU-02 / AU-12.
        audit_aps, _ = ssb.map_checkov_to_nist(
            "CKV_GCP_26",
            "Ensure that VPC Flow Logs is enabled for every subnet in a VPC Network",
        )
        self.assertEqual(audit_aps, "AU-02 / AU-12")


if __name__ == "__main__":
    unittest.main()
