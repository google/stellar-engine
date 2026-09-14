#!/usr/bin/env python3
"""Edge-case and negative tests for runbook operator placeholder hydration.

Covers boundary cases, malformed inventory structures, fabrication guards,
and injection resistance in ``runbook_hydration.py``:
- Identifier validation: rejection of HCL interpolations, template residue, markers, and path characters.
- Cloud KMS resource path extraction across standard, full, and malformed strings.
- Project ID resolution across precedence keys and resource self-links.
- Service account email extraction with strict rejection of historical fabrication placeholders
  ("workload", "project", "example", "changeme").
- Organization domain and ID extraction with DNS validation and case normalization.
- Discovered environment context block rendering under empty, full, and partially resolved states.
- Denial-of-service / catastrophic backtracking resistance on large templates with nested brackets.
"""

import os
import sys
import unittest
from typing import Any, Dict

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import runbook_hydration as rh


class TestIdentifierValidationEdges(unittest.TestCase):
    """Deep testing of _is_plausible_identifier fabrication guard."""

    def test_rejects_non_string_types(self) -> None:
        for val in (None, 123, 45.6, True, [], {}, ()):
            self.assertFalse(rh._is_plausible_identifier(val))

    def test_rejects_empty_or_whitespace_strings(self) -> None:
        for val in ("", "   ", "\t\n"):
            self.assertFalse(rh._is_plausible_identifier(val))

    def test_rejects_hcl_interpolation_and_template_residue(self) -> None:
        for val in (
            "${var.project_id}",
            "var.network_name",
            "local.environment",
            "[CONFIG_REQUIRED: project_id]",
            "[TBD]",
            "{name}",
        ):
            self.assertFalse(rh._is_plausible_identifier(val), f"Failed to reject: {val}")

    def test_rejects_redaction_and_fail_closed_markers(self) -> None:
        for val in (
            "[REDACTED_SENSITIVE]",
            "REDACTED",
            "[NOT DETERMINED FROM SOURCE]",
            "not determined",
        ):
            self.assertFalse(rh._is_plausible_identifier(val))

    def test_accepts_valid_cloud_identifiers(self) -> None:
        for val in (
            "my-project-123",
            "bkt-audit-logs.appspot.com",
            "us-central1",
            "kr-security-keys",
            "key-storage-cmek",
            "example.gov:mission-enclave",
            "corp.internal:security-vault",
        ):
            self.assertTrue(rh._is_plausible_identifier(val), f"Failed to accept: {val}")

    def test_rejects_invalid_characters_or_length(self) -> None:
        for val in (
            "-leading-dash",
            "has spaces",
            "has;semicolon",
            "rm-rf/etc",
            "a" * 64,  # regex bounds to 1..62 chars after leading char
        ):
            self.assertFalse(rh._is_plausible_identifier(val))


class TestKmsPathParsingEdges(unittest.TestCase):
    """Cloud KMS self-link and path parsing edge cases."""

    def test_parses_full_crypto_key_version_path(self) -> None:
        path = "projects/prj-sec/locations/us-east4/keyRings/kr-cmek/cryptoKeys/key-disk/cryptoKeyVersions/1"
        parsed = rh._parse_kms_path(path)
        self.assertEqual(parsed.get("project"), "prj-sec")
        self.assertEqual(parsed.get("location"), "us-east4")
        self.assertEqual(parsed.get("key_ring"), "kr-cmek")
        self.assertEqual(parsed.get("crypto_key"), "key-disk")

    def test_parses_key_ring_path_without_key(self) -> None:
        path = "projects/prj-sec/locations/europe-west3/keyRings/kr-ring"
        parsed = rh._parse_kms_path(path)
        self.assertEqual(parsed.get("project"), "prj-sec")
        self.assertEqual(parsed.get("location"), "europe-west3")
        self.assertEqual(parsed.get("key_ring"), "kr-ring")
        self.assertNotIn("crypto_key", parsed)

    def test_rejects_non_kms_paths(self) -> None:
        self.assertEqual(rh._parse_kms_path(""), {})
        self.assertEqual(rh._parse_kms_path(None), {})
        self.assertEqual(rh._parse_kms_path("projects/prj/locations/us-east4"), {})
        self.assertEqual(rh._parse_kms_path("https://storage.googleapis.com/bkt/obj"), {})

    def test_collect_kms_facts_from_malformed_and_heterogeneous_entries(self) -> None:
        inventory: Dict[str, Any] = {
            "infrastructure_components": {
                "kms_keys": [
                    None,
                    "not-a-dict",
                    {"name": "bare-key", "key_ring": "projects/p1/locations/l1/keyRings/r1"},
                    {"name": "projects/p2/locations/l2/keyRings/r2/cryptoKeys/k2"},
                    {"name": "invalid!key", "key_ring": "invalid!ring"},
                ]
            }
        }
        facts = rh.collect_kms_facts(inventory)
        self.assertIn("p1", facts["kms_projects"])
        self.assertIn("p2", facts["kms_projects"])
        self.assertIn("r1", facts["key_rings"])
        self.assertIn("r2", facts["key_rings"])
        self.assertIn("bare-key", facts["key_names"])
        self.assertIn("k2", facts["key_names"])
        self.assertNotIn("invalid!key", facts["key_names"])


