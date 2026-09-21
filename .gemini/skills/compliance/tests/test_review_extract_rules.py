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

"""Regression tests for the data-gap POA&M rule added during PR #241 review.

The extractor previously defaulted absent attributes to their compliant value, so
a control that was never expressed in the Terraform read as satisfied and the
matching POA&M rule could never fire. The extractor now emits ``None`` for an
undetermined attribute, and the ``DATA_GAP`` rule turns those unknowns into
visible, tracked findings.

These tests pin the property that matters for an accreditation package: unknown
must behave like a gap to be investigated, and must never be silently absorbed
into either a passing control or a duplicate of an existing finding.
"""

import sys
import unittest
from pathlib import Path

skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root / "src"))
sys.path.insert(0, str(skill_root / "scripts"))

from compliance_engine.poam_rules import IAC_SECURITY_RULES  # noqa: E402
from extract_system_data import (  # noqa: E402
    _text_attr_tristate,
    classify_and_ingest_resource,
)


def _data_gap_rule():
    """Returns the DATA_GAP rule definition from the active rule set."""
    return next(r for r in IAC_SECURITY_RULES if r.rule_id == "DATA_GAP")


class TestDataGapRule(unittest.TestCase):
    """Verifies that undetermined attributes surface as tracked POA&M findings."""

    def test_unknown_attribute_raises_a_finding(self) -> None:
        """A bucket whose CMEK posture is unknown must produce exactly one finding."""
        rule = _data_gap_rule()
        inventory = {
            "infrastructure_components": {
                "storage_buckets": [
                    {
                        "name": "b1",
                        "cmek_encrypted": True,
                        "versioning": True,
                        "uniform_bucket_level_access": True,
                    },
                    {
                        "name": "b2",
                        "cmek_encrypted": None,
                        "versioning": True,
                        "uniform_bucket_level_access": True,
                    },
                ]
            }
        }
        findings = rule.eval_fn(inventory)
        self.assertEqual(len(findings), 1)
        self.assertIn("Storage Bucket b2", findings[0])

    def test_fully_specified_inventory_produces_no_findings(self) -> None:
        """A fully-specified system must stay at zero findings.

        This is the anti-false-positive guarantee. A gap rule that fires on a
        completely described system would bury real deficiencies in noise and
        train an assessor to ignore the category.
        """
        rule = _data_gap_rule()
        inventory = {
            "infrastructure_components": {
                "storage_buckets": [
                    {
                        "name": "b1",
                        "cmek_encrypted": True,
                        "versioning": True,
                        "uniform_bucket_level_access": True,
                    }
                ]
            }
        }
        self.assertEqual(rule.eval_fn(inventory), [])

    def test_explicit_false_is_not_a_data_gap(self) -> None:
        """An attribute known to be False is a real deficiency, not an unknown.

        ``False`` is already reported by the specific control rule for that
        attribute. Reporting it again here would double-count the same weakness
        in the POA&M under two different finding identifiers.
        """
        rule = _data_gap_rule()
        inventory = {
            "infrastructure_components": {
                "storage_buckets": [
                    {
                        "name": "b1",
                        "cmek_encrypted": False,
                        "versioning": True,
                        "uniform_bucket_level_access": True,
                    }
                ]
            }
        }
        self.assertEqual(rule.eval_fn(inventory), [])

    def test_empty_inventory_is_tolerated(self) -> None:
        """An inventory with no components must not raise."""
        rule = _data_gap_rule()
        self.assertEqual(rule.eval_fn({"infrastructure_components": {}}), [])
        self.assertEqual(rule.eval_fn({}), [])


