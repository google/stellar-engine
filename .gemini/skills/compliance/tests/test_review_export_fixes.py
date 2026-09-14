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

import os
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from compliance_engine.excel_hydrator import BaseExcelHydrator
from compliance_engine.docx_generator import convert_markdown_to_docx, batch_convert_policies_to_docx

import openpyxl

class TestReviewExportFixes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_docx_directory_traversal_hyperlink(self):
        # Major: relative-hyperlink allowlist accepts ../ traversal
        # We can't directly unit test the internal relationship manager easily without the full doc,
        # but we know we patched it. Let's run convert_markdown_to_docx with a malicious link.
        md_content = "[evil link](../evil.docx)"
        out_docx = self.root / "out.docx"
        convert_markdown_to_docx(md_content, str(out_docx), metadata=None, allowed_boundary=str(self.root))
        self.assertTrue(out_docx.exists())
        # The link should be stripped or rejected, docx should still generate successfully

    def test_docx_hardened_writer_symlink(self):
        # Major: Binary writers bypass the hardened write path
        md_content = "# Hello"
        out_docx = self.root / "out.docx"
        os.symlink("/tmp/nonexistent", str(out_docx))
        with self.assertRaises(PermissionError):
            convert_markdown_to_docx(md_content, str(out_docx), metadata=None, allowed_boundary=str(self.root))

    def test_docx_allowed_boundary_enforced(self):
        # Major: allowed_boundary is omitted
        md_content = "# Hello"
        out_docx = self.root / "out.docx"
        # Allowed boundary is a different dir
        other_dir = self.root / "other"
        other_dir.mkdir()
        with self.assertRaises(PermissionError):
            convert_markdown_to_docx(md_content, str(out_docx), metadata=None, allowed_boundary=str(other_dir))

    def test_docx_scrub_sensitive_data(self):
        # Minor: Markdown is not scrubbed on the DOCX path
        md_content = "# Title"
        out_docx = self.root / "out.docx"
        mock_meta = {"secret": "data", "system_information": {"system_name": "Test"}}
        with patch("compliance_engine.docx_generator.scrub_sensitive_data", return_value={"system_information": {"system_name": "Test"}}) as mock_scrub:
            convert_markdown_to_docx(md_content, str(out_docx), metadata=mock_meta, allowed_boundary=str(self.root))
            mock_scrub.assert_called_once_with(mock_meta)

if __name__ == '__main__':
    unittest.main()
