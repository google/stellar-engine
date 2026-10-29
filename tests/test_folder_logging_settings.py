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

"""Checks the folder module passes a bare folder number where needed."""

import pathlib
import re
import unittest

_FOLDER_DIR = pathlib.Path(__file__).resolve().parents[1] / "modules/folder"


class TestFolderLoggingSettings(unittest.TestCase):
    def test_settings_use_the_folder_number(self):
        # The provider builds folders/{{folder}}/settings itself, so the
        # folder ID with its folders/ prefix doubles the prefix.
        logging_tf = (_FOLDER_DIR / "logging.tf").read_text(encoding="utf-8")
        block = re.search(
            r'resource "google_logging_folder_settings" "default"\s*\{'
            r"[\s\S]*?\n\}",
            logging_tf,
        )
        self.assertIsNotNone(block)
        self.assertRegex(
            block.group(0), r"\n\s*folder\s*=\s*local\.folder_number\n"
        )

    def test_folder_number_strips_the_prefix(self):
        main_tf = (_FOLDER_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertRegex(
            main_tf,
            r"folder_number\s*=\s*\(\s*local\.folder_id == null \? null : "
            r'trimprefix\(local\.folder_id, "folders/"\)\s*\)',
        )


if __name__ == "__main__":
    unittest.main()
