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

"""Checks the CMEK wiring of the Cloud Composer environment blueprint."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = (
    _REPO_ROOT / "blueprints/fedramp-high/cloud-composer-environment"
)
_GATE = r"count\s*=\s*var\.kms_key_name == null \? 0 : 1\n"
_KEY_GRANT = 'resource "google_kms_crypto_key_iam_member" '
# Cloud Composer 3 requires the key for these two service agents only.
_KEY_GRANT_MEMBERS = {
    "composer_agent_cmek": (
        r"google_project_service_identity\.composer_agent\.member"
    ),
    "storage_agent_cmek": (
        r"data\.google_storage_project_service_account\.gcs\[0\]\.member"
    ),
}


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestCloudComposerCmek(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        self.iam_tf = (_BLUEPRINT_DIR / "iam.tf").read_text(encoding="utf-8")
        self.variable = _top_block(
            (_BLUEPRINT_DIR / "variables.tf").read_text(encoding="utf-8"),
            'variable "kms_key_name"',
        )
        self.environment = _top_block(
            self.main_tf, 'resource "google_composer_environment" "main"'
        )

    def test_kms_key_name_is_optional(self):
        self.assertRegex(self.variable, r"\n\s*type\s*=\s*string\n")
        self.assertRegex(self.variable, r"\n\s*default\s*=\s*null\n")

    def test_kms_key_name_rejects_malformed_values_at_plan_time(self):
        # An empty or malformed key would otherwise fail only at apply,
        # after the API and the service identity exist.
        self.assertIn("var.kms_key_name == null ||", self.variable)
        pattern = re.search(r'can\(regex\(\s*"([^"]+)"', self.variable)
        self.assertIsNotNone(pattern)
        key = "projects/my-project/locations/us-east4/keyRings/r/cryptoKeys/k"
        self.assertRegex(key, pattern.group(1))
        self.assertNotRegex("", pattern.group(1))
        self.assertNotRegex(key + "/cryptoKeyVersions/1", pattern.group(1))
        self.assertNotRegex(key + " ", pattern.group(1))

    def test_kms_key_name_documents_location_and_replacement(self):
        description = re.search(r'description\s*=\s*"([^"]+)"', self.variable)
        self.assertIsNotNone(description)
        self.assertIn("same region as the environment", description.group(1))
        self.assertIn("forces replacement", description.group(1))

    def test_sample_keeps_cmek_opt_in(self):
        sample = (_BLUEPRINT_DIR / "terraform.tfvars.sample").read_text(
            encoding="utf-8"
        )
        self.assertRegex(sample, r"\n# kms_key_name = ")
        self.assertNotRegex(sample, r"\nkms_key_name\s*=")

    def test_environment_is_encrypted_only_when_the_key_is_set(self):
        # A static block would change the plan of deployments without a key.
        self.assertRegex(
            self.environment,
            r'dynamic "encryption_config" \{\n'
            r"\s*for_each = var\.kms_key_name == null \? \[\] : "
            r"\[var\.kms_key_name\]\n"
            r"\s*content \{\n"
            r"\s*kms_key_name = encryption_config\.value\n",
        )
        self.assertNotRegex(self.environment, r"\n\s*encryption_config\s*\{")

    def test_service_agents_get_additive_key_grants(self):
        for label, member in _KEY_GRANT_MEMBERS.items():
            with self.subTest(grant=label):
                grant = _top_block(self.iam_tf, f'{_KEY_GRANT}"{label}"')
                self.assertRegex(grant, _GATE)
                self.assertRegex(
                    grant, r"crypto_key_id\s*=\s*var\.kms_key_name\n"
                )
                self.assertRegex(
                    grant,
                    r'role\s*=\s*"roles/cloudkms\.cryptoKeyEncrypterDecrypter"',
                )
                self.assertRegex(grant, r"member\s*=\s*" + member + r"\n")
        for text in (self.main_tf, self.iam_tf):
            self.assertNotIn("google_kms_crypto_key_iam_binding", text)
            self.assertNotIn("google_kms_crypto_key_iam_policy", text)

    def test_key_grants_are_limited_to_the_required_service_agents(self):
        labels = re.findall(
            re.escape(_KEY_GRANT) + r'"(\w+)"', self.main_tf + self.iam_tf
        )
        self.assertCountEqual(labels, _KEY_GRANT_MEMBERS)

    def test_storage_service_agent_lookup_is_gated(self):
        # An ungated lookup would add a Cloud Storage API call to the plan
        # of deployments without a key.
        lookup = _top_block(
            self.main_tf,
            'data "google_storage_project_service_account" "gcs"',
        )
        self.assertRegex(lookup, _GATE)
        self.assertRegex(lookup, r"project\s*=\s*var\.main_project_id\n")

    def test_environment_waits_for_the_key_grants(self):
        depends_on = re.search(
            r"depends_on\s*=\s*\[([\s\S]*?)\]", self.environment
        )
        self.assertIsNotNone(depends_on)
        for label in _KEY_GRANT_MEMBERS:
            self.assertIn(
                f"google_kms_crypto_key_iam_member.{label}",
                depends_on.group(1),
            )


if __name__ == "__main__":
    unittest.main()
