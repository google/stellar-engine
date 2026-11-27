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

resource "google_project_service_identity" "documentai_sa" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "documentai.googleapis.com"
  depends_on = [google_project_service.documentai]
}

resource "google_project_service_identity" "workflows_sa" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "workflows.googleapis.com"
  depends_on = [google_project_service.documentai]
}

# storage.googleapis.com has no primary service identity via
# serviceusage.services.generateServiceIdentity, so look up the GCS agent.
data "google_storage_project_service_account" "gcs_sa" {
  project    = var.main_project_id
  depends_on = [google_project_service.documentai]
}

# IAM does not recognize newly created service agents right away, so a short
# propagation wait prevents first-apply KMS IAM grant failures.
resource "time_sleep" "service_agent_propagation" {
  create_duration = "60s"

  depends_on = [
    google_project_service_identity.documentai_sa,
    google_project_service_identity.workflows_sa,
    data.google_storage_project_service_account.gcs_sa,
  ]
}

resource "google_kms_crypto_key_iam_member" "documentai_cmek" {
  crypto_key_id = var.processor_kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.documentai_sa.member

  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_kms_crypto_key_iam_member" "gcs_cmek" {
  crypto_key_id = var.regional_kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = data.google_storage_project_service_account.gcs_sa.member

  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_kms_crypto_key_iam_member" "workflows_cmek" {
  crypto_key_id = var.regional_kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.workflows_sa.member

  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_service_account" "workflow_sa" {
  project      = var.main_project_id
  account_id   = "docai-workflow-sa"
  display_name = "Workflows Service Account."
}