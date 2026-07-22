/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
data "google_bigquery_default_service_account" "bq_sa" {
  depends_on = [
    google_project_service.bigquery_api
  ]
}

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.region
  project  = var.core_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

resource "google_project_service" "bigquery_api" {
  project            = var.main_project_id
  service            = "bigquery.googleapis.com"
  disable_on_destroy = false
}

module "bigquery-dataset" {
  source         = "../../../modules/bigquery-dataset"
  location       = var.region
  project_id     = var.main_project_id
  id             = var.dataset_id
  encryption_key = data.google_kms_crypto_key.default.id
  description    = var.dataset_description
  tables         = var.tables
  depends_on = [
    google_kms_crypto_key_iam_member.bq_sa_kms_access,
    google_project_service.bigquery_api
  ]
}

resource "google_kms_crypto_key_iam_member" "bq_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = data.google_bigquery_default_service_account.bq_sa.member
}