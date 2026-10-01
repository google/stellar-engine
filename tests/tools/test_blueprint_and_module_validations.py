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



  def test_custom_stellar_engine_modules_validations(self):
    """Verify hardening and logic fixes across custom Stellar Engine modules."""
    alerts_main = (REPO_ROOT / "modules/cis-log-alerts/main.tf").read_text(encoding="utf-8")
    self.assertIn("concat([google_monitoring_notification_channel.email.name], var.notification_channels)", alerts_main)
    self.assertIn("display_name = each.key", alerts_main)
    self.assertNotIn('display_name = "each.key"', alerts_main)

    alerts_vars = (REPO_ROOT / "modules/cis-log-alerts/variables.tf").read_text(encoding="utf-8")
    self.assertIn('variable "notification_channels"', alerts_vars)

    metrics_main = (REPO_ROOT / "modules/cis-log-metrics/main.tf").read_text(encoding="utf-8")
    self.assertIn("AND ((ProjectOwnership OR projectOwnerInvitee)", metrics_main)

    ids_main = (REPO_ROOT / "modules/intrusion-detection-system/main.tf").read_text(encoding="utf-8")
    self.assertIn("count = var.create_service_networking_connection ? 1 : 0", ids_main)

    org_se_iam = (REPO_ROOT / "modules/organization-se/iam.tf").read_text(encoding="utf-8")
    self.assertIn('"iam-bpa:${principal}//${role}"', org_se_iam)
    org_se_vars = (REPO_ROOT / "modules/organization-se/variables.tf").read_text(encoding="utf-8")
    self.assertIn('can(regex("^organizations/[0-9]+$", var.organization_id))', org_se_vars)

    spanner_se_iam = (REPO_ROOT / "modules/spanner-instance-se/iam.tf").read_text(encoding="utf-8")
    self.assertIn('dynamic "condition"', spanner_se_iam)
    spanner_se_vars = (REPO_ROOT / "modules/spanner-instance-se/variables.tf").read_text(encoding="utf-8")
    self.assertIn("condition = optional(object({", spanner_se_vars)


if __name__ == "__main__":
  unittest.main()
