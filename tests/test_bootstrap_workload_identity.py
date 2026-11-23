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

"""Checks Stage 0 Workload and Workforce Identity Federation wiring."""

import pathlib
import unittest

_BOOTSTRAP_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "fast/stages-aw/0-bootstrap"
)


class TestBootstrapWorkloadIdentity(unittest.TestCase):
    def setUp(self):
        self.wif_tf = (_BOOTSTRAP_DIR / "workload-identity.tf").read_text(
            encoding="utf-8"
        )
        self.cicd_tf = (_BOOTSTRAP_DIR / "cicd.tf").read_text(encoding="utf-8")
        self.readme = (_BOOTSTRAP_DIR / "README.md").read_text(encoding="utf-8")

    def test_workload_identity_merges_defs_and_wires_oidc_fields(self):
        self.assertIn(
            "lookup(local.workload_identity_providers_defs, v.issuer, {})",
            self.wif_tf,
        )
        self.assertIn("issuer_uri        = each.value.issuer_uri", self.wif_tf)
        self.assertIn("jwks_json         = each.value.jwks_json", self.wif_tf)
        self.assertNotIn(
            "ref_type:branch:ref:main",
            self.wif_tf,
            "GitLab principal_repo must not hardcode ref:main",
        )

    def test_workforce_pool_wires_variable_attributes(self):
        self.assertIn("var.workforce_identity_pool.display_name", self.wif_tf)
        self.assertIn("var.workforce_identity_pool.description", self.wif_tf)
        self.assertIn("var.workforce_identity_pool.disabled", self.wif_tf)
        self.assertIn(
            "var.workforce_identity_pool.session_duration", self.wif_tf
        )

    def test_cicd_sa_fail_closes_on_null_branch_and_uses_cicd_providers(self):
        self.assertIn(
            "local.cicd_providers[v.identity_provider].principal_branch",
            self.cicd_tf,
        )
        self.assertIn(
            "local.cicd_providers[v.identity_provider].principal_repo",
            self.cicd_tf,
        )
        self.assertRegex(
            self.cicd_tf,
            r'"roles/iam\.workloadIdentityUser"\s*=\s*\(\s*'
            r"v\.branch\s*==\s*null\s*\?\s*\[\s*\]\s*:\s*\[",
        )

    def test_readme_references_real_variables_and_files(self):
        self.assertNotIn("workforce_identity_providers =", self.readme)
        self.assertNotIn("workload_identity_providers =", self.readme)
        self.assertNotIn("identity-providers.tf", self.readme)
        self.assertIn("workforce_identity_pool =", self.readme)
        self.assertIn("federated_identity_providers =", self.readme)
        self.assertIn("workload-identity.tf", self.readme)


if __name__ == "__main__":
    unittest.main()
