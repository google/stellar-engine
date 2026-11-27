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

resource "google_project_service" "datastore_api" {
  project            = var.main_project_id
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service_identity" "firestore" {
  count      = var.kms_key_name == null ? 0 : 1
  provider   = google-beta
  project    = var.main_project_id
  service    = "firestore.googleapis.com"
  depends_on = [google_project_service.datastore_api]
}

resource "time_sleep" "firestore_agent_propagation" {
  count           = var.kms_key_name == null ? 0 : 1
  create_duration = "60s"
  depends_on      = [google_project_service_identity.firestore]
}

resource "google_kms_crypto_key_iam_member" "firestore_cmek" {
  count         = var.kms_key_name == null ? 0 : 1
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.firestore[0].member
  depends_on    = [time_sleep.firestore_agent_propagation]
}

module "firestore" {
  source     = "../../../modules/firestore"
  project_id = var.main_project_id
  database = {
    name            = var.firestore_database_name
    location_id     = var.region
    type            = "FIRESTORE_NATIVE"
    deletion_policy = "DELETE"
    kms_key_name    = var.kms_key_name
  }

  backup_schedule = var.backup_schedule

  depends_on = [
    google_project_service.datastore_api,
    google_kms_crypto_key_iam_member.firestore_cmek,
  ]
}