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

import pathlib
import tempfile
import unittest
from unittest import mock

import check_names
from click.testing import CliRunner

_PROJECT_MODULE = """
module "automation-project" {
  source = "../../../modules/project"
  name   = "%s"
}
"""


class TestCheckNames(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.basedir = pathlib.Path(tmp.name)
        patcher = mock.patch.object(check_names, "BASEDIR", self.basedir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, project_name, *args):
        stage = self.basedir / "stage"
        stage.mkdir()
        (stage / "main.tf").write_text(_PROJECT_MODULE % project_name)
        return CliRunner().invoke(check_names.main, [*args, "stage"])

    def test_short_name_exits_zero(self):
        result = self._run("iac-core-0", "--prefix-length=10")
        self.assertEqual(result.exit_code, 0, result.output)

    def test_long_name_exits_non_zero(self):
        result = self._run(
            "a-very-long-iac-core-project-0", "--prefix-length=10"
        )
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("✗", result.output)

    def test_directory_without_names_is_a_usage_error(self):
        result = CliRunner().invoke(check_names.main, ["missing"])
        self.assertEqual(result.exit_code, 2, result.output)
        self.assertIn("no names found in missing", result.output)

    def test_lint_target_holds_names(self):
        lint = pathlib.Path(__file__).resolve().parents[1] / "tools" / "lint.sh"
        line = next(
            text
            for text in lint.read_text().splitlines()
            if "check_names.py" in text
        )
        target = line.split()[-1]
        with mock.patch.object(check_names, "BASEDIR", lint.parents[1]):
            self.assertTrue(list(check_names.get_names(target)), target)


if __name__ == "__main__":
    unittest.main()
