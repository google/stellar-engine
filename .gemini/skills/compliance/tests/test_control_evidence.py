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

"""Control status is derived from inventory evidence."""

import json
import unittest

from compliance_engine import evidence
from compliance_engine import oscal_generator

_EMPTY = {"system_information": {"system_abbreviation": "TST", "impact_level": "IL5"}, "infrastructure_components": {}, "network_architecture": {}}


def _positive():
    return {
        "system_information": {"system_abbreviation": "TST", "impact_level": "IL5"},
        "infrastructure_components": {
            "all_resources": [{"type": "google_compute_firewall", "name": "deny"}, {"type": "google_cloud_ids_endpoint", "name": "ids"}],
            "iam_bindings": [{"role": "roles/viewer", "principal": "group:a"}],
            "security_policies": [{"name": "armor"}],
            "service_perimeters": [{"name": "perim"}],
            "kms_keys": [{"name": "hsm", "protection_level": "HSM", "rotation_period": "7776000s"}],
            "storage_buckets": [{"name": "b", "cmek_encrypted": True, "uniform_bucket_level_access": True}],
            "logging_sinks": [{"name": "sink"}],
        },
        "network_architecture": {
            "vpcs": ["core"],
            "firewall_rules": [{"name": "deny-all", "action": "DENY", "direction": "INGRESS", "source_ranges": ["0.0.0.0/0"], "protocol": "all"}],
        },
    }


class ControlEvidenceTest(unittest.TestCase):
    """derive_control_status and the OSCAL builder that consumes it."""

    def _oscal_states(self, inventory):
        ssp = oscal_generator.generate_oscal_ssp(inventory)["system-security-plan"]
        reqs = ssp["control-implementation"]["implemented-requirements"]
        return {r["control-id"]: r["by-components"][0] for r in reqs}

    def test_empty_inventory_never_implemented(self) -> None:
        states = self._oscal_states(_EMPTY)
        self.assertEqual(len(states), 20)
        self.assertEqual([c for c, bc in states.items() if bc["implementation-status"]["state"] == "implemented"], [])

    def test_software_keys_no_hsm_claim(self) -> None:
        inv = json.loads(json.dumps(_EMPTY))
        inv["infrastructure_components"]["kms_keys"] = [{"name": "soft", "protection_level": "SOFTWARE"}]
        text = json.dumps(self._oscal_states(inv))
        self.assertNotIn("Level 3", text)
        self.assertNotIn("hardware-backed", text)

    def test_no_cloud_armor_without_security_policy(self) -> None:
        inv = json.loads(json.dumps(_EMPTY))
        web = {"name": "web", "action": "ALLOW", "protocol": "tcp", "ports": ["443"], "source_ranges": ["0.0.0.0/0"]}
        inv["network_architecture"]["firewall_rules"] = [web]
        result = evidence.derive_control_status(inv, "SC-7")
        self.assertNotIn("Cloud Armor", result.narrative)
        self.assertNotEqual(result.status, evidence.IMPLEMENTED)
        self.assertIn("public ingress", result.narrative)

    def test_oscal_sc8_tls_from_inventory(self) -> None:
        states = self._oscal_states(_EMPTY)
        self.assertNotIn("TLS 1.3", json.dumps(states))
        self.assertNotEqual(states["sc-8"]["implementation-status"]["state"], "implemented")

    def test_positive_evidence_fixture(self) -> None:
        inv = _positive()
        for cid in ("SC-7", "SC-12", "SC-13", "SC-28", "AC-3", "AC-4", "AC-6", "AU-12", "MP-4", "SI-4", "CM-2"):
            with self.subTest(control=cid):
                result = evidence.derive_control_status(inv, cid)
                self.assertEqual(result.status, evidence.IMPLEMENTED, result.narrative)
                self.assertTrue(result.evidence)
        states = self._oscal_states(inv)
        for cid, bc in states.items():
            if bc["implementation-status"]["state"] == "implemented":
                self.assertRegex(bc["description"], r"\d", cid)

    def test_open_poam_caps_status(self) -> None:
        result = evidence.derive_control_status(_positive(), "SC-7", open_poam_controls=["SC-7"])
        self.assertEqual(result.status, evidence.PARTIAL)

    def test_zero_padded_and_enhancement_ids(self) -> None:
        self.assertEqual(evidence.derive_control_status(_positive(), "SC-07(05)").control_id, "SC-7")
        self.assertEqual(evidence.derive_control_status(_EMPTY, "PL-2").status, evidence.PLANNED)


if __name__ == "__main__":
    unittest.main()
