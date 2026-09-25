# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for blueprint API enablement and module ID length preconditions."""

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class TestBlueprintAndModuleValidations(unittest.TestCase):
  """Verify API enablement in blueprints and 30-char ID preconditions in modules."""

  def test_blueprints_enable_required_project_services(self):
    """Ensure app-engine and postgresql blueprints enable required APIs (#104)."""
    ae_tf = (
        REPO_ROOT / "blueprints/fedramp-high/app-engine/main.tf"
    ).read_text(encoding="utf-8")
    self.assertIn('resource "google_project_service" "appengine"', ae_tf)
    self.assertIn('service            = "appengine.googleapis.com"', ae_tf)
    self.assertIn("depends_on  = [google_project_service.appengine]", ae_tf)

    pg_tf = (
        REPO_ROOT / "blueprints/il5/postgresql/main.tf"
    ).read_text(encoding="utf-8")
    self.assertIn('resource "google_project_service" "sqladmin"', pg_tf)
    self.assertIn('service            = "sqladmin.googleapis.com"', pg_tf)
    self.assertIn("google_project_service.sqladmin", pg_tf)

  def test_modules_enforce_30_char_id_preconditions(self):
    """Ensure project and iam-service-account modules enforce 30-character ID preconditions (#228)."""
    proj_tf = (REPO_ROOT / "modules/project/main.tf").read_text(encoding="utf-8")
    self.assertIn('condition     = length("${local.prefix}${var.name}") <= 30', proj_tf)
    self.assertIn("exceeding the 30-character GCP project ID limit", proj_tf)

    sa_tf = (REPO_ROOT / "modules/iam-service-account/main.tf").read_text(
        encoding="utf-8"
    )
    self.assertIn('condition     = length("${local.prefix}${local.name}") <= 30', sa_tf)
    self.assertIn(
        "exceeding the 30-character GCP service account ID limit", sa_tf
    )


if __name__ == "__main__":
  unittest.main()
