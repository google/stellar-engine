# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for tools/check_versions.py."""

import os
import pathlib
import tempfile
import unittest

import check_versions

_VALID_TF = """
terraform {
  required_version = ">= 1.12.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 8.6.0, < 9.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 8.10.0, < 9.0.0"
    }
  }
}
"""


class TestCheckVersions(unittest.TestCase):
    """Tests constraint evaluation and repository scanning in check_versions."""

    def test_check_constraint_terraform_bounds(self):
        tf_min = check_versions.MIN_TERRAFORM_VERSION
        self.assertIsNone(check_versions.check_constraint(">= 1.12.2", tf_min))
        self.assertIsNone(check_versions.check_constraint(">= 1.13.3", tf_min))
        self.assertIsNone(check_versions.check_constraint("~> 1.12.2", tf_min))
        self.assertIsNotNone(
            check_versions.check_constraint(">= 1.7.4", tf_min)
        )
        self.assertIsNotNone(check_versions.check_constraint(">= 0.13", tf_min))
        self.assertIsNotNone(
            check_versions.check_constraint("<= 1.13.0", tf_min)
        )

    def test_check_constraint_google_bounds(self):
        g_min = check_versions.MIN_GOOGLE_VERSION
        g_max = check_versions.MAX_GOOGLE_VERSION_EXCL
        self.assertIsNone(
            check_versions.check_constraint(">= 8.6.0, < 9.0.0", g_min, g_max)
        )
        self.assertIsNone(
            check_versions.check_constraint(">= 8.10.0, < 9.0.0", g_min, g_max)
        )
        self.assertIsNone(
            check_versions.check_constraint("~> 8.6", g_min, g_max)
        )
        for bad in (
            ">= 8.10.0",
            ">= 6.21.0, < 9.0.0",
            ">= 5.0.0",
            "< 7.0.0",
            ">= 9.0.0, < 10.0.0",
            ">= 8.10.0, < 8.5.0",
            "",
        ):
            with self.subTest(bad=bad):
                self.assertIsNotNone(
                    check_versions.check_constraint(bad, g_min, g_max)
                )

    def test_check_repo_provider_tf_and_versions_tf(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "default-versions.tf").write_text(
                _VALID_TF, encoding="utf-8"
            )
            bp = root / "blueprints" / "il5" / "sample"
            bp.mkdir(parents=True)
            (bp / "provider.tf").write_text(_VALID_TF, encoding="utf-8")

            link_parent = root / "blueprints" / "fedramp-high"
            link_parent.mkdir(parents=True)
            os.symlink(bp, link_parent / "sample")

            mod_split = root / "modules" / "split"
            mod_split.mkdir(parents=True)
            (mod_split / "versions.tf").write_text(_VALID_TF, encoding="utf-8")
            (mod_split / "provider.tf").write_text(
                'provider "google" {}\n', encoding="utf-8"
            )

            self.assertEqual(check_versions.check_repo(root), [])

    def test_check_repo_rejects_bad_provider_and_missing_blueprint(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "default-versions.tf").write_text(
                _VALID_TF, encoding="utf-8"
            )
            bp_bad = root / "blueprints" / "il5" / "bad"
            bp_bad.mkdir(parents=True)
            (bp_bad / "provider.tf").write_text(
                """
# hashicorp/google >= 8.6.0, < 9.0.0 in comment must not fool parser
terraform {
  required_version = ">= 1.7.4"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "< 7.0.0"
    }
  }
}
""",
                encoding="utf-8",
            )
            bp_missing = root / "blueprints" / "il5" / "no-vfile"
            bp_missing.mkdir(parents=True)
            (bp_missing / "main.tf").write_text(
                'variable "project_id" {}\n', encoding="utf-8"
            )

            errors = check_versions.check_repo(root)
            joined = "\n".join(errors)
            self.assertIn("Invalid provider.tf", joined)
            self.assertIn("required_version", joined)
            self.assertIn("hashicorp/google", joined)
            self.assertIn("Invalid blueprint", joined)

    def test_check_repo_non_google_recipe_exemption(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            aws_recipe = root / "modules" / "net-vpn-ha" / "recipe-vpn-aws-gcp"
            aws_recipe.mkdir(parents=True)
            (aws_recipe / "providers.tf").write_text(
                """
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
""",
                encoding="utf-8",
            )
            self.assertEqual(check_versions.check_repo(root), [])


if __name__ == "__main__":
    unittest.main()
