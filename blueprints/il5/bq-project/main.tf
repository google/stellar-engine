/**
 * Copyright 2024 Google LLC
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

resource "google_project_service" "bigquery_api" {
  project            = var.main_project_id
  service            = "bigquery.googleapis.com"
  disable_on_destroy = false
}

data "google_bigquery_default_service_account" "bq_sa" {
  project = var.main_project_id
  depends_on = [
    google_project_service.bigquery_api
  ]
}

module "bigquery-dataset" {
  source         = "../../../modules/bigquery-dataset"
  location       = var.region
  project_id     = var.main_project_id
  id             = var.dataset_id
  encryption_key = module.kms.keys.default.id
  description    = var.dataset_description
  tables         = var.tables
  depends_on = [
    module.kms,
    google_project_service.bigquery_api,
  ]
}

#Google KMS Module
module "kms" {
  source     = "../../../modules/kms"
  project_id = var.main_project_id
  keys       = var.kms_key_names
  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [data.google_bigquery_default_service_account.bq_sa.member]
  }
  keyring = var.kms_keyring_name
}
