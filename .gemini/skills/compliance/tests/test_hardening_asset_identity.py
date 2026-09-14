"""Hardening tests for asset identity and attribute fidelity on the HCL path.

Terraform declared in ``.tf`` files reaches the inventory through the structured
(AST dictionary) branch of :func:`classify_and_ingest_resource`. That branch is
the only one that can read nested blocks positionally, so it is the sole source
of exact CMEK key identity, per-NIC public-IP exposure, and boot-disk encryption
references.

These tests pin the three properties an accreditation package depends on:

* every resource declared in the boundary appears in the inventory, including
  the ones whose ``name`` is a Terraform expression rather than a literal;
* no asset identifier is ever emitted as raw expression syntax; and
* attribute values are concrete, not unresolved ``${var.*}`` references.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root / "scripts"))

from extract_system_data import (  # noqa: E402
    classify_and_ingest_resource,
    deep_scan_tf_files,
)

# A deliberately module-flavoured blueprint: names are expressions, encryption is
# declared in a nested block, and the machine type comes from a variable.
REPRESENTATIVE_TF = """
variable "bucket_suffix" {
  type    = string
  default = "evidence-archive"
}

variable "vm_size" {
  type    = string
  default = "n2-standard-16"
}

resource "google_storage_bucket" "audit" {
  name          = "${var.bucket_suffix}"
  location      = "US-EAST4"
  storage_class = "STANDARD"

  encryption {
    default_kms_key_name = "projects/acme/locations/us-east4/keyRings/core/cryptoKeys/audit-key"
  }

  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "spillover" {
  name     = "${each.value.bucket}"
  location = "US-EAST4"
}

resource "google_compute_instance" "worker" {
  name         = "${var.bucket_suffix}-worker"
  machine_type = var.vm_size
  zone         = "us-east4-a"

  network_interface {
    subnetwork = "workload-subnet"

    access_config {
    }
  }
}
"""

EXPECTED_KMS_KEY = (
    "projects/acme/locations/us-east4/keyRings/core/cryptoKeys/audit-key"
)

# Fields that carry an asset identifier into the SSP, SCTM and HW/SW inventory.
IDENTIFIER_FIELDS = ("name", "account_id", "service_account", "resource_name")

EXPRESSION_MARKERS = ("${", "var.", "each.", "local.")


class TestAssetIdentityOnTheHclPath(unittest.TestCase):
    """Verifies fidelity of names and attributes extracted from .tf sources."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        target = Path(cls._tmp.name)
        (target / "main.tf").write_text(REPRESENTATIVE_TF, encoding="utf-8")
        cls.tf_data: Dict[str, Any] = deep_scan_tf_files(str(target))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _buckets_by_name(self) -> Dict[str, Dict[str, Any]]:
        return {b["name"]: b for b in self.tf_data["storage_buckets"]}

    def test_cmek_key_identity_is_preserved_not_reduced_to_a_boolean(self) -> None:
        """The exact KMS key path must survive into the inventory.

        SC-12 and SC-28 evidence has to name the key protecting the data, and the
        FIPS 140-3 matrix keys off the crypto key resource. Reporting only that
        *some* key is configured is not an auditable assertion.
        """
        bucket = self._buckets_by_name().get("evidence-archive")
        self.assertIsNotNone(
            bucket, "bucket with an interpolated name must be inventoried"
        )
        assert bucket is not None
        self.assertEqual(
            bucket["kms_key"],
            EXPECTED_KMS_KEY,
            "nested encryption block must yield the key path, not a flag",
        )
        self.assertTrue(bucket["cmek_encrypted"])

    def test_resources_named_by_an_expression_are_still_inventoried(self) -> None:
        """A resource must never be dropped because its name is an expression.

        Every resource declared inside a reusable module is named from a
        variable. Skipping those silently shrinks the accreditation boundary,
        which is the most dangerous possible failure mode for this tool.
        """
        self.assertEqual(
            len(self.tf_data["storage_buckets"]),
            2,
            "both buckets are in the boundary regardless of how they are named",
        )

    def test_unresolvable_name_degrades_to_the_terraform_logical_name(self) -> None:
        """``${each.value.bucket}`` has no static value, so fall back readably."""
        self.assertIn(
            "spillover",
            self._buckets_by_name(),
            "an unresolvable name must degrade to the logical resource name",
        )

    def test_no_asset_identifier_contains_expression_syntax(self) -> None:
        """No emitted identifier may contain ``${``, ``var.``, ``each.`` or ``local.``.

        These strings are copied verbatim into deliverables, so an unresolved
        expression surfaces to an assessor as a malformed asset name and trips
        the validator's unresolved-token check.
        """
        offenders = []
        for category, items in self.tf_data.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                for field in IDENTIFIER_FIELDS:
                    value = item.get(field)
                    if not isinstance(value, str):
                        continue
                    if any(marker in value for marker in EXPRESSION_MARKERS):
                        offenders.append(f"{category}.{field}={value!r}")
        self.assertEqual(offenders, [], f"unresolved identifiers emitted: {offenders}")

    def test_scalar_attributes_are_resolved_against_declared_variables(self) -> None:
        """``machine_type = var.vm_size`` must arrive as the concrete size.

        The hardware inventory records machine types; an unresolved reference
        makes the sizing column useless and breaks downstream cost and boundary
        reporting.
        """
        vms = {v["name"]: v for v in self.tf_data["compute_instances"]}
        self.assertEqual(len(vms), 1)
        vm = next(iter(vms.values()))
        self.assertEqual(vm["machine_type"], "n2-standard-16")

    def test_public_ip_exposure_uses_the_key_the_poam_rules_read(self) -> None:
        """Exposure must be reported under ``has_public_ip``.

        ``poam_rules`` raises its internet-exposed-instance finding by testing
        ``vm.get("has_public_ip") is True``. Emitting the flag under any other
        key silently disarms that rule, so a publicly reachable VM would never
        reach the POA&M.
        """
        vm = self.tf_data["compute_instances"][0]
        self.assertIn(
            "has_public_ip",
            vm,
            "compute records must use the field name poam_rules evaluates",
        )
        self.assertIs(
            vm["has_public_ip"],
            True,
            "a network_interface with access_config is internet-exposed",
        )


class TestStructuredBranchIsReachable(unittest.TestCase):
    """Guards the dispatch contract that makes the structured branch usable."""

    def test_dict_bodies_take_the_structured_branch(self) -> None:
        """A mapping body must be read structurally, not as text.

        A previous revision wrapped the parsed AST in a ``str`` subclass, so the
        ``isinstance(body, dict)`` gate never matched and fully parsed Terraform
        was silently downgraded to substring heuristics. This pins the gate.
        """
        tf_data: Dict[str, Any] = {"all_resources": [], "storage_buckets": []}
        classify_and_ingest_resource(
            "google_storage_bucket",
            "audit",
            {
                "name": "audit-bucket",
                "encryption": [{"default_kms_key_name": EXPECTED_KMS_KEY}],
            },
            "main.tf",
            tf_data,
        )
        self.assertEqual(len(tf_data["storage_buckets"]), 1)
        self.assertEqual(tf_data["storage_buckets"][0]["kms_key"], EXPECTED_KMS_KEY)


class TestFirewallAttributeShapes(unittest.TestCase):
    """Firewall attributes must tolerate the shapes Terraform actually yields."""

    def _ingest(self, allow_block: Dict[str, Any]) -> Dict[str, Any]:
        tf_data: Dict[str, Any] = {"all_resources": [], "firewall_rules": []}
        classify_and_ingest_resource(
            "google_compute_firewall",
            "allow-db",
            {"name": "allow-db", "network": "core-vpc", "allow": [allow_block]},
            "main.tf",
            tf_data,
        )
        self.assertEqual(len(tf_data["firewall_rules"]), 1)
        return tf_data["firewall_rules"][0]

    def test_scalar_port_value_does_not_abort_extraction(self) -> None:
        """``ports = var.allowed_ports`` can resolve to a bare scalar.

        A single-element variable default such as ``[5432]`` is stored unwrapped,
        so the attribute arrives as an int. Iterating it raised ``TypeError`` and
        aborted the whole blueprint, losing every remaining resource in the
        boundary rather than degrading on one field.
        """
        rule = self._ingest({"protocol": "tcp", "ports": 5432})
        self.assertEqual(rule["ports"], "5432")
        self.assertEqual(rule["protocol"], "tcp")

    def test_list_port_values_are_still_joined(self) -> None:
        """The ordinary list shape must keep working."""
        rule = self._ingest({"protocol": "tcp", "ports": [5432, "443"]})
        self.assertEqual(rule["ports"], "5432,443")

    def test_list_valued_protocol_is_flattened(self) -> None:
        """A protocol wrapped in a list must not break the join."""
        rule = self._ingest({"protocol": ["tcp"], "ports": ["443"]})
        self.assertEqual(rule["protocol"], "tcp")


if __name__ == "__main__":
    unittest.main()
