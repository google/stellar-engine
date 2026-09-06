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
import check_boilerplate


class TestCheckBoilerplate(unittest.TestCase):

  def test_valid_apache_boilerplate(self):
    content = """# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
"""
    self.assertIsNotNone(check_boilerplate._MATCH_RE.search(content))

  def test_missing_boilerplate(self):
    content = """# Some random script without license
print('Hello World')
"""
    self.assertIsNone(check_boilerplate._MATCH_RE.search(content))

  def test_exclude_comment_detected(self):
    content = """# skip boilerplate check
# Auto-generated code
"""
    self.assertIsNotNone(check_boilerplate._EXCLUDE_RE.search(content))

  def test_match_files_extensions(self):
    self.assertIn('.py', check_boilerplate._MATCH_FILES)
    self.assertIn('.sh', check_boilerplate._MATCH_FILES)
    self.assertIn('.tf', check_boilerplate._MATCH_FILES)
    self.assertIn('.yaml', check_boilerplate._MATCH_FILES)


if __name__ == '__main__':
  unittest.main()
