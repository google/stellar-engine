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

"""Checks Stage 2/3 folder parent fallbacks."""

import pathlib
import re
import unittest

_STAGES_DIR = pathlib.Path(__file__).resolve().parents[1] / "fast/stages-aw"

_TARGET_FILES = (
    _STAGES_DIR / "2-networking-a-fedramp/main.tf",
    _STAGES_DIR / "2-networking-b-il5-ngfw/main.tf",
    _STAGES_DIR / "3-security/main.tf",
)


class TestStageFolderParentFallbacks(unittest.TestCase):
    def test_stage_folders_coalesce_enclave_parents(self):
        expected = re.compile(
            r'module "folder"\s*\{[\s\S]*?'
            r"parent\s*=\s*coalesce\(\s*"
            r"var\.common_services_folder,\s*"
            r"var\.assured_workloads\.folder,\s*"
            r'"organizations/\$\{var\.organization\.id\}"\s*\)'
        )
        for path in _TARGET_FILES:
            with self.subTest(path=path.relative_to(_STAGES_DIR)):
                self.assertRegex(path.read_text(encoding="utf-8"), expected)

    def test_stage_variables_define_non_nullable_assured_workloads(self):
        expected = re.compile(
            r'variable "assured_workloads"\s*\{[\s\S]*?'
            r"folder\s*=\s*optional\(string\)[\s\S]*?"
            r"nullable\s*=\s*false[\s\S]*?"
            r"default\s*=\s*\{\}[\s\S]*?\n\}"
        )
        for path in _TARGET_FILES:
            variables_tf = path.parent / "variables.tf"
            with self.subTest(path=variables_tf.relative_to(_STAGES_DIR)):
                self.assertRegex(
                    variables_tf.read_text(encoding="utf-8"), expected
                )


if __name__ == "__main__":
    unittest.main()
