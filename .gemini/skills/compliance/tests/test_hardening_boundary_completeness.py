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

"""Regression tests for authorization boundary completeness.

A Terraform blueprint that the HCL parser cannot read is the most dangerous
class of discovery failure, because it is invisible. The parse error is logged,
the run exits zero, and every project, network, service account, key and
firewall rule declared in that file is simply absent from the System Security
Plan, the SCTM and the architecture reconciliation. Nothing in the delivered
package indicates that part of the boundary was never read, so an Authorizing
Official sees a package that reads as assessed-and-complete.

This was observed on a real 269-file DoD IL5 estate: one module used a comment
between a ternary's condition and its ``?``, which is valid Terraform that the
``bc-python-hcl2`` grammar rejects. Every resource in that module vanished.

Two properties are asserted here:

1. The extractor **records** unreadable blueprints rather than only logging them.
2. The POA&M engine **converts** each record into a CA-2 / RA-5 assessment
   coverage gap carrying every field the Excel hydrator indexes -- a missing
   field aborts the whole package generation, so the schema is load-bearing.
"""

import os
import sys
import tempfile
import unittest
from typing import Any, Dict, List

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
sys.path.insert(0, SCRIPTS_DIR)

import extract_system_data  # noqa: E402
import file_helpers  # noqa: E402,F401  bootstraps dependencies onto sys.path
import poam_rules  # noqa: E402

#: Every key the POA&M Excel sheet indexes with ``item[...]`` rather than
#: ``item.get(...)``. Omitting any one of these raises KeyError and destroys all
#: 71 deliverables, so new POA&M producers must satisfy this contract exactly.
REQUIRED_POAM_FIELDS = (
    "control", "item_id", "desc", "aps", "checks", "status", "sched_date",
    "milestone_id", "milestone_desc", "milestone_status", "source", "severity",
    "threat", "likelihood", "impact", "residual",
)

#: Reproduces the real failure: valid Terraform whose comment placement the
#: vendored HCL grammar rejects.
UNPARSEABLE_BLUEPRINT_ERROR = (
    "Unexpected token Token('_NEW_LINE_OR_COMMENT', "
    "'# default scopes for Compute default SA\\n') at line 58, column 9."
)


def _inventory_with_unparsed(paths: List[str]) -> Dict[str, Any]:
    """Build a minimal inventory carrying unparsed blueprint records.

    Args:
        paths: Repository-relative paths of blueprints that failed to parse.

    Returns:
        An inventory dictionary shaped like ``system_inventory.json``.
    """
    return {
        "system_information": {
            "system_abbreviation": "C2T",
            "effective_date": "2026-08-24",
        },
        "infrastructure_components": {
            "unparsed_terraform_files": [
                {"path": p, "error": UNPARSEABLE_BLUEPRINT_ERROR} for p in paths
            ],
        },
    }


