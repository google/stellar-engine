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

"""Checks the endpoint verification controls of the beyondcorp module."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_MODULE_DIR = _REPO_ROOT / "modules/beyondcorp"
_ACCESS_LEVEL = "google_access_context_manager_access_level.endpoint_verified"


def _read(name):
    return (_MODULE_DIR / name).read_text(encoding="utf-8")


def _block(text, header):
    """Returns the body of the top-level block that starts with header."""
    start = text.index(header)
    end = text.find("\n}", start)
    return text[start : end if end != -1 else len(text)]


class TestBeyondcorpEndpoint(unittest.TestCase):
    def test_access_level_allows_only_encrypted_devices(self):
        block = _block(
            _read("main.tf"),
            'resource "google_access_context_manager_access_level"',
        )
        statuses = re.search(
            r"allowed_encryption_statuses\s*=\s*\[([^\]]*)\]", block
        )
        self.assertIsNotNone(statuses)
        self.assertEqual(
            re.findall(r'"(\w+)"', statuses.group(1)), ["ENCRYPTED"]
        )

    def test_iap_grant_requires_the_access_level(self):
        main = _read("main.tf")
        block = _block(main, 'resource "google_project_iam_member" "iap_user"')
        self.assertRegex(
            block,
            r"condition\s*\{[^}]*"
            r"expression\s*=\s*local\.iap_condition_expression",
        )
        # IAM exposes the access levels as a list of full names, so the
        # condition tests membership and adds no prefix to the name.
        self.assertIn(
            '"\\"${local._access_level}\\" in request.auth.access_levels"',
            main,
        )
        self.assertRegex(
            main,
            rf"_access_level\s*=\s*\(\s*{re.escape(_ACCESS_LEVEL)}\.name\s",
        )
        self.assertNotIn(".match(", main)

    def test_oauth_client_secret_is_sensitive(self):
        block = _block(_read("variables.tf"), 'variable "oauth_client_secret"')
        self.assertRegex(block, r"sensitive\s*=\s*true")

    def test_endpoint_name_output_returns_the_name(self):
        block = _block(_read("outputs.tf"), 'output "endpoint_name"')
        self.assertRegex(
            block, rf"value\s*=\s*\(\s*{re.escape(_ACCESS_LEVEL)}\.name\s"
        )


if __name__ == "__main__":
    unittest.main()
