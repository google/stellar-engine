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
locals {
  vpc    = "projects/${var.network_config.network_project_id}/global/networks/${var.network_config.network_name}"
  subnet = "projects/${var.network_config.network_project_id}/regions/${var.region}/subnetworks/${var.network_config.subnetwork_name}"

  prefix = var.prefix == null ? "" : "${var.prefix}-"

}

module "gcs-bucket" {
  count          = var.bucket_name == null ? 0 : 1
  source         = "../../../modules/gcs"
  project_id     = var.main_project_id
  name           = var.bucket_name
  prefix         = var.prefix
  location       = var.region
  storage_class  = "REGIONAL"
  versioning     = false
  encryption_key = var.service_encryption_keys.storage
  force_destroy  = !var.deletion_protection

  depends_on = [
    google_kms_crypto_key_iam_member.gcs_kms
  ]
}

# Default bucket for Cloud Build to prevent error: "'us' violates constraint ‘gcp.resourceLocations’"
# https://stackoverflow.com/questions/53206667/cloud-build-fails-with-resource-location-constraint
module "gcs-bucket-cloudbuild" {
  source         = "../../../modules/gcs"
  project_id     = var.main_project_id
  name           = "${var.main_project_id}_cloudbuild"
  location       = var.region
  storage_class  = "REGIONAL"
  versioning     = false
  encryption_key = var.service_encryption_keys.storage
  force_destroy  = !var.deletion_protection

  depends_on = [
    google_kms_crypto_key_iam_member.gcs_kms
  ]
}

module "bq-dataset" {
  count          = var.dataset_name == null ? 0 : 1
  source         = "../../../modules/bigquery-dataset"
  project_id     = var.main_project_id
  id             = var.dataset_name
  location       = var.region
  encryption_key = var.service_encryption_keys.bq

  depends_on = [
    google_kms_crypto_key_iam_member.bq_kms
  ]
}

data "google_project" "project" {
  project_id = var.main_project_id
}

module "service-account-mlops" {
  source     = "../../../modules/iam-service-account"
  name       = "${local.prefix}sa-mlops"
  project_id = var.main_project_id
}

resource "google_project_iam_member" "shared_vpc" {
  project = var.network_config.network_project_id
  role    = "roles/compute.networkUser"
  member  = "serviceAccount:${google_project_service_identity.notebooks.email}"
}

//add iam bindings to compute service account running notebooks
resource "google_project_iam_member" "service_permissions" {
  for_each = toset([
    "roles/notebooks.runner",
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/iam.serviceAccountUser",
    "projects/${var.main_project_id}/roles/storage_iam",
  ])
  project = var.main_project_id
  role    = each.key
  member  = "serviceAccount:${module.service-account-mlops.email}"
  depends_on = [
    module.service-account-mlops
  ]
}

resource "google_project_iam_custom_role" "storage_role" {
  role_id = "storage_iam"
  project = var.main_project_id
  title   = "Storage IAM Policy Role"
  permissions = [
    "storage.buckets.getIamPolicy",
    "storage.buckets.setIamPolicy",
  ]
}

resource "google_kms_crypto_key_iam_member" "bq_kms" {
  count         = var.service_encryption_keys.bq != null ? 1 : 0
  crypto_key_id = var.service_encryption_keys.bq
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:bq-${data.google_project.project.number}@bigquery-encryption.iam.gserviceaccount.com"
}

resource "google_kms_crypto_key_iam_member" "gcs_kms" {
  count         = var.service_encryption_keys.storage != null ? 1 : 0
  crypto_key_id = var.service_encryption_keys.storage
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
}

resource "google_project_service_identity" "notebooks" {
  provider = google-beta
  project  = var.main_project_id
  service  = "notebooks.googleapis.com"
}

resource "google_kms_crypto_key_iam_member" "notebooks_kms" {
  count         = var.service_encryption_keys.notebooks != null ? 1 : 0
  crypto_key_id = var.service_encryption_keys.notebooks
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.notebooks.email}"
}

# 4. AI Platform Service Account (P4SA)
resource "google_project_service_identity" "aiplatform" {
  provider = google-beta
  project  = var.main_project_id
  service  = "aiplatform.googleapis.com"
}

resource "google_kms_crypto_key_iam_member" "aiplatform_kms" {
  count         = var.service_encryption_keys.aiplatform != null ? 1 : 0
  crypto_key_id = var.service_encryption_keys.aiplatform
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.aiplatform.email}"

}

resource "google_kms_crypto_key_iam_member" "compute_kms" {
  count         = var.service_encryption_keys.notebooks != null ? 1 : 0
  crypto_key_id = var.service_encryption_keys.notebooks
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
}

resource "google_project_service" "aiplatform_api" {
  project            = var.main_project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "notebooks_api" {
  project            = var.main_project_id
  service            = "notebooks.googleapis.com"
  disable_on_destroy = false
}
