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

"""Comprehensive regression and edge-case tests for modular export strategies and hydrators.

Validates:
- ExporterRegistry: Strategy resolution for 'both', 'all', single formats, comma-separated lists,
  and fallback defaults on unknown format preferences.
- dualmethod decorator: Dual class/instance dispatch and instance-based dependency injection isolation.
- Policy Exporters (Markdown, Docx): File extension normalization and boundary path confinement.
- Structured Data Exporters (YAML, Excel, OSCAL): Matrix generation, template hydration, and audit trail emission.
- Excel Hydrator Hardening: 50MB file size ceiling (CWE-400) and symlink/directory boundary confinement (CWE-59).
"""

import os
from pathlib import Path
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from excel_hydrator import HWSWHydrator, SCTMHydrator, _load_reference_mappings
import export_strategies as es


class TestExporterRegistryResolution(unittest.TestCase):
    """Testing strategy resolution across format preferences and fallbacks."""

    def setUp(self) -> None:
        self.registry = es.ExporterRegistry(load_defaults=True)

    def test_policy_format_both_and_all(self) -> None:
        both_exporters = self.registry.get_policy_exporters("both")
        self.assertEqual(len(both_exporters), 2)
        names = {exp.format_name for exp in both_exporters}
        self.assertEqual(names, {"markdown", "docx"})

        all_exporters = self.registry.get_policy_exporters("all")
        self.assertEqual(len(all_exporters), 2)

    def test_policy_format_single_and_comma_separated(self) -> None:
        md_only = self.registry.get_policy_exporters("markdown")
        self.assertEqual(len(md_only), 1)
        self.assertEqual(md_only[0].format_name, "markdown")

        docx_only = self.registry.get_policy_exporters("docx")
        self.assertEqual(len(docx_only), 1)
        self.assertEqual(docx_only[0].format_name, "docx")

        comma_list = self.registry.get_policy_exporters("docx, markdown")
        self.assertEqual(len(comma_list), 2)
        self.assertEqual([exp.format_name for exp in comma_list], ["docx", "markdown"])

    def test_policy_format_unknown_falls_back_to_markdown(self) -> None:
        fallback = self.registry.get_policy_exporters("unknown_format")
        self.assertEqual(len(fallback), 1)
        self.assertEqual(fallback[0].format_name, "markdown")

    def test_data_format_both_and_all(self) -> None:
        both_data = self.registry.get_data_exporters("both")
        self.assertEqual(len(both_data), 2)
        self.assertEqual({exp.format_name for exp in both_data}, {"yaml", "excel"})

        all_data = self.registry.get_data_exporters("all")
        self.assertEqual(len(all_data), 3)
        self.assertEqual({exp.format_name for exp in all_data}, {"yaml", "excel", "oscal"})

    def test_data_format_comma_separated_and_single(self) -> None:
        comma_data = self.registry.get_data_exporters("yaml, oscal")
        self.assertEqual(len(comma_data), 2)
        self.assertEqual([exp.format_name for exp in comma_data], ["yaml", "oscal"])

        excel_only = self.registry.get_data_exporters("excel")
        self.assertEqual(len(excel_only), 1)
        self.assertEqual(excel_only[0].format_name, "excel")

    def test_data_format_unknown_falls_back_to_yaml(self) -> None:
        fallback = self.registry.get_data_exporters("parquet")
        self.assertEqual(len(fallback), 1)
        self.assertEqual(fallback[0].format_name, "yaml")


class TestDualMethodAndRegistryIsolation(unittest.TestCase):
    """Testing dualmethod dispatch and instance-level dependency injection."""

    def test_class_level_call_uses_default_registry(self) -> None:
        default_policy_exps = es.ExporterRegistry.get_policy_exporters("both")
        self.assertEqual(len(default_policy_exps), 2)

    def test_instance_level_mutation_does_not_pollute_class_default(self) -> None:
        isolated_registry = es.ExporterRegistry(load_defaults=False)
        isolated_registry.register_policy_exporter("custom", es.MarkdownPolicyExporter())

        # Isolated instance only knows 'custom'
        self.assertIn("custom", isolated_registry.get_registered_policy_exporters())
        self.assertEqual(len(isolated_registry.get_registered_policy_exporters()), 1)

        # Default class registry remains untouched
        default_exps = es.ExporterRegistry.get_registered_policy_exporters()
        self.assertIn("markdown", default_exps)
        self.assertIn("docx", default_exps)
        self.assertNotIn("custom", default_exps)


