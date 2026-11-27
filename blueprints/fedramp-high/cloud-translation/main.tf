# Copyright 2025 Google LLC
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

# Enable the API service
resource "google_project_service" "translate" {
  project = var.main_project_id
  for_each = toset([
    "storage.googleapis.com",
    "translate.googleapis.com",
    "workflows.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_project_service_identity" "translate_sa" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "translate.googleapis.com"
  depends_on = [google_project_service.translate]
}

resource "google_project_service_identity" "workflows_sa" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "workflows.googleapis.com"
  depends_on = [google_project_service.translate]
}

# storage.googleapis.com has no primary service identity via
# serviceusage.services.generateServiceIdentity, so look up the GCS agent.
data "google_storage_project_service_account" "gcs_sa" {
  count      = var.kms_key_self_link == null ? 0 : 1
  project    = var.main_project_id
  depends_on = [google_project_service.translate]
}

# IAM does not recognize newly created service agents right away, so a short
# propagation wait prevents first-apply KMS IAM grant failures.
resource "time_sleep" "service_agent_propagation" {
  count           = var.kms_key_self_link == null ? 0 : 1
  create_duration = "60s"

  depends_on = [
    google_project_service_identity.translate_sa,
    google_project_service_identity.workflows_sa,
    data.google_storage_project_service_account.gcs_sa,
  ]
}

resource "google_kms_crypto_key_iam_member" "gcs_cmek" {
  count         = var.kms_key_self_link == null ? 0 : 1
  crypto_key_id = var.kms_key_self_link
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = data.google_storage_project_service_account.gcs_sa[0].member

  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_kms_crypto_key_iam_member" "translate_cmek" {
  count         = var.kms_key_self_link == null ? 0 : 1
  crypto_key_id = var.kms_key_self_link
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.translate_sa.member

  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_kms_crypto_key_iam_member" "workflows_cmek" {
  count         = var.kms_key_self_link == null ? 0 : 1
  crypto_key_id = var.kms_key_self_link
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.workflows_sa.member

  depends_on = [time_sleep.service_agent_propagation]
}

moved {
  from = module.input_bucket
  to   = module.input-bucket
}

module "input-bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "translate-input"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  encryption_key              = var.kms_key_self_link

  depends_on = [
    google_project_service.translate,
    google_kms_crypto_key_iam_member.gcs_cmek,
  ]
}

moved {
  from = module.output_bucket
  to   = module.output-bucket
}

module "output-bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "translate-output"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  encryption_key              = var.kms_key_self_link

  depends_on = [
    google_project_service.translate,
    google_kms_crypto_key_iam_member.gcs_cmek,
  ]
}

resource "google_service_account" "workflow_sa" {
  project      = var.main_project_id
  account_id   = "translate-workflow-sa"
  display_name = "Workflows Service Account."
}

module "workflows" {
  source              = "../../../modules/workflows"
  project             = var.main_project_id
  name                = "translate-workflow"
  region              = var.region
  deletion_protection = var.deletion_protection
  description         = "Translation LLM example workflow."
  file                = var.file
  kms_key_self_link   = var.kms_key_self_link
  service_account     = google_service_account.workflow_sa.email
  env_vars = {
    input_bucket  = "${module.input-bucket.url}/*.txt"
    output_bucket = "${module.output-bucket.url}/${var.output_folder}/"
    src_lang      = var.src_lang
    target_lang   = var.target_lang
    parent        = "projects/${var.main_project_id}/locations/${var.region}"
  }
  iam = {
    "roles/workflows.invoker"                 = [google_service_account.workflow_sa.member],
    "roles/logging.logWriter"                 = [google_service_account.workflow_sa.member],
    "roles/serviceusage.serviceUsageConsumer" = [google_service_account.workflow_sa.member],
    "roles/storage.objectViewer"              = [google_service_account.workflow_sa.member],
    "roles/storage.objectCreator"             = [google_service_account.workflow_sa.member],
    "roles/storage.insightsCollectorService"  = [google_service_account.workflow_sa.member],
    "roles/cloudtranslate.user"               = [google_service_account.workflow_sa.member],
  }
  depends_on = [
    google_project_service.translate,
    google_service_account.workflow_sa,
    google_kms_crypto_key_iam_member.translate_cmek,
    google_kms_crypto_key_iam_member.workflows_cmek,
  ]
}