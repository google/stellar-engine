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
data "google_project" "core_project" {
  project_id = var.core_project_id
}

resource "google_service_account" "cloud_build_sa" {
  account_id   = "cloud-build-sa"
  project      = var.core_project_id
  display_name = "Devops Cloud Build Service Account"
}

resource "google_project_iam_member" "build_sa_core_roles" {
  for_each = toset(var.cloud_build_core_roles)
  project  = var.core_project_id
  role     = each.key
  member   = google_service_account.cloud_build_sa.member
}

resource "google_project_iam_member" "build_sa_main_roles" {
  for_each = toset(var.terraform_apply_roles)
  project  = var.main_project_id
  role     = each.key
  member   = google_service_account.cloud_build_sa.member
}

resource "google_storage_bucket_iam_member" "cloud_build_source_reader" {
  bucket = module.cloud-build-source-gcs.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.cloud_build_sa.email}"
  depends_on = [
    module.cloud-build-source-gcs
  ]
}

resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access" {
  crypto_key_id = module.gcs-kms.keys.gcs.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.core_project.number}@gs-project-accounts.iam.gserviceaccount.com"
}
