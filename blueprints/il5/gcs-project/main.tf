/**
 * Copyright 2023 Google LLC
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

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.region
  project  = var.core_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

resource "google_project_service" "storage_api" {
  project            = var.main_project_id
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

data "google_storage_project_service_account" "gcs_sa" {
  project    = var.main_project_id
  depends_on = [google_project_service.storage_api]
}

resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = data.google_storage_project_service_account.gcs_sa.member
}

module "gcs" {
  source         = "../../../modules/gcs"
  prefix         = var.prefix
  project_id     = var.main_project_id
  location       = var.region
  autoclass      = var.autoclass
  storage_class  = var.storage_class
  encryption_key = data.google_kms_crypto_key.default.id
  name           = var.bucket_name

  # CIS Compliance Benchmark 5.1
  public_access_prevention = var.public_access_prevention

  # CIS Compliance Benchmark 5.2
  uniform_bucket_level_access = var.uniform_bucket_level_access

  retention_policy = var.retention_policy
  depends_on = [
    google_kms_crypto_key_iam_member.gcs_sa_kms_access,
    google_project_service.storage_api,
  ]
}