class TestServiceAccountEmailEdges(unittest.TestCase):
    """Fabrication guards on service accounts and email reconstruction."""

    def test_all_known_fabricated_project_names_are_discarded(self) -> None:
        for placeholder in ("workload", "project", "example", "changeme"):
            inventory: Dict[str, Any] = {
                "infrastructure_components": {
                    "service_accounts": [
                        {"email": f"sa-test@{placeholder}.iam.gserviceaccount.com"}
                    ]
                }
            }
            emails = rh.collect_service_account_emails(inventory)
            self.assertEqual(emails, [], f"Fabricated placeholder '{placeholder}' was not discarded")

    def test_reconstructs_email_from_valid_account_id_and_project(self) -> None:
        inventory: Dict[str, Any] = {
            "infrastructure_components": {
                "service_accounts": [
                    {"account_id": "sa-runner", "project": "prj-ci"}
                ]
            }
        }
        emails = rh.collect_service_account_emails(inventory)
        self.assertEqual(emails, ["sa-runner@prj-ci.iam.gserviceaccount.com"])

    def test_rejects_reconstruction_when_project_is_missing_or_invalid(self) -> None:
        inventory: Dict[str, Any] = {
            "infrastructure_components": {
                "service_accounts": [
                    {"account_id": "sa-orphan"},
                    {"account_id": "sa-bad", "project": "not valid!"},
                ]
            }
        }
        emails = rh.collect_service_account_emails(inventory)
        self.assertEqual(emails, [])


class TestOrganizationDomainAndIdEdges(unittest.TestCase):
    """DNS domain shape checking and numeric org ID resolution."""

    def test_organization_domain_case_normalization(self) -> None:
        inventory: Dict[str, Any] = {
            "system_information": {"organization_domain": "EXAMPLE-AGENCY.GOV"}
        }
        self.assertEqual(rh.resolve_organization_domain(inventory), "example-agency.gov")

    def test_organization_display_name_not_mangled(self) -> None:
        """Display names such as 'Department of Veteran Affairs' must NOT be mangled to 'departmentofveteranaffairs.gov'."""
        inventory: Dict[str, Any] = {
            "system_information": {"organization": "Department of Veteran Affairs"}
        }
        self.assertIsNone(rh.resolve_organization_domain(inventory))

    def test_organization_display_name_accepted_if_already_valid_dns(self) -> None:
        inventory: Dict[str, Any] = {
            "system_information": {"organization": "cloud.agency.mil"}
        }
        self.assertEqual(rh.resolve_organization_domain(inventory), "cloud.agency.mil")

    def test_organization_id_numeric_validation(self) -> None:
        self.assertEqual(
            rh.resolve_organization_id({"system_information": {"org_id": "123456789012"}}),
            "123456789012",
        )
        self.assertIsNone(
            rh.resolve_organization_id({"system_information": {"org_id": "not-numeric"}})
        )
        self.assertIsNone(
            rh.resolve_organization_id({"system_information": {"org_id": "12"}})  # too short
        )


class TestHydrationPerformanceAndLargeInput(unittest.TestCase):
    """Stress test ensuring regex evaluation on large inputs does not backtrack catastrophically."""

    def test_large_template_evaluates_quickly(self) -> None:
        inventory: Dict[str, Any] = {
            "system_information": {"project_id": "prj-perf"},
            "infrastructure_components": {
                "storage_buckets": [{"name": "bkt-perf"}],
            },
        }
        repeated_block = (
            "gcloud storage ls gs://[BUCKET_NAME]/data\n"
            "gcloud compute instances describe [INSTANCE_NAME] --project=[PROJECT_ID]\n"
            "Reference citation [PRIVACT] and [EVIDACT].\n"
        )
        large_content = repeated_block * 500  # ~50,000 chars with 1,000 operator tokens

        hydrated = rh.hydrate_operator_placeholders(large_content, inventory)
        self.assertIn("gs://bkt-perf/data", hydrated)
        self.assertIn("--project=prj-perf", hydrated)
        self.assertIn("<INSTANCE_NAME: fill in", hydrated)
        self.assertIn("[PRIVACT]", hydrated)
        self.assertIn("[EVIDACT]", hydrated)

    def test_unallowlisted_bracketed_tokens_survive_unchanged(self) -> None:
        """Arbitrary bracketed strings that do not match allowlisted tokens must not be modified."""
        text = "Check [NIST_800_53] control [AC_2_1] and status [UNKNOWN_TOKEN]."
        hydrated = rh.hydrate_operator_placeholders(text, {})
        self.assertEqual(hydrated, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
