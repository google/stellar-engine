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

data "google_project" "project" {
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

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.region
  project  = var.core_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

data "google_storage_project_service_account" "gcs_account_main_project" {
  project = var.main_project_id
}

resource "google_project_service" "datafusion_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "datafusion.googleapis.com",
    "dataproc.googleapis.com",
  ])

  project            = var.main_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service_identity" "datafusion_agent" {
  provider = google-beta
  project  = var.main_project_id
  service  = "datafusion.googleapis.com"

  depends_on = [
    google_project_service.datafusion_apis
  ]
}

resource "google_project_service_identity" "dataproc_agent" {
  provider = google-beta
  project  = var.main_project_id
  service  = "dataproc.googleapis.com"

  depends_on = [
    google_project_service.datafusion_apis
  ]
}

resource "time_sleep" "datafusion_service_propagation" {
  create_duration = "3m"

  depends_on = [
    google_project_service_identity.datafusion_agent,
    google_project_service_identity.dataproc_agent
  ]
}

module "datafusion" {
  source                   = "../../../modules/datafusion-se"
  name                     = var.name
  region                   = var.region
  project_id               = var.main_project_id
  network                  = data.google_compute_network.network.self_link
  subnet                   = data.google_compute_subnetwork.subnetwork.self_link
  firewall_create          = false
  landing_project_id       = var.network_project_id
  dataproc_service_account = google_service_account.datafusion_sa.email
  private_instance         = true
  kms_key                  = data.google_kms_crypto_key.default.id
  ip_allocation_create     = false
  network_peering          = false

  depends_on = [
    google_project_service.datafusion_apis,
    google_project_iam_member.datafusion_agent_network_user_main_project,
    google_project_iam_member.datafusion_agent_network_user_network_project,
    google_project_iam_member.datafusion_agent_spanner_viewer,
    google_project_iam_member.datafusion_service_agent,
    google_project_iam_member.dataproc_service_agent,
    google_kms_crypto_key_iam_member.datafusion_agent_kms_access,
    google_kms_crypto_key_iam_member.datafusion_sa_kms_access,
    google_kms_crypto_key_iam_member.gcs_sa_kms_access,
    time_sleep.datafusion_service_propagation
  ]
}
