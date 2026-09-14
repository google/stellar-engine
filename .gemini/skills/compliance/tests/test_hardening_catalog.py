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
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import service_catalog
from service_catalog import resolve_gcp_service


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

    def test_genuine_token_matches_still_classify(self) -> None:
        """Anchoring must not cost real classifications."""
        cases = {
            "aiplatform.googleapis.com": "AI & Machine Learning",
            "future-vertex-ai.googleapis.com": "AI & Machine Learning",
            "networkconnectivity.googleapis.com": "Network & Connectivity",
            "cloudsql.googleapis.com": "Database Management",
            "cloudtrace.googleapis.com": "Observability & Audit",
        }
        for api, expected in cases.items():
            with self.subTest(api=api):
                self.assertEqual(self._heuristic_category(api), expected)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