class TestExtractorDoesNotAssumeCompliance(unittest.TestCase):
    """Pins the provider-accurate defaults for unstated security attributes.

    Terraform and the Google provider default nearly every one of these controls
    to its insecure setting. The extractor previously defaulted them to the
    secure setting, which meant a blueprint that simply never mentioned a control
    was documented in the SSP as enforcing it.
    """

    def _ingest(self, res_type: str, name: str, body: dict, bucket: str) -> dict:
        """Runs one resource through the structured ingest path."""
        tf_data = {"all_resources": [], bucket: []}
        classify_and_ingest_resource(res_type, name, body, "main.tf", tf_data)
        self.assertEqual(len(tf_data[bucket]), 1, f"expected one {bucket} entry")
        return tf_data[bucket][0]

    def test_bucket_without_versioning_or_ubla_is_not_reported_as_secure(self) -> None:
        """An unconfigured bucket has versioning off and UBLA off."""
        bucket = self._ingest(
            "google_storage_bucket",
            "plain",
            {"name": "plain-bucket", "location": "US-EAST4"},
            "storage_buckets",
        )
        self.assertIs(bucket["versioning"], False)
        self.assertIs(bucket["uniform_bucket_level_access"], False)

    def test_kms_key_without_version_template_is_software(self) -> None:
        """Absent a version_template, Cloud KMS protects the key in software.

        Reporting HSM here would manufacture a FIPS 140-3 Level 3 claim, which is
        an explicit IL5 requirement and the most consequential value in the
        generated cryptographic matrix.
        """
        key = self._ingest(
            "google_kms_crypto_key",
            "plain_key",
            {"name": "plain-key", "key_ring": "kr"},
            "kms_keys",
        )
        self.assertEqual(key["protection_level"], "SOFTWARE")

    def test_kms_key_honours_declared_hsm(self) -> None:
        """An explicitly declared HSM key must still be reported as HSM."""
        key = self._ingest(
            "google_kms_crypto_key",
            "hsm_key",
            {
                "name": "hsm-key",
                "key_ring": "kr",
                "version_template": [{"protection_level": "HSM"}],
            },
            "kms_keys",
        )
        self.assertEqual(key["protection_level"], "HSM")

    def test_cloudsql_without_tls_or_backup_settings_is_not_reported_as_secure(self) -> None:
        """Cloud SQL requires neither TLS nor backups unless configured."""
        db = self._ingest(
            "google_sql_database_instance",
            "pg",
            {"name": "pg", "database_version": "POSTGRES_15", "settings": [{"tier": "db-custom-4-16384"}]},
            "databases",
        )
        self.assertIs(db["require_ssl"], False)
        self.assertIs(db["backup_enabled"], False)

    def test_cloudsql_ssl_mode_is_honoured(self) -> None:
        """``ssl_mode`` supersedes the deprecated ``require_ssl`` attribute.

        A config that enforces TLS through the modern attribute must not be
        reported as a deficiency simply because the old attribute is missing.
        """
        db = self._ingest(
            "google_sql_database_instance",
            "pg",
            {
                "name": "pg",
                "database_version": "POSTGRES_15",
                "settings": [{"ip_configuration": [{"ssl_mode": "ENCRYPTED_ONLY"}]}],
            },
            "databases",
        )
        self.assertIs(db["require_ssl"], True)

    def test_gke_without_private_config_is_public(self) -> None:
        """A cluster with no private_cluster_config is public on both counts."""
        cluster = self._ingest(
            "google_container_cluster",
            "c",
            {"name": "c", "location": "us-east4"},
            "gke_clusters",
        )
        self.assertIs(cluster["private_cluster"], False)
        self.assertIs(cluster["private_endpoint"], False)


class TestTextAttrTristate(unittest.TestCase):
    """Covers the degraded text-scan reader used when no HCL AST is available."""

    def test_absent_attribute_is_undetermined(self) -> None:
        """Silence must read as unknown, never as a value."""
        self.assertIsNone(_text_attr_tristate("resource {}", "versioning"))

    def test_explicit_values_are_read(self) -> None:
        """Explicit assignments are read in both directions."""
        self.assertIs(_text_attr_tristate("versioning = true", "versioning"), True)
        self.assertIs(_text_attr_tristate("versioning = false", "versioning"), False)

    def test_unrelated_false_does_not_leak(self) -> None:
        """A false elsewhere in the body must not flip an unrelated attribute.

        The previous heuristic tested the whole resource body for the substring
        'false', so one unrelated disabled flag silently disabled every other
        attribute it checked.
        """
        body = "deletion_protection = false\nuniform_bucket_level_access = true"
        self.assertIs(_text_attr_tristate(body, "uniform_bucket_level_access"), True)

    def test_nested_enabled_block_is_read(self) -> None:
        """A block form such as ``versioning { enabled = true }`` is understood."""
        self.assertIs(_text_attr_tristate("versioning {\n  enabled = true\n}", "versioning"), True)


if __name__ == "__main__":
    unittest.main()
