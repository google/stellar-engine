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

resource "google_project_service" "spanner_api" {
  project            = var.main_project_id
  service            = "spanner.googleapis.com"
  disable_on_destroy = false
}

# The Spanner service agent exists only after this call, and the key grant
# below needs its email.
resource "google_project_service_identity" "spanner" {
  provider = google-beta
  count    = var.kms_key_name == null ? 0 : 1
  project  = var.main_project_id
  service  = "spanner.googleapis.com"

  depends_on = [google_project_service.spanner_api]
}

resource "google_kms_crypto_key_iam_member" "spanner_cmek" {
  count         = var.kms_key_name == null ? 0 : 1
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.spanner[0].member
}

moved {
  from = module.cloud_spanner
  to   = module.cloud-spanner
}

module "cloud-spanner" {
  source     = "../../../modules/spanner-instance-se"
  project_id = var.main_project_id
  edition    = var.edition
  instance = {
    name         = var.instance_name
    display_name = var.display_name
    config = {
      name = var.config_name
    }
    autoscaling = {
      limits = {
        min_processing_units = var.min_processing_units
        max_processing_units = var.max_processing_units
      }
      targets = {
        high_priority_cpu_utilization_percent = var.high_priority_cpu_utilization_percent
        storage_utilization_percent           = var.storage_utilization_percent
      }
    }
  }

  databases = {
    (var.database_name) = {
      iam = {
        "roles/spanner.databaseUser" = [
          var.database_user
        ]
      }
      kms_key_name = var.kms_key_name
    }
  }

  # Spanner rejects a database whose key the service agent cannot use, so the
  # key grant completes before the module creates the database.
  depends_on = [
    google_project_service.spanner_api,
    google_kms_crypto_key_iam_member.spanner_cmek,
  ]
}