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
from compliance_engine.docx_generator import convert_markdown_to_docx


class TestReviewExportFixes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_docx_directory_traversal_hyperlink(self):
        # Major: relative-hyperlink allowlist accepts ../ traversal
        import zipfile
        md_content = "[evil link](../evil.docx) and [safe anchor](#section-1)"
        out_docx = self.root / "out.docx"
        convert_markdown_to_docx(md_content, str(out_docx), metadata=None, allowed_boundary=str(self.root))
        self.assertTrue(out_docx.exists())
        with zipfile.ZipFile(out_docx, "r") as zf:
            rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")
            doc_xml = zf.read("word/document.xml").decode("utf-8")
        self.assertNotIn("../evil.docx", rels_xml)
        self.assertNotIn("evil.docx", rels_xml)
        self.assertIn("#section-1", rels_xml)
        self.assertIn("evil link", doc_xml)

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
        # Minor: Markdown and metadata are scrubbed on the DOCX path
        import zipfile
        md_content = "# Security Plan\nLeaked key: AKIAIOSFODNN7EXAMPLE in body."
        out_docx = self.root / "out.docx"
        leaked_meta = {
            "system_information": {
                "system_name": "Test",
                "organization": "Org AKIAIOSFODNN7EXAMPLE",
                "compliance_baseline": "Baseline AKIAIOSFODNN7EXAMPLE",
            }
        }
        convert_markdown_to_docx(md_content, str(out_docx), metadata=leaked_meta, allowed_boundary=str(self.root))
        with zipfile.ZipFile(out_docx, "r") as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            app_xml = zf.read("docProps/app.xml").decode("utf-8")
            core_xml = zf.read("docProps/core.xml").decode("utf-8")
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", doc_xml)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", app_xml)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", core_xml)
        self.assertIn("[REDACTED_SENSITIVE]", doc_xml)
        self.assertIn("[REDACTED_SENSITIVE]", app_xml)


if __name__ == '__main__':
    unittest.main()
