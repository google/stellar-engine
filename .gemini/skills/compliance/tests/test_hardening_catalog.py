#!/usr/bin/env python3
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

"""Regression tests for GCP service catalog heuristic classification.

The heuristic classifier is the last resort for service APIs absent from both
the declarative catalog and any user override. Whatever it returns is written
into the SSP and the Hardware/Software Inventory as though it were derived
fact, so a confidently wrong classification is an evidence-integrity defect,
not a cosmetic one.
"""

import os
from pathlib import Path
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from compliance_engine import service_catalog  # noqa: E402
from compliance_engine.service_catalog import resolve_gcp_service  # noqa: E402
import yaml  # noqa: E402  (after the package, which applies COMPLIANCE_SITE_PACKAGES)


class TestHardeningServiceCatalog(unittest.TestCase):
    """Guards the heuristic fallback against unanchored substring matching."""

    def _heuristic_category(self, api: str) -> str:
        """Returns the inferred category, asserting the API is not catalog-backed.

        Args:
            api: Fully qualified GCP service API domain.

        Returns:
            The resolved category string.
        """
        self.assertNotIn(
            api.lower(),
            service_catalog.get_service_catalog(),
            f"'{api}' is catalog-backed, so this test would not exercise the heuristic",
        )
        category, _, _ = resolve_gcp_service(api)
        return category

    def test_substring_collisions_are_not_classified(self) -> None:
        """A keyword buried inside an unrelated word must not drive classification.

        'retail' contains 'ai'; 'dialogflow' and 'datacatalog' contain 'log'.
        Each of these was previously reported with a confident but wrong
        category.
        """
        for api, wrong_category in (
            ("retail.googleapis.com", "AI & Machine Learning"),
            ("dialogflow.googleapis.com", "Observability & Audit"),
            ("datacatalog.googleapis.com", "Observability & Audit"),
        ):
            with self.subTest(api=api):
                category = self._heuristic_category(api)
                self.assertNotEqual(
                    category,
                    wrong_category,
                    f"'{api}' must not be classified as '{wrong_category}' on a substring collision",
                )
                # Falls back to the neutral, self-evidently-generic label.
                self.assertTrue(
                    category.endswith("Cloud Service"),
                    f"unmatched service '{api}' should get a neutral label, got '{category}'",
                )

    def test_heuristic_category_synthetic_domains(self) -> None:
        """Anchoring must not cost real classifications on synthetic uncataloged domains."""
        cases = {
            "aiplatform-synthetic.example.googleapis.com": "AI & Machine Learning",
            "future-vertex-ai.example.googleapis.com": "AI & Machine Learning",
            "networkconnectivity-synthetic.example.googleapis.com": "Network & Connectivity",
            "cloudsql-synthetic.example.googleapis.com": "Database Management",
            "cloudtrace-synthetic.example.googleapis.com": "Observability & Audit",
        }
        for api, expected in cases.items():
            with self.subTest(api=api):
                self.assertEqual(self._heuristic_category(api), expected)

    def test_genuine_token_matches_still_classify(self) -> None:
        """Alias preserving backwards-compatible test name for synthetic heuristic classification."""
        self.test_heuristic_category_synthetic_domains()

    def test_qualifier_prefix_is_stripped_for_matching(self) -> None:
        """A leading 'cloud'/'google' qualifier must not hide the real keyword."""
        self.assertEqual(
            self._heuristic_category("cloudkms-preview.googleapis.com"),
            "Security & Access Control",
        )

    def test_unknown_service_is_not_fabricated(self) -> None:
        """An unrecognized service must be labelled neutrally, never guessed."""
        category, display_name, purpose = resolve_gcp_service("zzqqxx.googleapis.com")
        self.assertEqual(category, "Zzqqxx Cloud Service")
        self.assertIn("zzqqxx.googleapis.com", display_name)
        self.assertIn("zzqqxx.googleapis.com", purpose)


class _DuplicateKeyRejectingLoader(yaml.SafeLoader):
    """SafeLoader that raises on duplicate mapping keys (PyYAML keeps the last one)."""