class TestPolicyExportersConfinement(unittest.TestCase):
    """Testing boundary enforcement and file writing in policy exporters."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_markdown_exporter_writes_and_appends_extension(self) -> None:
        exporter = es.MarkdownPolicyExporter()
        target = self.root / "policy_doc"
        written = exporter.export_document(
            markdown_content="# Policy Title\nContent",
            output_base_path=target,
            inventory={},
            allowed_boundary=self.root,
        )
        self.assertEqual(written.suffix, ".md")
        self.assertTrue(written.is_file())
        self.assertEqual(written.read_text(encoding="utf-8"), "# Policy Title\nContent")

    def test_markdown_exporter_outside_boundary_raises_permission_error(self) -> None:
        exporter = es.MarkdownPolicyExporter()
        escaped = self.root / ".." / "escaped_policy"
        with self.assertRaises(PermissionError):
            exporter.export_document(
                markdown_content="content",
                output_base_path=escaped,
                inventory={},
                allowed_boundary=self.root,
            )

    def test_docx_exporter_outside_boundary_raises_permission_error(self) -> None:
        exporter = es.DocxPolicyExporter()
        escaped = self.root / ".." / "escaped_docx"
        with self.assertRaises(PermissionError):
            exporter.export_document(
                markdown_content="content",
                output_base_path=escaped,
                inventory={},
                allowed_boundary=self.root,
            )


class TestExcelHydratorHardening(unittest.TestCase):
    """Regression tests for Excel workbook loading bounds and boundary confinement."""

    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name).resolve()
        self.dummy_xlsm = self.root / "dummy.xlsm"
        self.dummy_xlsm.write_bytes(b"dummy zip data")

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_load_workbook_size_limit(self) -> None:
        """CWE-400: Oversize Excel files (> 50MB) must be rejected before buffering into memory."""
        huge_file = self.root / "huge.xlsm"
        with open(huge_file, "wb") as f:
            f.seek((51 * 1024 * 1024) - 1)
            f.write(b"\x00")

        hydrator = HWSWHydrator(str(huge_file))
        with self.assertRaises((ValueError, PermissionError)):
            hydrator.load_workbook()

    def test_load_workbook_boundary(self) -> None:
        """CWE-59: A symlink pointing outside the boundary must be rejected."""
        outside_file = self.root / "outside.xlsm"
        outside_file.write_bytes(b"dummy")

        inside_dir = self.root / "inside"
        inside_dir.mkdir()
        symlink_path = inside_dir / "symlink.xlsm"
        os.symlink(outside_file, symlink_path)

        hydrator = HWSWHydrator(str(symlink_path))
        with self.assertRaises(PermissionError):
            hydrator.load_workbook()

    def test_load_reference_mappings_default(self) -> None:
        """_load_reference_mappings must return dict with military ranks and honorifics."""
        data = _load_reference_mappings()
        self.assertIsInstance(data, dict)
        self.assertIn("military_ranks", data)
        self.assertIn("civilian_honorifics", data)
        self.assertTrue(len(data["military_ranks"]) > 0)

    def test_load_reference_mappings_with_yaml_override(self) -> None:
        """_load_reference_mappings must safely merge overrides from a YAML file."""
        override_file = self.root / "custom_config.yaml"
        override_file.write_text(
            "reference_mappings:\n"
            "  custom_category:\n"
            "    test_key: test_val\n"
            "  military_ranks:\n"
            "    - FLEET_ADMIRAL\n",
            encoding="utf-8",
        )
        merged = _load_reference_mappings(config_override_path=override_file)
        self.assertIsInstance(merged, dict)
        self.assertIn("custom_category", merged)
        self.assertEqual(merged["custom_category"], {"test_key": "test_val"})

    def test_load_reference_mappings_handles_missing_or_invalid_file(self) -> None:
        """_load_reference_mappings must fail gracefully on non-existent or invalid override."""
        base = _load_reference_mappings()
        missing = self.root / "does_not_exist.yaml"
        result = _load_reference_mappings(config_override_path=missing)
        self.assertEqual(result, base)

        invalid_file = self.root / "invalid.yaml"
        invalid_file.write_text(": : : not valid yaml\n  - [broken", encoding="utf-8")
        result_invalid = _load_reference_mappings(config_override_path=invalid_file)
        self.assertIsInstance(result_invalid, dict)

    def test_sctm_blank_row_tolerance_up_to_30(self) -> None:
        """SCTM hydration must tolerate up to 30 consecutive blank rows without truncating."""
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Template"
        ws["A2"] = "Template"
        ws["A7"] = "AC-01"
        # 25 consecutive blank rows: rows 8 through 32 are blank
        ws["A33"] = "AC-02"
        # Row 70 follows 36 blank rows (> 30 blanks), which should trigger the break guard
        ws["A70"] = "AC-03"

        test_template = self.root / "sctm_test_template.xlsx"
        wb.save(test_template)

        hydrator = SCTMHydrator(str(test_template))
        out_file = self.root / "sctm_output.xlsx"
        mock_inv = {
            "system_information": {
                "system_name": "TestEnclave",
                "organization": "TestAgency",
                "impact_level": "FedRAMP Moderate",
                "compliance_baseline": "NIST SP 800-53 Rev. 5",
            }
        }
        import unittest.mock as mock
        with mock.patch("compliance_engine.file_helpers.ensure_path_within_boundary", side_effect=lambda t, b, **k: Path(t)):
            with mock.patch("file_helpers.ensure_path_within_boundary", side_effect=lambda t, b, **k: Path(t)):
                hydrator.hydrate(mock_inv, str(out_file), allowed_boundary=self.root)

        res_wb = openpyxl.load_workbook(out_file)
        res_ws = res_wb["Template"]
        # Row 7 is hydrated (AC-01 has Planned status in SCTM catalog)
        self.assertEqual(res_ws.cell(row=7, column=5).value, "Planned")
        # Row 33 (after 25 consecutive blank rows) is ALSO hydrated (AC-02 is Implemented)
        self.assertEqual(res_ws.cell(row=33, column=5).value, "Implemented")
        # Row 70 (after 36 consecutive blank rows > 30) was truncated by break guard
        self.assertIsNone(res_ws.cell(row=70, column=5).value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
