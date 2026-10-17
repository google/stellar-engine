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

"""The scrubber keeps inventory structure while still redacting secret values."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from compliance_engine import extract_system_data
from compliance_engine import file_helpers

_TF = (
    'resource "google_secret_manager_secret" "db_password" {\n'
    '  secret_id = "db-password"\n'
    '  replication {\n    auto {}\n  }\n}\n'
    'resource "google_secret_manager_secret" "api_token" {\n'
    '  secret_id = "api-token"\n'
    '  replication {\n    auto {}\n  }\n}\n'
    'resource "google_secret_manager_secret_version" "db_password_v1" {\n'
    '  secret      = google_secret_manager_secret.db_password.id\n'
    '  secret_data = "hunter2-not-a-real-password"\n'
    '}\n'
)


class SecretsContainerTest(unittest.TestCase):
    """infrastructure_components.secrets is a resource inventory, not a credential."""

    def test_secrets_container_not_wiped(self) -> None:
        inventory = {"infrastructure_components": {"secrets": ["db_password", "api_token"]}}
        scrubbed = file_helpers.scrub_sensitive_data(inventory)
        self.assertEqual(scrubbed["infrastructure_components"]["secrets"], ["db_password", "api_token"])

    def test_secret_values_still_redacted(self) -> None:
        token = "ghp_" + "A" * 36
        inventory = {
            "infrastructure_components": {
                # A name that embeds a credential is span-redacted, not kept verbatim.
                "secrets": ["db_password", f"leaked-{token}"],
            },
            "variables": {"secret_data": "hunter2-not-a-real-password", "client_secret": "x"},
            # The exemption is path-specific: a top-level "secrets" key is still redacted.
            "secrets": ["hunter2-not-a-real-password"],
        }
        scrubbed = file_helpers.scrub_sensitive_data(inventory)
        names = scrubbed["infrastructure_components"]["secrets"]
        self.assertEqual(names[0], "db_password")
        self.assertNotIn(token, json.dumps(scrubbed))
        self.assertEqual(scrubbed["variables"]["secret_data"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["variables"]["client_secret"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["secrets"], "[REDACTED_SENSITIVE]")

    def test_non_name_payload_under_secrets_still_redacted(self) -> None:
        # Only a flat list of names is exempt; a mapping could carry payloads.
        inventory = {"infrastructure_components": {"secrets": {"db": "hunter2-not-a-real-password"}}}
        scrubbed = file_helpers.scrub_sensitive_data(inventory)
        self.assertEqual(scrubbed["infrastructure_components"]["secrets"], "[REDACTED_SENSITIVE]")

    def test_extracted_inventory_keeps_two_secret_names_without_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "blueprints" / "il5" / "secrets_demo"
            target.mkdir(parents=True)
            (target / "main.tf").write_text(_TF, encoding="utf-8")
            with mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "1", "COMPLIANCE_OFFLINE": "1"}):
                extract_system_data.extract_system_inventory(str(target))
            raw = (target / "system_inventory.json").read_text(encoding="utf-8")
            inventory = json.loads(raw)
        secrets = inventory["infrastructure_components"]["secrets"]
        self.assertIsInstance(secrets, list)
        self.assertEqual(len(secrets), 2)
        self.assertEqual(sorted(secrets), ["api_token", "db_password"])
        self.assertNotIn("hunter2-not-a-real-password", raw)


if __name__ == "__main__":
    unittest.main()
