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

"""Checks that the postgresql blueprint waits for its service agent."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/il5/postgresql"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestPostgresqlServiceAgentWait(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")

    def test_wait_follows_the_service_agent(self):
        wait = _top_block(
            self.main_tf, 'resource "time_sleep" "cloudsql_sa_propagation"'
        )
        self.assertRegex(wait, r'create_duration\s*=\s*"\d+[sm]"')
        self.assertRegex(
            wait,
            r"depends_on\s*=\s*"
            r"\[google_project_service_identity\.cloudsql_sa\]",
        )

    def test_key_grant_waits_for_the_service_agent_to_propagate(self):
        # A grant issued right after the service agent is created fails,
        # because IAM does not recognize the new agent yet.
        grant = _top_block(
            self.main_tf, 'resource "google_kms_crypto_key_iam_member" "sql_sa"'
        )
        self.assertRegex(
            grant,
            r"depends_on\s*=\s*\[time_sleep\.cloudsql_sa_propagation\]",
        )

    def test_time_provider_is_declared(self):
        provider_tf = (_BLUEPRINT_DIR / "provider.tf").read_text(
            encoding="utf-8"
        )
        self.assertRegex(provider_tf, r'source\s*=\s*"hashicorp/time"')

    def test_beta_provider_is_declared_and_configured(self):
        # The service identity and the Cloud SQL module use google-beta, so
        # it needs the same version bounds and defaults as google.
        provider_tf = (_BLUEPRINT_DIR / "provider.tf").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            provider_tf,
            r'google-beta = \{\s*source\s*=\s*"hashicorp/google-beta"\s*'
            r'version\s*=\s*">= 8\.6\.0, < 9\.0\.0"',
        )
        block = _top_block(provider_tf, 'provider "google-beta"')
        self.assertRegex(block, r"project\s*=\s*var\.main_project_id")
        self.assertRegex(block, r"region\s*=\s*var\.region")


if __name__ == "__main__":
    unittest.main()
