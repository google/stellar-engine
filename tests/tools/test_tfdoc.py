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
    items = list(tfdoc._parse(sample_out, enum=tfdoc.OUT_ENUM, re=tfdoc.OUT_RE, template=tfdoc.OUT_TEMPLATE))
    self.assertEqual(len(items), 1)
    item = items[0]
    self.assertEqual(item["name"], "vpc_id")
    self.assertIn("The VPC network self link.", "".join(item["description"]))


if __name__ == '__main__':
  unittest.main()
