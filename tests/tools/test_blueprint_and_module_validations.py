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



  def test_synced_upstream_cff_modules_fixes(self):
    """Verify upstream CFF fixes in synced folder, net-lb-int, net-lb-proxy-int, spanner-instance, and cloud-run-v2 modules."""
    self.assertFalse((REPO_ROOT / "modules/cloud-run").exists())
    self.assertTrue((REPO_ROOT / "modules/cloud-run-v2").exists())

    folder_vars = (REPO_ROOT / "modules/folder/variables.tf").read_text(encoding="utf-8")
    self.assertNotIn('"CA_PROTECTED_B, IL5, HIPAA, HITRUST"', folder_vars)
    self.assertIn('"IL5"', folder_vars)

    nlb_hc = (REPO_ROOT / "modules/net-lb-int/health-check.tf").read_text(encoding="utf-8")
    self.assertIn("local.hc.http2.host", nlb_hc)
    self.assertIn("local.hc.ssl.port", nlb_hc)

    proxy_bs = (REPO_ROOT / "modules/net-lb-proxy-int/backend-service.tf").read_text(encoding="utf-8")
    self.assertNotIn(" ar.backend_service_config", proxy_bs)
    self.assertNotIn("local.bs_conntrack", proxy_bs)

    spanner_iam = (REPO_ROOT / "modules/spanner-instance/iam.tf").read_text(encoding="utf-8")
    self.assertIn('dynamic "condition"', spanner_iam)


if __name__ == "__main__":
  unittest.main()
