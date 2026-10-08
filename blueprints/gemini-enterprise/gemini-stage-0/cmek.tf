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

locals {
  # Final CMEK Key ID - Only explicitly set if we are enabling Data Store CMEK
  cmek_key_id = var.enable_data_store_cmek ? var.kms_key_id : null
}

# ---------------------------------------------------------------------------- #
# 1. IAM Bindings
# ---------------------------------------------------------------------------- #

# Grant Discovery Engine Service Agent access
resource "google_kms_crypto_key_iam_member" "discoveryengine_sa_kms_access" {
  count         = var.enable_data_store_cmek ? 1 : 0
  crypto_key_id = local.cmek_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"

  depends_on = [
    google_project_service_identity.discoveryengine,
    time_sleep.wait_for_services
  ]
}

# Grant Cloud Storage Service Agent access
resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access" {
  count         = var.enable_data_store_cmek ? 1 : 0
  crypto_key_id = local.cmek_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"

  depends_on = [
    google_project_service_identity.storage,
    time_sleep.wait_for_services
  ]
}

# Grant BigQuery Service Agent access
resource "google_kms_crypto_key_iam_member" "bq_sa_kms_access" {
  count         = var.enable_data_store_cmek ? 1 : 0
  crypto_key_id = local.cmek_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:bq-${data.google_project.project.number}@bigquery-encryption.iam.gserviceaccount.com"

  depends_on = [
    google_project_service_identity.bigquery,
    time_sleep.wait_for_services
  ]
}
