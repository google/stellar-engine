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

"""Checks the CMEK wiring of the Cloud Spanner blueprint."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/fedramp-high/cloud-spanner"
_GATE = r"count\s*=\s*var\.kms_key_name == null \? 0 : 1\n"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestCloudSpannerCmek(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")

    def test_kms_key_name_is_optional(self):
        variables_tf = (_BLUEPRINT_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        variable = _top_block(variables_tf, 'variable "kms_key_name"')
        self.assertRegex(variable, r"\n\s*type\s*=\s*string\n")
        self.assertRegex(variable, r"\n\s*default\s*=\s*null\n")

    def test_kms_key_name_rejects_malformed_values_at_plan_time(self):
        # An empty or malformed key would otherwise fail only at apply,
        # after the API and the service identity exist.
        variables_tf = (_BLUEPRINT_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        variable = _top_block(variables_tf, 'variable "kms_key_name"')
        self.assertIn("var.kms_key_name == null ||", variable)
        pattern = re.search(r'can\(regex\(\s*"([^"]+)"', variable)
        self.assertIsNotNone(pattern)
        key = "projects/my-project/locations/us-east4/keyRings/r/cryptoKeys/k"
        self.assertRegex(key, pattern.group(1))
        self.assertNotRegex("", pattern.group(1))
        self.assertNotRegex(key + "/cryptoKeyVersions/1", pattern.group(1))
        self.assertNotRegex(key + " ", pattern.group(1))

    def test_sample_keeps_cmek_opt_in(self):
        sample = (_BLUEPRINT_DIR / "terraform.tfvars.sample").read_text(
            encoding="utf-8"
        )
        self.assertRegex(sample, r"\n# kms_key_name = ")
        self.assertNotRegex(sample, r"\nkms_key_name\s*=")

    def test_database_receives_the_key(self):
        # The module configures CMEK per database, so the key belongs
        # inside the database entry and not at the module root.
        module = _top_block(self.main_tf, 'module "cloud-spanner"')
        self.assertRegex(
            module,
            r"\(var\.database_name\) = \{[\s\S]*?"
            r"\n {6}kms_key_name = var\.kms_key_name\n",
        )
        self.assertNotRegex(module, r"\n {2}kms_key_name\s*=")

    def test_service_identity_is_gated_and_uses_beta_provider(self):
        identity = _top_block(
            self.main_tf,
            'resource "google_project_service_identity" "spanner"',
        )
        # Only the beta provider offers this resource.
        self.assertRegex(identity, r"provider\s*=\s*google-beta\n")
        self.assertRegex(identity, _GATE)
        self.assertRegex(identity, r'service\s*=\s*"spanner\.googleapis\.com"')
        self.assertRegex(
            identity,
            r"depends_on\s*=\s*\[google_project_service\.spanner_api\]",
        )

    def test_service_agent_gets_additive_key_grant(self):
        grant = _top_block(
            self.main_tf,
            'resource "google_kms_crypto_key_iam_member" "spanner_cmek"',
        )
        self.assertRegex(grant, _GATE)
        self.assertRegex(grant, r"crypto_key_id\s*=\s*var\.kms_key_name\n")
        self.assertRegex(
            grant,
            r'role\s*=\s*"roles/cloudkms\.cryptoKeyEncrypterDecrypter"',
        )
        self.assertRegex(
            grant,
            r"member\s*=\s*"
            r"google_project_service_identity\.spanner\[0\]\.member\n",
        )
        self.assertNotIn("google_kms_crypto_key_iam_binding", self.main_tf)
        self.assertNotIn("google_kms_crypto_key_iam_policy", self.main_tf)

    def test_database_waits_for_the_key_grant(self):
        module = _top_block(self.main_tf, 'module "cloud-spanner"')
        depends_on = re.search(r"depends_on\s*=\s*\[([\s\S]*?)\]", module)
        self.assertIsNotNone(depends_on)
        self.assertIn("google_project_service.spanner_api", depends_on.group(1))
        self.assertIn(
            "google_kms_crypto_key_iam_member.spanner_cmek",
            depends_on.group(1),
        )


if __name__ == "__main__":
    unittest.main()