class TestUnparsedBlueprintsBecomeCoverageGaps(unittest.TestCase):
    """An unreadable blueprint must surface in the POA&M, not just the log."""

    def _derive(self, inventory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Derive POA&M findings with live scanners disabled.

        Args:
            inventory: The inventory to derive from.

        Returns:
            The derived POA&M items.
        """
        return poam_rules.derive_poam_findings(inventory, run_scanners=False)

    def test_unparsed_blueprint_produces_a_poam_item(self) -> None:
        """The gap is reported, not swallowed."""
        items = self._derive(_inventory_with_unparsed([
            "infrastructure/terraform/modules/fabric/compute-vm/main.tf",
        ]))
        matching = [
            i for i in items
            if "compute-vm/main.tf" in str(i.get("title", ""))
        ]
        self.assertEqual(
            1, len(matching),
            "An unreadable Terraform blueprint produced no POA&M item. Its "
            "resources are missing from the boundary and the package says "
            f"nothing about it. Derived items: {[i.get('title') for i in items]}",
        )

    def test_gap_is_attributed_to_assessment_controls(self) -> None:
        """A discovery gap is an assessment failure, not an infrastructure defect."""
        items = self._derive(_inventory_with_unparsed(["infra/main.tf"]))
        gap = next(i for i in items if "infra/main.tf" in str(i.get("title", "")))
        self.assertIn("CA-02", str(gap.get("aps")))
        self.assertIn("RA-05", str(gap.get("aps")))
        self.assertNotIn(
            "SA-11", str(gap.get("aps")),
            "A boundary discovery gap must not be filed as a code-quality finding.",
        )

    def test_gap_carries_every_field_the_excel_sheet_indexes(self) -> None:
        """A missing field aborts generation of the entire package."""
        items = self._derive(_inventory_with_unparsed(["infra/main.tf"]))
        gap = next(i for i in items if "infra/main.tf" in str(i.get("title", "")))
        missing = [field for field in REQUIRED_POAM_FIELDS if field not in gap]
        self.assertEqual(
            [], missing,
            "The POA&M Excel sheet indexes these fields directly, so their "
            f"absence raises KeyError and destroys all deliverables: {missing}",
        )

    def test_every_derived_item_satisfies_the_excel_contract(self) -> None:
        """Guards every producer, not only the one under test."""
        items = self._derive(_inventory_with_unparsed(["a/main.tf", "b/main.tf"]))
        for item in items:
            missing = [field for field in REQUIRED_POAM_FIELDS if field not in item]
            self.assertEqual(
                [], missing,
                f"POA&M item {item.get('item_id')} "
                f"({str(item.get('title'))[:60]}) omits {missing}.",
            )

    def test_each_unreadable_file_is_reported_separately(self) -> None:
        """Consolidation must not collapse distinct files into one finding."""
        items = self._derive(_inventory_with_unparsed([
            "infra/alpha/main.tf",
            "infra/beta/main.tf",
        ]))
        reported = {
            path for path in ("infra/alpha/main.tf", "infra/beta/main.tf")
            if any(path in str(i.get("title", "")) for i in items)
        }
        self.assertEqual(
            {"infra/alpha/main.tf", "infra/beta/main.tf"}, reported,
            "Distinct unreadable blueprints were merged, hiding one of them.",
        )

    def test_diagnostic_is_preserved_for_the_assessor(self) -> None:
        """The finding must say why the file could not be read."""
        items = self._derive(_inventory_with_unparsed(["infra/main.tf"]))
        gap = next(i for i in items if "infra/main.tf" in str(i.get("title", "")))
        self.assertIn("Parser diagnostic:", str(gap.get("desc")))
        self.assertIn("line 58", str(gap.get("desc")))

    def test_clean_estate_produces_no_boundary_gap(self) -> None:
        """No unparsed files means no finding: zero synthetic filler."""
        inventory = _inventory_with_unparsed([])
        items = poam_rules.derive_poam_findings(inventory, run_scanners=False)
        spurious = [
            i for i in items
            if "could not be parsed" in str(i.get("title", ""))
        ]
        self.assertEqual(
            [], spurious,
            "A fully parseable estate must not produce a boundary coverage gap.",
        )

    def test_malformed_ledger_entries_are_skipped(self) -> None:
        """A corrupt record must not abort the package."""
        inventory = _inventory_with_unparsed([])
        inventory["infrastructure_components"]["unparsed_terraform_files"] = [
            None,
            "not-a-dict",
            {"error": "no path recorded"},
            {"path": "   "},
            {"path": "infra/real.tf", "error": "genuine failure"},
        ]
        items = poam_rules.derive_poam_findings(inventory, run_scanners=False)
        gaps = [i for i in items if "could not be parsed" in str(i.get("title", ""))]
        self.assertEqual(
            1, len(gaps),
            "Only the well-formed record should yield a finding; malformed "
            "entries must be skipped rather than crashing or inventing items.",
        )
        self.assertIn("infra/real.tf", str(gaps[0].get("title")))

    def test_config_flag_can_disable_boundary_gap_poam_items(self) -> None:
        """When include_unparsed_blueprints_in_poam is False, unparsed records do not pollute the POA&M."""
        inventory = _inventory_with_unparsed(["infra/broken.tf"])
        inventory["compliance_config"] = {"include_unparsed_blueprints_in_poam": False}
        items = poam_rules.derive_poam_findings(inventory, run_scanners=False)
        gaps = [i for i in items if "could not be parsed" in str(i.get("title", ""))]
        self.assertEqual(
            0, len(gaps),
            "Setting include_unparsed_blueprints_in_poam to False must omit AST parse gaps from POA&M.",
        )

    def test_auxiliary_and_recovered_files_do_not_populate_unparsed_ledger(self) -> None:
        """Auxiliary files without resources and files whose resources are recovered must not be marked unparsed."""
        with tempfile.TemporaryDirectory() as td:
            # 1. Auxiliary file without resources
            with open(os.path.join(td, "outputs.tf"), "w") as f:
                f.write('output "sample" { value = [for x in var.items: x] }\n')

            # 2. File with complex HCL expression where fallback regex extracts resource
            with open(os.path.join(td, "main.tf"), "w") as f:
                f.write(
                    'resource "google_storage_bucket" "b" {\n'
                    '  name = "clean-test-bucket"\n'
                    '  labels = { for k, v in var.tags : k => v }\n'
                    '}\n'
                )

            # 3. Genuinely broken file with unclosed brace
            with open(os.path.join(td, "broken.tf"), "w") as f:
                f.write('resource "google_compute_instance" "vm" {\n  unclosed block')

            scanned = extract_system_data.deep_scan_tf_files(td)
            unparsed = [u["path"] for u in scanned.get("unparsed_terraform_files", [])]

            self.assertNotIn("outputs.tf", unparsed, "Auxiliary files must not enter unparsed ledger")
            self.assertNotIn("main.tf", unparsed, "Recovered resource files must not enter unparsed ledger")
            self.assertIn("broken.tf", unparsed, "Genuinely unrecoverable broken files must enter unparsed ledger")


if __name__ == "__main__":
    unittest.main()
