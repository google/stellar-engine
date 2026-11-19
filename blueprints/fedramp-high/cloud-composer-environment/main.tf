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

data "google_project" "current" {
  project_id = var.main_project_id
}

data "google_compute_network" "network" {
  name    = var.network_name
  project = var.network_project_id
}

data "google_compute_subnetwork" "subnetwork" {
  name    = var.subnetwork_name
  region  = var.region
  project = var.network_project_id
}

# Composer keeps DAGs, plugins and logs in the environment bucket, so the
# Cloud Storage service agent of the main project also uses the key.
data "google_storage_project_service_account" "gcs" {
  count   = var.kms_key_name == null ? 0 : 1
  project = var.main_project_id
}

resource "google_project_service" "cloud_composer_api" {
  project            = var.main_project_id
  service            = "composer.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service_identity" "composer_agent" {
  provider = google-beta
  project  = var.main_project_id
  service  = "composer.googleapis.com"

  depends_on = [
    google_project_service.cloud_composer_api
  ]
}

resource "google_service_account" "composer" {
  project      = var.main_project_id
  account_id   = var.sa_account_id
  display_name = var.sa_display_name
}

resource "google_composer_environment" "main" {
  provider = google-beta

  project = var.main_project_id
  name    = var.composer_env_name
  region  = var.region

  config {
    enable_private_environment = true
    software_config {
      image_version = var.composer_version
    }

    node_config {
      network         = data.google_compute_network.network.self_link
      subnetwork      = data.google_compute_subnetwork.subnetwork.self_link
      service_account = google_service_account.composer.name
    }

    dynamic "encryption_config" {
      for_each = var.kms_key_name == null ? [] : [var.kms_key_name]
      content {
        kms_key_name = encryption_config.value
      }
    }
  }

  # Composer rejects an environment whose key the service agents cannot use,
  # so both key grants complete before the environment is created.
  depends_on = [
    google_project_service.cloud_composer_api,
    google_project_iam_member.composer_worker,
    google_project_iam_member.composer_service_agent,
    google_compute_subnetwork_iam_member.composer_network_user,
    google_project_iam_member.composer_vpc_agent,
    google_kms_crypto_key_iam_member.composer_agent_cmek,
    google_kms_crypto_key_iam_member.storage_agent_cmek
  ]
}