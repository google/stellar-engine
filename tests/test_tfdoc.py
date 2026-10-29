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
import tempfile
import unittest

import tfdoc


class TestTfDoc(unittest.TestCase):
    def test_count_test_re(self):
        test_line = "# tftest modules=3 resources=12"
        m = tfdoc.COUNT_TEST_RE.search(test_line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("modules"), "3")
        self.assertEqual(m.group("resources"), "12")

    def test_count_test_re_with_files(self):
        test_line = "# tftest modules=1 resources=4 files=file1,file2"
        m = tfdoc.COUNT_TEST_RE.search(test_line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("modules"), "1")
        self.assertEqual(m.group("resources"), "4")
        self.assertEqual(m.group("files"), "file1,file2")

    def test_tag_re(self):
        tag_line = "# tfdoc:variable:source fast/stages-aw/0-bootstrap"
        m = tfdoc.TAG_RE.match(tag_line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "variable:source")
        self.assertEqual(m.group(2), "fast/stages-aw/0-bootstrap")

    def test_file_desc_defaults(self):
        self.assertIn("main.tf", tfdoc.FILE_DESC_DEFAULTS)
        self.assertIn("variables.tf", tfdoc.FILE_DESC_DEFAULTS)
        self.assertIn("outputs.tf", tfdoc.FILE_DESC_DEFAULTS)
        self.assertIn("versions.tf", tfdoc.FILE_DESC_DEFAULTS)

    def test_variable_regex_parsing(self):
        sample_var = """
variable "project_id" {
  description = "The GCP project ID."
  type        = string
}
"""
        items = list(tfdoc._parse(sample_var))
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["name"], "project_id")
        self.assertIn("The GCP project ID.", "".join(item["description"]))

    def test_output_regex_parsing(self):
        sample_out = """
output "vpc_id" {
  description = "The VPC network self link."
  value       = google_compute_network.main.id
}
"""
        items = list(
            tfdoc._parse(
                sample_out,
                enum=tfdoc.OUT_ENUM,
                re=tfdoc.OUT_RE,
                template=tfdoc.OUT_TEMPLATE,
            )
        )
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["name"], "vpc_id")
        self.assertIn(
            "The VPC network self link.", "".join(item["description"])
        )

    def test_parse_files_skips_symlinks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            real_tf = os.path.join(tmpdir, "main.tf")
            with open(real_tf, "w", encoding="utf-8") as f:
                f.write("# main\n")
            ext_tf = os.path.join(tmpdir, "external.txt")
            with open(ext_tf, "w", encoding="utf-8") as f:
                f.write("# external\n")
            os.symlink(ext_tf, os.path.join(tmpdir, "linked.tf"))
            files = list(tfdoc.parse_files(tmpdir))
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, "main.tf")

    def test_create_and_render_tfref_generates_expected_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vars_path = os.path.join(tmpdir, "variables.tf")
            with open(vars_path, "w", encoding="utf-8") as f:
                f.write(
                    'variable "project_id" {\n'
                    '  description = "Project ID."\n'
                    "  type        = string\n"
                    "}\n"
                )
            outs_path = os.path.join(tmpdir, "outputs.tf")
            with open(outs_path, "w", encoding="utf-8") as f:
                f.write(
                    'output "id" {\n'
                    '  description = "Output ID."\n'
                    "  value       = var.project_id\n"
                    "  sensitive   = true\n"
                    "}\n"
                )
            doc = tfdoc.create_tfref(
                tmpdir, files=False, show_extra=False, readme=""
            )
            rendered = tfdoc.render_tfref(
                f"# Mod\n{tfdoc.MARK_BEGIN}\n{tfdoc.MARK_END}\n", doc.content
            )
            self.assertIn(
                "| [project_id](variables.tf#L1) | Project ID."
                " | <code>string</code> | ✓ |  |",
                rendered,
            )
            self.assertIn("| [id](outputs.tf#L1) | Output ID. | ✓ |", rendered)


if __name__ == "__main__":
    unittest.main()
