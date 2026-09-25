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


if __name__ == "__main__":
  unittest.main()
