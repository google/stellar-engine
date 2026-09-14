"""Regression tests pinning the corrected coverage / ATC assessment behaviour.

These tests exist because the validator's headline metrics are what an ISSM acts
on. Each test pins a specific defect that caused the engine to report a number
that was not true:

* the reconciliation denominator silently excluded KMS keys, firewall rules and
  subnets, so most of a small estate was invisible to the coverage metric;
* the FIPS matrix was only ever read in one rendition, so an asset documented in
  the other rendition was reported as undocumented;
* the SSP implementation status was inferred by substring, which always tripped
  on the *unchecked* "- [ ] Planned" box present in every control section;
* a control present in neither the SCTM nor the SSP was reported as "PARTIAL"
  and back-filled with the ATC catalog blurb, presenting a requirement as if it
  were evidence.

Tests deliberately assert in both directions: a genuinely unverifiable control
must stay unverified, and a genuinely documented asset must be reconciled.
"""

import os
import shutil
import sys
import tempfile
import unittest
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import validate_compliance_artifacts as vca


# An SSP control section rendered exactly as the engine's template emits it: the
# implementation status is a checkbox list inside a Markdown table cell, so every
# section contains the literal words "Planned" and "Not Applicable" whether or
# not those boxes are ticked.
_STATUS_ROW = (
    "| **Implementation Status (check all that apply)**:<br>"
    "- [{implemented}] Implemented<br>"
    "- [{partial}] Partially Implemented (Hybrid)<br>"
    "- [ ] Planned<br>"
    "- [{inherited}] Inherited<br>"
    "- [ ] Not Applicable |"
)


def _ssp_section(ctrl_id: str, narrative: str, implemented: str = " ",
                 partial: str = "x", inherited: str = "x") -> str:
    """Builds one SSP control section in the engine's real template shape.

    Args:
        ctrl_id: Control identifier used in the level-3 heading.
        narrative: Implementation narrative body text.
        implemented: Checkbox mark for the "Implemented" status.
        partial: Checkbox mark for the "Partially Implemented" status.
        inherited: Checkbox mark for the "Inherited" status.

    Returns:
        The Markdown for a single control section, heading included.
    """
    status = _STATUS_ROW.format(implemented=implemented, partial=partial, inherited=inherited)
    return f"### {ctrl_id} Control Title\n\n{narrative}\n\n{status}\n\n"


