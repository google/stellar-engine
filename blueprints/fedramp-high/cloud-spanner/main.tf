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

moved {
  from = module.cloud_spanner
  to   = module.cloud-spanner
}

module "cloud-spanner" {
  source       = "../../../modules/spanner-instance-se"
  project_id   = var.main_project_id
  edition      = var.edition
  kms_key_name = var.kms_key_name
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
    }
  }

  depends_on = [google_project_service.spanner_api]
}

# Grant Spanner service identity access to CMEK key when provided
resource "google_project_service_identity" "spanner" {
  provider = google-beta
  project  = var.main_project_id
  service  = "spanner.googleapis.com"
  count    = var.kms_key_name != null ? 1 : 0
}

resource "google_kms_crypto_key_iam_member" "spanner_sa_kms_access" {
  count         = var.kms_key_name != null ? 1 : 0
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.spanner[0].member
}