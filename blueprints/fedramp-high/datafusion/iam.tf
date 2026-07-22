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

resource "google_service_account" "datafusion_sa" {
  project      = var.main_project_id
  account_id   = "df-${var.main_project_id}"
  display_name = "Dataproc Worker Service Account"
}

resource "google_project_iam_member" "datafusion_agent_network_user_main_project" {
  project    = var.main_project_id
  role       = "roles/compute.networkUser"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}

resource "google_project_iam_member" "datafusion_agent_network_user_network_project" {
  project    = var.network_project_id
  role       = "roles/compute.networkUser"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}

resource "google_project_iam_member" "datafusion_agent_spanner_viewer" {
  project    = var.main_project_id
  role       = "roles/spanner.viewer"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}

resource "google_kms_crypto_key_iam_member" "datafusion_agent_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on    = [time_sleep.datafusion_service_propagation]
}

resource "google_kms_crypto_key_iam_member" "datafusion_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.datafusion_sa.email}"
  depends_on    = [google_service_account.datafusion_sa]
}

resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs_account_main_project.email_address}"
}

resource "google_project_iam_member" "datafusion_service_agent" {
  project    = var.main_project_id
  role       = "roles/datafusion.serviceAgent"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}
resource "google_project_iam_member" "dataproc_service_agent" {
  project    = var.main_project_id
  role       = "roles/dataproc.serviceAgent"
  member     = "serviceAccount:${google_project_service_identity.dataproc_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}
