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

resource "google_service_account" "workstation_config_key_user" {
  project      = var.main_project_id
  account_id   = "workstation-config-kms"
  display_name = "Workstation Config Service Account"
}

resource "google_kms_crypto_key_iam_member" "workstations_sa_kms_permissions" {
  crypto_key_id = local.key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.workstation_config_key_user.email}"
}

resource "google_project_iam_member" "network_user" {
  project    = var.network_project_id
  role       = "roles/compute.networkUser"
  member     = local.workstation_default_sa
  depends_on = [google_project_service.workstations]
}

resource "google_project_iam_member" "artifact_registry_reader" {
  project    = var.main_project_id
  role       = "roles/artifactregistry.reader"
  member     = local.compute_default_sa
  depends_on = [google_project_service.workstations]
}