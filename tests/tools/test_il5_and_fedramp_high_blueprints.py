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

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class TestModuleAndBlueprintHardening(unittest.TestCase):
  def test_il5_and_fedramp_high_blueprint_security_hardening(self):
    """Verify security hardening across blueprints/il5 and blueprints/fedramp-high."""
    docai_main = (REPO_ROOT / "blueprints/fedramp-high/document-ai/main.tf").read_text(encoding="utf-8")
    self.assertIn('"roles/storage.objectViewer" = [google_service_account.workflow_sa.member]', docai_main)
    docai_iam = (REPO_ROOT / "blueprints/fedramp-high/document-ai/iam.tf").read_text(encoding="utf-8")
    self.assertIn("project      = var.main_project_id", docai_iam)
    self.assertIn("@gcp-sa-prod-dai-core.iam.gserviceaccount.com", docai_iam)

    trans_main = (REPO_ROOT / "blueprints/fedramp-high/cloud-translation/main.tf").read_text(encoding="utf-8")
    self.assertIn("encryption_key              = var.kms_key_self_link", trans_main)
    self.assertIn('resource "google_project_iam_member" "workflow_sa_roles"', trans_main)

    gitlab_main = (REPO_ROOT / "blueprints/fedramp-high/gitlab/main.tf").read_text(encoding="utf-8")
    self.assertIn('resource "google_service_account" "gke_node_sa"', gitlab_main)
    self.assertIn('protocol   = "HTTPS"', gitlab_main)
    self.assertNotIn("gitlab_sa     = \"serviceAccount:${google_service_account.gitlab-sa.email}\"\n  }\n  crypto_key_id", gitlab_main)

    pg_main = (REPO_ROOT / "blueprints/il5/postgresql/main.tf").read_text(encoding="utf-8")
    self.assertIn('target_tags   = ["postgres"]', pg_main)

    bastion_main = (REPO_ROOT / "blueprints/il5/bastion-pattern/main.tf").read_text(encoding="utf-8")
    self.assertIn("target_service_accounts = [google_service_account.compute.email]", bastion_main)

    gkeh_main = (REPO_ROOT / "blueprints/il5/gke-hardened/main.tf").read_text(encoding="utf-8")
    self.assertIn("auto_create = true", gkeh_main)
    self.assertIn("remove_pool        = coalesce(var.remove_default_node_pool, true)", gkeh_main)
    self.assertIn("secret_type = var.config_sync_secret_type", gkeh_main)

    gke_main = (REPO_ROOT / "blueprints/il5/gke/main.tf").read_text(encoding="utf-8")
    self.assertIn('resource "google_service_account" "bastion_sa"', gke_main)
    self.assertIn("private_nodes = true", gke_main)
    gke_prov = (REPO_ROOT / "blueprints/il5/gke/provider.tf").read_text(encoding="utf-8")
    self.assertIn('required_version = ">= 1.10.2"', gke_prov)
    self.assertIn('version = ">= 6.21.0, < 7.0.0"', gke_prov)

    cnap_cr = (REPO_ROOT / "blueprints/fedramp-high/cnap/cloud_run.tf").read_text(encoding="utf-8")
    self.assertIn("service_account = google_service_account.cloud_run.email", cnap_cr)
    self.assertIn("vpc_access {", cnap_cr)
    cnap_iap = (REPO_ROOT / "blueprints/fedramp-high/cnap/iap.tf").read_text(encoding="utf-8")
    self.assertIn('resource "google_cloud_run_v2_service_iam_member" "iap_sa_cloudrun_invoker"', cnap_iap)

    pubsub_main = (REPO_ROOT / "blueprints/il5/pub-sub-project/main.tf").read_text(encoding="utf-8")
    self.assertIn('resource "google_pubsub_topic_iam_member" "pubsub_publisher"', pubsub_main)
    self.assertIn('resource "google_pubsub_subscription_iam_member" "pubsub_subscriber"', pubsub_main)

    cf_main = (REPO_ROOT / "blueprints/fedramp-high/cloud-functions/main.tf").read_text(encoding="utf-8")
    self.assertIn('module "service-account-runtime"', cf_main)
    self.assertNotIn('resource "google_project_iam_member" "cloud_invoker"', cf_main)

    cw_iam = (REPO_ROOT / "blueprints/fedramp-high/cloud-workstations/iam.tf").read_text(encoding="utf-8")
    self.assertIn('resource "google_service_account" "workstation_vm"', cw_iam)
    self.assertIn('resource "google_compute_subnetwork_iam_member" "network_user"', cw_iam)

    comp_main = (REPO_ROOT / "blueprints/fedramp-high/cloud-composer-environment/main.tf").read_text(encoding="utf-8")
    self.assertIn('dynamic "encryption_config"', comp_main)
    self.assertIn("web_server_network_access_control {", comp_main)

    spanner_main = (REPO_ROOT / "blueprints/fedramp-high/cloud-spanner/main.tf").read_text(encoding="utf-8")
    self.assertIn("kms_key_name = var.kms_key_name", spanner_main)

    cr_main = (REPO_ROOT / "blueprints/fedramp-high/cloud-run/main.tf").read_text(encoding="utf-8")
    self.assertNotIn('resource "google_project_iam_member" "cloud_run_permissions"', cr_main)
    cr_vars = (REPO_ROOT / "blueprints/fedramp-high/cloud-run/variables.tf").read_text(encoding="utf-8")
    self.assertIn('contains(["default", "policy"], var.binary_authorization_mode)', cr_vars)

    df_main = (REPO_ROOT / "blueprints/il5/dataflow/main.tf").read_text(encoding="utf-8")
    self.assertIn("network    = var.network_name", df_main)
    self.assertIn("account_id   = substr(var.main_project_id, 0, 28)", df_main)

    ar_tpl = (REPO_ROOT / "blueprints/il5/artifact-registry/templates/userdata.tftpl").read_text(encoding="utf-8")
    self.assertIn("gpgcheck=1", ar_tpl)


if __name__ == "__main__":
  unittest.main()
