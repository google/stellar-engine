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

"""Protocol-aware public-ingress evaluation shared by every firewall consumer."""

from pathlib import Path
import re
import unittest

from compliance_engine import poam_rules
from compliance_engine import validate_compliance_artifacts

_PUBLIC = ["0.0.0.0/0"]


class FirewallExposureTest(unittest.TestCase):
    """firewall_rule_exposes_ports() honours flat and nested protocol fields."""

    def test_flat_icmp_no_ports(self) -> None:
        rule = {"name": "icmp", "protocol": "icmp", "ports": "all", "source_ranges": _PUBLIC, "direction": "INGRESS"}
        self.assertTrue(poam_rules.is_public_ingress_allow_rule(rule))
        self.assertEqual(poam_rules.firewall_rule_exposes_ports(rule, {22, 80, 3389}), [])
        self.assertEqual(poam_rules.firewall_rule_exposes_ports(dict(rule, ports=["all"]), {22}), [])

    def test_flat_tcp_empty_ports_is_all(self) -> None:
        for ports in ([], None, ""):
            with self.subTest(ports=ports):
                rule = {"protocol": "tcp", "ports": ports, "source_ranges": _PUBLIC}
                self.assertEqual(poam_rules.firewall_rule_exposes_ports(rule, {22, 3389}), [22, 3389])
        self.assertEqual(poam_rules.firewall_rule_exposes_ports({"protocol": "all", "source_ranges": _PUBLIC}, {22}), [22])
        self.assertEqual(poam_rules.firewall_rule_exposes_ports({"protocol": "tcp", "ports": ["443"], "source_ranges": _PUBLIC}, {22, 443}), [443])
        self.assertEqual(poam_rules.firewall_rule_exposes_ports({"ports": ["20-25"], "source_ranges": _PUBLIC}, {22, 80}), [22])

    def test_deny_and_disabled_rules(self) -> None:
        base = {"protocol": "tcp", "ports": ["22"], "source_ranges": _PUBLIC}
        for extra in ({"action": "DENY"}, {"type": "deny"}, {"disabled": True}, {"direction": "EGRESS"}, {"source_ranges": ["10.0.0.0/8"]}):
            with self.subTest(extra=extra):
                rule = dict(base, **extra)
                self.assertFalse(poam_rules.is_public_ingress_allow_rule(rule))
                self.assertEqual(poam_rules.firewall_rule_exposes_ports(rule, {22}), [])
        self.assertTrue(poam_rules.is_public_ingress_allow_rule(dict(base, source_ranges="::/0")))
        self.assertTrue(poam_rules.is_public_ingress_allow_rule(dict(base, source_ranges=None, sources=["*"])))

    def test_validator_does_not_flag_public_icmp_as_cat_i(self) -> None:
        inventory = {
            "system_information": {"impact_level": "IL5"},
            "network_architecture": {"firewall_rules": [{"name": "icmp", "protocol": "icmp", "ports": "all", "source_ranges": _PUBLIC}]},
            "infrastructure_components": {},
        }
        findings = validate_compliance_artifacts.evaluate_firewall_exposure(inventory)
        self.assertEqual(findings, ([], []))

    def test_only_poam_rules_defines_public_source_logic(self) -> None:
        pkg = Path(poam_rules.__file__).parent
        pattern = re.compile(r"in \[\"0\.0\.0\.0/0\", \"::/0\"|in \(\"0\.0\.0\.0/0\", \"::/0\"")
        hits = [
            f"{p.name}:{n}"
            for p in sorted(pkg.glob("*.py"))
            if p.name != "poam_rules.py"
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if pattern.search(line)
        ]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
