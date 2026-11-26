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

"""Checks the NGFW instance template and bootstrap hardening in Stage 2b."""

import pathlib
import re
import unittest
from xml.etree import ElementTree

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_IL5_NET_DIR = _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw"
_BROKEN_ALGORITHMS = {"3des", "sha1", "md5", "group1", "group2"}
_LEGACY_ALGORITHMS = _BROKEN_ALGORITHMS | {"aes-128-cbc"}
_CRYPTO_PROFILE_FAMILIES = {
    "global-protect-app-crypto-profiles",
    "ike-crypto-profiles",
    "ipsec-crypto-profiles",
}


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _bootstrap_xml():
    """Returns the bootstrap template parsed without template directives."""
    text = (_IL5_NET_DIR / "templates/bootstrap.xml.tpl").read_text(
        encoding="utf-8"
    )
    text = re.sub(r"%\{[^}]*\}", "", text)
    text = re.sub(r"\$\{[^}]*\}", "placeholder", text)
    return ElementTree.fromstring(text)


def _members(element, path):
    """Returns the member values below path, or the text of path itself."""
    values = [m.text for m in element.findall(f"{path}/member")]
    if values:
        return values
    return [e.text for e in element.findall(path)]


def _element_values(element):
    """Returns stripped lowercase text values for all descendant elements."""
    return {
        node.text.strip().lower()
        for node in element.iter()
        if node.text and node.text.strip()
    }


class TestNgfwTemplateHardening(unittest.TestCase):
    def setUp(self):
        ngfw_tf = (_IL5_NET_DIR / "ngfw.tf").read_text(encoding="utf-8")
        self.template = _top_block(
            ngfw_tf,
            'resource "google_compute_region_instance_template" '
            '"ngfw_template"',
        )
        self.crypto = _bootstrap_xml().find(".//ike/crypto-profiles")

    def _assert_argument(self, name, value):
        """Asserts that the template sets name to value on its own line."""
        self.assertRegex(
            self.template,
            rf"(?m)^\s*{re.escape(name)}\s*=\s*{re.escape(value)}\s*(#.*)?$",
        )

    def test_template_region_follows_the_iterated_region(self):
        # The managed instance group for a region only accepts a regional
        # template from the same region.
        self._assert_argument("for_each", "var.regions")
        self._assert_argument("region", "each.value")

    def test_template_metadata_blocks_console_and_project_keys(self):
        self._assert_argument("serial-port-enable", '"false"')
        self._assert_argument("block-project-ssh-keys", '"true"')
        # Serial port logging stays requested for boot diagnosis.
        self._assert_argument("serial-port-logging-enable", '"true"')

    def test_default_ike_profile_matches_the_strong_named_profile(self):
        profiles = self.crypto.find("ike-crypto-profiles")
        default = profiles.find("entry[@name='default']")
        strong = profiles.find("entry[@name='Suite-B-GCM-256']")
        for path in ("encryption", "hash", "dh-group"):
            with self.subTest(path=path):
                values = _members(default, path)
                self.assertEqual(values, _members(strong, path))
                self.assertFalse(_LEGACY_ALGORITHMS.intersection(values))

    def test_default_ipsec_profile_matches_the_strong_named_profile(self):
        profiles = self.crypto.find("ipsec-crypto-profiles")
        default = profiles.find("entry[@name='default']")
        strong = profiles.find("entry[@name='Suite-B-GCM-256']")
        for path in ("esp/encryption", "esp/authentication", "dh-group"):
            with self.subTest(path=path):
                values = _members(default, path)
                self.assertEqual(values, _members(strong, path))
                self.assertFalse(_LEGACY_ALGORITHMS.intersection(values))

    def test_globalprotect_app_crypto_profiles_is_empty(self):
        # PAN-OS only allows sha1 in GlobalProtect crypto authentication, so
        # keeping this unused container empty removes aes-128-cbc and sha1.
        profiles = self.crypto.find("global-protect-app-crypto-profiles")
        self.assertIsNotNone(profiles)
        self.assertEqual(list(profiles), [])
        self.assertFalse(_element_values(profiles))

    def test_default_crypto_profiles_reject_legacy_algorithms(self):
        families = list(self.crypto)
        self.assertTrue(
            _CRYPTO_PROFILE_FAMILIES.issubset({f.tag for f in families})
        )
        defaults_checked = 0
        for family in families:
            for entry in family.findall("entry[@name='default']"):
                defaults_checked += 1
                with self.subTest(family=family.tag):
                    self.assertFalse(
                        _LEGACY_ALGORITHMS.intersection(_element_values(entry))
                    )
        self.assertGreaterEqual(defaults_checked, 2)

    def test_all_crypto_profiles_reject_broken_algorithms(self):
        # PAN-OS predefined Suite-B-GCM-128 uses aes-128-cbc for IKEv2 per
        # RFC 6379, so check every profile entry against broken algorithms.
        entries_checked = 0
        for family in self.crypto:
            for entry in family.findall("entry"):
                entries_checked += 1
                with self.subTest(family=family.tag, entry=entry.get("name")):
                    self.assertFalse(
                        _BROKEN_ALGORITHMS.intersection(_element_values(entry))
                    )
        self.assertGreater(entries_checked, 0)

    def test_allow_rules_log_at_session_end_only(self):
        rules = _bootstrap_xml().findall(".//rulebase/security/rules/entry")
        allow_rules = [r for r in rules if r.findtext("action") == "allow"]
        self.assertTrue(allow_rules)
        for rule in allow_rules:
            with self.subTest(rule=rule.get("name")):
                self.assertEqual(rule.findtext("log-end"), "yes")
                self.assertIsNone(rule.find("log-start"))


if __name__ == "__main__":
    unittest.main()