def _construct_unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    """Builds a mapping, failing on a repeated key instead of silently overwriting it."""
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_DuplicateKeyRejectingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


class TestShippedCatalogFile(unittest.TestCase):
    """The shipped catalog must be exactly what service_catalog.py expects."""

    def setUp(self) -> None:
        # yaml.load is safe here: the loader is a SafeLoader subclass.
        with open(service_catalog.DEFAULT_CATALOG_PATH, "r", encoding="utf-8") as handle:
            self.document = yaml.load(handle, Loader=_DuplicateKeyRejectingLoader)

    def test_entries_have_the_expected_shape(self) -> None:
        """Every entry has exactly category/display_name/purpose as non-empty strings."""
        self.assertEqual(list(self.document), ["services"])
        services = self.document["services"]
        self.assertGreater(len(services), 0)
        for domain, attrs in services.items():
            with self.subTest(domain=domain):
                self.assertEqual(set(attrs), {"category", "display_name", "purpose"})
                for field, value in attrs.items():
                    self.assertIsInstance(value, str, field)
                    self.assertTrue(value.strip(), field)

    def test_keys_are_lowercase_api_domains(self) -> None:
        """resolve_gcp_service lowercases its input, so a mixed-case key never matches."""
        for domain in self.document["services"]:
            with self.subTest(domain=domain):
                self.assertEqual(domain, domain.lower())
                self.assertTrue(domain.endswith(".googleapis.com"))

    def test_loader_returns_the_file_contents(self) -> None:
        """parse_simple_yaml_services must neither drop nor alter entries."""
        loaded = service_catalog.parse_simple_yaml_services(service_catalog.DEFAULT_CATALOG_PATH)
        self.assertEqual(loaded, self.document["services"])

    def test_real_gcp_services_are_cataloged_and_purpose_has_no_unverifiable_auth_claims(self) -> None:
        """Real GCP services are cataloged and purpose strings contain no unverifiable authorization claims."""
        services = self.document["services"]
        for required_domain in (
            "networkconnectivity.googleapis.com",
            "cloudtrace.googleapis.com",
            "aiplatform.googleapis.com",
            "cloudsql.googleapis.com",
        ):
            self.assertIn(required_domain, services)
        for domain, attrs in services.items():
            purpose = attrs.get("purpose", "")
            self.assertNotIn("FedRAMP High", purpose, f"{domain} purpose carries unverifiable FedRAMP High claim")
            self.assertNotIn("Under DISA Review", purpose, f"{domain} purpose carries Under DISA Review claim")
            self.assertNotIn("DoD IL5", purpose, f"{domain} purpose carries DoD IL5 claim")


class TestCatalogLoaderAndOverrides(unittest.TestCase):
    """Loader failure handling and custom-service override lookups."""

    def test_malformed_catalog_yields_empty_mapping_and_a_warning(self) -> None:
        """A file PyYAML rejects must not be half-parsed by a lenient fallback."""
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "catalog.yaml"
            bad.write_text(
                'services:\n  a.googleapis.com:\n    category: "A"\n  b.googleapis.com: [unclosed\n',
                encoding="utf-8",
            )
            with self.assertLogs(service_catalog.logger, level="WARNING"):
                self.assertEqual(service_catalog.parse_simple_yaml_services(str(bad)), {})

    def test_custom_service_keys_match_case_insensitively(self) -> None:
        """A mixed-case key in compliance_config.yaml must still override."""
        custom = {"MyVendor.example.com": {"category": "Firewall", "display_name": "Vendor FW", "purpose": "Filtering"}}
        self.assertEqual(
            resolve_gcp_service("myvendor.example.com", custom),
            ("Firewall", "Vendor FW", "Filtering"),
        )

    def test_custom_service_empty_values_fall_back_to_defaults(self) -> None:
        """None or blank override values must not reach the inventory as 'None' or ''."""
        category, name, purpose = resolve_gcp_service(
            "x.example.com", {"x.example.com": {"category": None, "display_name": "  ", "purpose": ""}}
        )
        self.assertEqual(category, "Custom Service")
        self.assertEqual(name, "x.example.com")
        self.assertEqual(purpose, "Configured custom service (x.example.com)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
