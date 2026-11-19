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
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/fedramp-high/beyondcorp"
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


class TestBeyondcorpProviderConfiguration(unittest.TestCase):
    """The calling root configures the providers, not the module."""

    def test_module_declares_no_provider_blocks(self):
        # A module with provider blocks rejects count, for_each and
        # depends_on, and ignores the providers that the caller passes.
        for path in sorted(_MODULE_DIR.glob("*.tf")):
            with self.subTest(path=path.name):
                self.assertNotRegex(
                    path.read_text(encoding="utf-8"), r'(?m)^provider\s+"'
                )

    def test_module_declares_its_required_providers(self):
        self.assertRegex(
            _read("versions.tf"),
            r"required_providers \{\s*google = \{\s*source\s*=\s*"
            r'"hashicorp/google"',
        )

    def test_module_keeps_project_id_and_drops_region(self):
        variables = _read("variables.tf")
        # The resources read the project from the variable, so they do not
        # depend on a provider default.
        self.assertIn('variable "project_id"', variables)
        self.assertNotIn('variable "region"', variables)
        for name in ("main.tf", "outputs.tf"):
            with self.subTest(path=name):
                self.assertNotRegex(_read(name), r"var\.region\b")
        for resource in (
            'resource "google_project_service" "required_apis"',
            'resource "google_compute_backend_service" "iap_backend"',
            'resource "google_project_iam_member" "iap_user"',
        ):
            with self.subTest(resource=resource):
                self.assertRegex(
                    _block(_read("main.tf"), resource),
                    r"\n\s*project\s*=\s*var\.project_id\n",
                )

    def test_blueprint_configures_the_providers_at_the_root(self):
        provider_tf = (_BLUEPRINT_DIR / "provider.tf").read_text(
            encoding="utf-8"
        )
        for provider in ("google", "google-beta"):
            with self.subTest(provider=provider):
                block = _block(provider_tf, f'provider "{provider}"')
                self.assertRegex(block, r"billing_project\s*=\s*var\.")
                self.assertRegex(block, r"user_project_override\s*=\s*true")

    def test_blueprint_passes_no_removed_input(self):
        main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        module = _block(main_tf, 'module "beyondcorp"')
        self.assertRegex(module, r"\n\s*project_id\s*=\s*var\.main_project_id")
        self.assertNotRegex(module, r"\n\s*region\s*=")


if __name__ == "__main__":
    unittest.main()
