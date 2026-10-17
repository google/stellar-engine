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

"""Dynamic DISA STIG table in Path_to_Authorization.md matches StigResolver output."""

from pathlib import Path
import tempfile
import unittest

from compliance_engine import generate_compliance_artifacts
from compliance_engine import stig_resolver


class PtaStigTableTest(unittest.TestCase):
    """PTA STIG table must be generated from StigResolver, not a static 10-row list."""

    def test_rows_from_resolver(self) -> None:
        """A blueprint with no VMs/DBs has no RHEL/Ubuntu/PostgreSQL STIG rows in the PTA."""
        inv = {
            "system_information": {
                "system_name": "BigQuery Analytics",
                "system_abbreviation": "BQA",
                "impact_level": "IL5",
                "compliance_baseline": "NIST SP 800-53 Rev. 5 / DoD IL5",
                "organization": "Example Agency",
                "primary_location": "us-east4",
            },
            "infrastructure_components": {
                "services_enabled": ["bigquery.googleapis.com", "cloudkms.googleapis.com"],
                "databases": [{"name": "analytics-ds", "type": "google_bigquery_dataset"}],
                "compute_instances": [],
                "gke_clusters": [],
            },
            "network_architecture": {},
            "application_components": {},
        }
        with tempfile.TemporaryDirectory() as td:
            resolver = stig_resolver.StigResolver(target_dir=td)
            expected_stigs = resolver.evaluate_applicable_stigs(inv)
            expected_slugs = {item["slug"] for item in expected_stigs}

            template_path = Path(generate_compliance_artifacts.TEMPLATES_DIR) / "pta" / "Path_to_Authorization_Template.md"
            raw_pta = template_path.read_text(encoding="utf-8")
            rendered = generate_compliance_artifacts.populate_placeholders(raw_pta, inv, doc_version="1.0.0")

            # Must not contain unrelated OS or database STIGs when no VMs/RDBMS exist
            for absent_slug in (
                "red_hat_enterprise_linux_9",
                "canonical_ubuntu_2204_lts",
                "crunchy_data_postgres_16",
                "kubernetes",
            ):
                self.assertNotIn(absent_slug, expected_slugs)
                self.assertNotIn(f"[{absent_slug}]", rendered)

            # Every applicable STIG from StigResolver must appear in the rendered PTA table
            for item in expected_stigs:
                self.assertIn(item["title"], rendered)
                self.assertIn(f"`{item['version']}`", rendered)


if __name__ == "__main__":
    unittest.main()
