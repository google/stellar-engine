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
"""Checks that the repository tooling runs through the locked uv project."""

import pathlib
import re
import tomllib
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_BARE_PYTHON_RE = re.compile(r"(?<![\w.-])python3?(?![\w.-])")
_UV_PYTHON_RE = re.compile(r"uv run\b[^\n]*\bpython\b")


def _load_toml(relative_path):
    with open(_REPO_ROOT / relative_path, "rb") as toml_file:
        return tomllib.load(toml_file)


class TestUvTooling(unittest.TestCase):
    def test_root_project_pins_the_cli_python_range(self):
        root = _load_toml("pyproject.toml")
        cli = _load_toml("cli/pyproject.toml")
        self.assertEqual(
            root["project"]["requires-python"],
            cli["project"]["requires-python"],
        )
        self.assertRegex(
            root["project"]["requires-python"], r"^>=3\.(\d+),<3\.(\d+)$"
        )
        lower, upper = re.findall(
            r"3\.(\d+)", root["project"]["requires-python"]
        )
        self.assertEqual(int(upper), int(lower) + 1)

    def test_root_project_is_not_a_workspace(self):
        root = _load_toml("pyproject.toml")
        self.assertFalse(root["tool"]["uv"]["package"])
        self.assertNotIn("workspace", root["tool"]["uv"])

    def test_root_lock_is_committed(self):
        self.assertTrue((_REPO_ROOT / "uv.lock").is_file())

    def test_tools_scripts_run_python_through_uv(self):
        for script in sorted((_REPO_ROOT / "tools").glob("*.sh")):
            with self.subTest(script=script.name):
                for line in script.read_text(encoding="utf-8").splitlines():
                    if line.lstrip().startswith("#"):
                        continue
                    if _BARE_PYTHON_RE.search(line):
                        self.assertRegex(line, _UV_PYTHON_RE)
                        self.assertIn("--locked", line)


if __name__ == "__main__":
    unittest.main()