class _PackageFixture:
    """Creates a throwaway ``ato_artifacts`` tree for a single test."""

    def __init__(self, root: str) -> None:
        """Records the workspace root that will hold ``ato_artifacts``.

        Args:
            root: Absolute path to the temporary workspace directory.
        """
        self.root = root
        self.ato_dir = os.path.join(root, "ato_artifacts")

    def write(self, relative_path: str, content: str) -> str:
        """Writes one deliverable into the package.

        Args:
            relative_path: Path relative to ``ato_artifacts``.
            content: File contents.

        Returns:
            The absolute path that was written.
        """
        full = os.path.join(self.ato_dir, relative_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(content)
        return full


class TestReconciliationCoverage(unittest.TestCase):
    """Pins the asset reconciliation denominator and matching sources."""

    def setUp(self) -> None:
        """Creates an isolated workspace for each test."""
        self.tmp = tempfile.mkdtemp(prefix="cov_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pkg = _PackageFixture(self.tmp)

    def _inventory(self) -> Dict[str, object]:
        """Returns an inventory matching the shape the extractor emits.

        Returns:
            An inventory with one bucket, VPC, subnet CIDR, firewall rule, KMS
            key and service account.
        """
        return {
            "infrastructure_components": {
                "storage_buckets": [{"name": "bkt-audit-logs-smoke"}],
                "kms_keys": [{"name": "key-bucket-cmek"}],
                "service_accounts": [{"account_id": "sa-pipeline"}],
            },
            "network_architecture": {
                "vpcs": ["vpc-hub"],
                # The extractor serialises this as a stringified Python set.
                "subnets_cidrs": "{'10.10.0.0/20'}",
                "firewall_rules": [{"name": "allow_internal"}],
            },
            "application_components": {},
        }

    def test_all_six_resource_classes_are_counted(self) -> None:
        """Every discovered resource class must appear in the denominator.

        Before this fix only buckets, VPCs and service accounts were counted, so
        a six-resource estate reported a denominator of three and the coverage
        percentage was computed over an unrepresentative subset.
        """
        self.pkg.write("SSP/SSP_System_Security_Plan.md", "vpc-hub sa-pipeline 10.10.0.0/20\n")
        self.pkg.write("PPSM/PPSM_Ports_Protocols_Services.yaml", "record: allow_internal\n")
        self.pkg.write("HW_SW_Inventory/Hardware_Software_Inventory.yaml", "nickname: key-bucket-cmek\n")
        self.pkg.write("FIPS_Cryptography/FIPS_Cryptographic_Matrix.md", "- **bkt-audit-logs-smoke**: us-central1\n")

        result = vca.audit_inventory_artifact_alignment(self.tmp, self._inventory(), self.pkg.ato_dir)

        self.assertEqual(result["total_discovered_assets"], 6, result["breakdown"])
        for category in ("storage", "vpcs", "subnets", "firewall_rules", "kms_keys", "service_accounts"):
            self.assertEqual(
                result["breakdown"][category]["discovered"], 1,
                f"{category} must contribute to the coverage denominator: {result['breakdown']}",
            )
        self.assertEqual(result["reconciled_assets_count"], 6)
        self.assertEqual(result["coverage_score_percent"], 100.0)
        self.assertEqual(result["discrepancies"], [])

    def test_bucket_documented_only_in_fips_markdown_is_reconciled(self) -> None:
        """Per-asset CMEK evidence lives in the FIPS Markdown, not the YAML.

        The audit previously opened only ``FIPS_Cryptographic_Matrix.yaml``,
        which carries module-level metadata, so a bucket documented in the
        Markdown rendition was reported as undocumented.
        """
        self.pkg.write(
            "FIPS_Cryptography/FIPS_Cryptographic_Matrix.yaml",
            "cryptographic_modules:\n  - module_id: FIPS-01\n",
        )
        self.pkg.write(
            "FIPS_Cryptography/FIPS_Cryptographic_Matrix.md",
            "### Storage & Persistence CMEK Verification\n- **bkt-audit-logs-smoke**: CMEK Encrypted: `False`\n",
        )
        inventory = {
            "infrastructure_components": {"storage_buckets": [{"name": "bkt-audit-logs-smoke"}]},
            "network_architecture": {},
            "application_components": {},
        }

        result = vca.audit_inventory_artifact_alignment(self.tmp, inventory, self.pkg.ato_dir)

        self.assertEqual(result["breakdown"]["storage"], {"discovered": 1, "matched": 1})
        self.assertIn("Storage Bucket: bkt-audit-logs-smoke", result["matched_assets"])

    def test_undocumented_subnet_cidr_is_reported_not_hidden(self) -> None:
        """A CIDR absent from every deliverable must lower the coverage score."""
        self.pkg.write("SSP/SSP_System_Security_Plan.md", "no subnet ranges recorded here\n")
        inventory = {
            "infrastructure_components": {},
            "network_architecture": {"subnets_cidrs": "{'10.10.0.0/20'}"},
            "application_components": {},
        }

        result = vca.audit_inventory_artifact_alignment(self.tmp, inventory, self.pkg.ato_dir)

        self.assertEqual(result["breakdown"]["subnets"], {"discovered": 1, "matched": 0})
        self.assertEqual(result["coverage_score_percent"], 0.0)
        self.assertTrue(
            any("10.10.0.0/20" in d for d in result["discrepancies"]),
            result["discrepancies"],
        )

    def test_unparseable_subnet_value_fails_closed(self) -> None:
        """A populated but unparseable subnet field must not shrink the denominator.

        Dropping it would raise the coverage percentage by removing an asset
        whose documentation status is genuinely unknown.
        """
        self.pkg.write("SSP/SSP_System_Security_Plan.md", "irrelevant\n")
        inventory = {
            "infrastructure_components": {},
            "network_architecture": {"subnets_cidrs": "set()"},
            "application_components": {},
        }

        result = vca.audit_inventory_artifact_alignment(self.tmp, inventory, self.pkg.ato_dir)

        self.assertEqual(result["breakdown"]["subnets"], {"discovered": 1, "matched": 0})
        self.assertTrue(
            any("NOT DETERMINED FROM SOURCE" in d for d in result["discrepancies"]),
            result["discrepancies"],
        )

    def test_empty_subnet_field_adds_nothing(self) -> None:
        """An absent subnet field must not invent an asset to reconcile."""
        inventory = {
            "infrastructure_components": {},
            "network_architecture": {"subnets_cidrs": ""},
            "application_components": {},
        }

        result = vca.audit_inventory_artifact_alignment(self.tmp, inventory, self.pkg.ato_dir)

        self.assertEqual(result["breakdown"]["subnets"], {"discovered": 0, "matched": 0})

    def test_deliverable_renditions_are_all_read(self) -> None:
        """Both renditions of a deliverable contribute to the searched text."""
        self.pkg.write("SSP/SSP_System_Security_Plan.md", "MARKDOWN-ONLY-TOKEN\n")
        self.pkg.write("SSP/SSP_System_Security_Plan.yaml", "YAML-ONLY-TOKEN\n")

        text = vca._read_deliverable_renditions(self.pkg.ato_dir, "SSP", ["SSP_System_Security_Plan"])

        self.assertIn("markdown-only-token", text)
        self.assertIn("yaml-only-token", text)

    def test_missing_deliverable_returns_empty_string(self) -> None:
        """An absent deliverable degrades to empty text rather than raising."""
        self.assertEqual(vca._read_deliverable_renditions(self.pkg.ato_dir, "SSP", ["Nope"]), "")


class TestSspControlSectionParsing(unittest.TestCase):
    """Pins the SSP section extractor and implementation-status parser."""

    def test_base_control_does_not_capture_enhancement_section(self) -> None:
        """Asking for AC-17 must not return the AC-17(2) narrative.

        The previous substring search for ``"### AC-17"`` matched the heading of
        the enhancement, attributing another control's evidence to the base
        control.
        """
        ssp = _ssp_section("AC-17(2)", "ENHANCEMENT NARRATIVE") + _ssp_section("AC-17", "BASE NARRATIVE")

        base = vca._extract_ssp_control_section(ssp, "AC-17")
        enhancement = vca._extract_ssp_control_section(ssp, "AC-17(2)")

        self.assertIn("BASE NARRATIVE", base)
        self.assertNotIn("ENHANCEMENT NARRATIVE", base)
        self.assertIn("ENHANCEMENT NARRATIVE", enhancement)

    def test_absent_control_yields_empty_section(self) -> None:
        """A control with no section must return empty, never a neighbour's text."""
        ssp = _ssp_section("SC-7", "BOUNDARY NARRATIVE")

        self.assertEqual(vca._extract_ssp_control_section(ssp, "IA-2(3)"), "")

    def test_unchecked_planned_box_is_not_a_status(self) -> None:
        """The unchecked "Planned" box must not be read as a Planned status."""
        section = _ssp_section("SC-8", "narrative", implemented="x", partial=" ", inherited=" ")

        checked, unchecked = vca._parse_ssp_implementation_status(section)

        self.assertIn("implemented", checked)
        self.assertIn("planned", unchecked)
        self.assertNotIn("planned", checked)

    def test_partially_implemented_is_reported_as_checked(self) -> None:
        """The template's default status is Partially Implemented plus Inherited."""
        checked, _ = vca._parse_ssp_implementation_status(_ssp_section("SC-8", "narrative"))

        self.assertIn("partially implemented (hybrid)", checked)
        self.assertIn("inherited", checked)
        self.assertNotIn("implemented", checked)

    def test_section_without_status_block_yields_nothing(self) -> None:
        """A section with no checkbox list must report an undetermined status."""
        checked, unchecked = vca._parse_ssp_implementation_status("### SC-8\nNarrative only.\n")

        self.assertEqual(checked, frozenset())
        self.assertEqual(unchecked, frozenset())


class TestAtcVerification(unittest.TestCase):
    """Pins the 14 ATC connection control verdicts."""

    def setUp(self) -> None:
        """Creates an isolated workspace for each test."""
        self.tmp = tempfile.mkdtemp(prefix="atc_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pkg = _PackageFixture(self.tmp)

    def _audit(self) -> Dict[str, object]:
        """Runs the senior compliance audit against the fixture package.

        Returns:
            The audit result dictionary.
        """
        return vca.audit_senior_compliance_quality(
            target_dir=self.tmp,
            inventory={},
            ato_dir=self.pkg.ato_dir,
            alignment_res={"discrepancies": []},
            excel_results=[],
            docx_results=[],
            oscal_results=[],
            unresolved_tokens=[],
            config_required_vars=[],
            stigs_required=[],
            rmf_action_items=[],
        )

    def _record(self, result: Dict[str, object], ctrl_id: str) -> Dict[str, str]:
        """Returns the ATC record for one control.

        Args:
            result: Audit result dictionary.
            ctrl_id: Control identifier to look up.

        Returns:
            The matching ATC verification record.

        Raises:
            AssertionError: If the control is missing from the records.
        """
        records: List[Dict[str, str]] = result["atc_records"]  # type: ignore[assignment]
        for record in records:
            if record["id"] == ctrl_id:
                return record
        raise AssertionError(f"{ctrl_id} absent from atc_records")

    def test_control_absent_everywhere_reports_missing_not_partial(self) -> None:
        """A control documented nowhere must not be dressed up as PARTIAL.

        It previously inherited the ATC catalog description as its
        "Implementation Evidence", which presents a requirement as evidence.
        """
        self.pkg.write("SSP/SSP_System_Security_Plan.md", _ssp_section("SC-7", "boundary firewall narrative"))

        record = self._record(self._audit(), "IA-2(3)")

        self.assertEqual(record["verification"], "MISSING")
        self.assertEqual(record["evidence_source"], "None")
        self.assertIn("NOT DETERMINED FROM SOURCE", record["details"])
        self.assertNotIn("Enforces hardware MFA", record["details"])

    def test_absent_controls_raise_a_cat_two_finding(self) -> None:
        """Undocumented mandatory ATC controls must surface as a finding."""
        self.pkg.write("SSP/SSP_System_Security_Plan.md", "no control sections at all\n")

        result = self._audit()

        atc_findings = [f for f in result["cat_2_findings"] if f["id"] == "CAT2-ATC-001"]  # type: ignore[index]
        self.assertEqual(len(atc_findings), 1, result["cat_2_findings"])
        self.assertIn("IA-2(3)", atc_findings[0]["description"])
        self.assertIn("14", atc_findings[0]["description"])

    def test_partially_implemented_ssp_control_is_not_verified(self) -> None:
        """A Partially Implemented control must never count towards the 14.

        This is the anti-inflation guard: fixing the unchecked-"Planned" bug
        must not turn every SSP-documented control into a verified one.
        """
        self.pkg.write(
            "SSP/SSP_System_Security_Plan.md",
            _ssp_section(
                "IA-2(1)",
                "Hardware token MFA (CAC/PIV FIDO2) is enforced for privileged network access "
                "through the enterprise identity provider.",
            ),
        )

        result = self._audit()
        record = self._record(result, "IA-2(1)")

        self.assertEqual(record["verification"], "PARTIAL")
        self.assertIn("partially implemented", record["status"].lower())
        self.assertNotIn("IA-2(1)", str(result["verified_atc_count"]))

    def test_fully_implemented_ssp_control_is_verified(self) -> None:
        """A genuinely Implemented, tailored, substantive control must verify.

        Without this the unchecked-"Planned" fix would be untested in the
        positive direction and the SSP evidence path could silently stay dead.
        """
        self.pkg.write(
            "SSP/SSP_System_Security_Plan.md",
            _ssp_section(
                "IA-2(1)",
                "Hardware token MFA (CAC/PIV FIDO2) is enforced for all privileged network "
                "access through the enterprise identity provider and Cloud Identity.",
                implemented="x",
                partial=" ",
                inherited=" ",
            ),
        )

        result = self._audit()
        record = self._record(result, "IA-2(1)")

        self.assertEqual(record["verification"], "VERIFIED")
        self.assertEqual(record["evidence_source"], "SSP")
        self.assertGreaterEqual(int(result["verified_atc_count"]), 1)  # type: ignore[arg-type]

    def test_untailored_assignment_parameters_block_verification(self) -> None:
        """An untailored NIST catalog statement is not an implementation claim."""
        self.pkg.write(
            "SSP/SSP_System_Security_Plan.md",
            _ssp_section(
                "IR-9",
                "Respond to information spills by assigning [Assignment: organization-defined "
                "personnel or roles] responsibility for spillage containment and sanitization.",
                implemented="x",
                partial=" ",
                inherited=" ",
            ),
        )

        record = self._record(self._audit(), "IR-9")

        self.assertEqual(record["verification"], "PARTIAL")
        self.assertIn("untailored", record["status"].lower())

    def test_every_record_carries_an_evidence_source(self) -> None:
        """The report must be able to name where each verdict came from."""
        self.pkg.write("SSP/SSP_System_Security_Plan.md", _ssp_section("SC-7", "boundary narrative"))

        records: List[Dict[str, str]] = self._audit()["atc_records"]  # type: ignore[assignment]

        self.assertEqual(len(records), 14)
        for record in records:
            self.assertIn(record["evidence_source"], {"SCTM", "SSP", "None"}, record)
            self.assertIn(record["verification"], {"VERIFIED", "PARTIAL", "MISSING"}, record)


if __name__ == "__main__":
    unittest.main()
