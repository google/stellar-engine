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

  def test_skips_symlinks(self):
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
      target = os.path.join(tmpdir, 'unlicensed.txt')
      with open(target, 'w', encoding='utf-8') as f:
        f.write('no boilerplate here\n')
      link_py = os.path.join(tmpdir, 'linked.py')
      os.symlink(target, link_py)
      # Should not raise SystemExit(1) because symlinks are skipped
      check_boilerplate.main([tmpdir])

  def test_match_files_includes_yml(self):
    """Both .yaml and .yml extensions must be checked for boilerplate."""
    self.assertIn('.yml', check_boilerplate._MATCH_FILES)

  def test_EndToEnd_fails_on_missing_boilerplate_and_passes_on_valid(self):
    """End-to-end test of check_boilerplate.main on real files."""
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
      bad_py = os.path.join(tmpdir, 'bad.py')
      with open(bad_py, 'w', encoding='utf-8') as f:
        f.write('print("missing license")\n')
      with self.assertRaises(SystemExit) as ctx:
        check_boilerplate.main([tmpdir])
      self.assertEqual(ctx.exception.code, 1)

      # Now replace with valid boilerplate
      with open(bad_py, 'w', encoding='utf-8') as f:
        f.write(
            '# Copyright 2026 Google LLC\n'
            '#\n'
            '# Licensed under the Apache License, Version 2.0 (the "License");\n'
            '# you may not use this file except in compliance with the License.\n'
            '# You may obtain a copy of the License at\n'
            '#\n'
            '#     http://www.apache.org/licenses/LICENSE-2.0\n'
            '#\n'
            '# Unless required by applicable law or agreed to in writing, software\n'
            '# distributed under the License is distributed on an "AS IS" BASIS,\n'
            '# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n'
            '# See the License for the specific language governing permissions and\n'
            '# limitations under the License.\n'
        )
      # Should complete without raising SystemExit
      check_boilerplate.main([tmpdir])

  def test_EndToEnd_skips_ignored_dirs(self):
    """Directories in _EXCLUDE_DIRS (e.g., .venv, .terraform) must be skipped."""
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
      for skip_dir in check_boilerplate._EXCLUDE_DIRS:
        dpath = os.path.join(tmpdir, skip_dir)
        os.makedirs(dpath, exist_ok=True)
        with open(os.path.join(dpath, 'unlicensed.py'), 'w', encoding='utf-8') as f:
          f.write('x = 1\n')
      check_boilerplate.main([tmpdir])


if __name__ == '__main__':
  unittest.main()
