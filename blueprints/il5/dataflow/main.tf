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

resource "google_project_service_identity" "dataflow_agent" {
  provider = google-beta
  project  = var.main_project_id
  service  = "dataflow.googleapis.com"
}

resource "google_project_service" "dataflow_api" {
  project            = var.main_project_id
  service            = "dataflow.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "dataflow_worker" {
  account_id   = var.main_project_id
  display_name = "Dataflow Worker Storage Account"
}

resource "google_compute_firewall" "dataflow" {
  name    = var.firewall_name
  network = data.google_compute_network.network.id
  project = var.network_project_id
  allow {
    protocol = "tcp"
    ports    = var.allowed_firewall_ports
  }
  source_ranges = var.allowed_source_ranges
}

resource "google_compute_subnetwork_iam_member" "dataflow_sa_compute_network_user" {
  subnetwork = data.google_compute_subnetwork.subnetwork.id
  role       = "roles/compute.networkUser"
  member     = google_project_service_identity.dataflow_agent.member
}

resource "google_kms_crypto_key_iam_member" "compute_system_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
}

resource "google_kms_crypto_key_iam_member" "dataflow_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.dataflow_agent.member
}

resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
}

module "gcs" {
  source         = "../../../modules/gcs"
  prefix         = var.prefix
  project_id     = var.main_project_id
  location       = var.region
  storage_class  = var.storage_class
  encryption_key = data.google_kms_crypto_key.default.id
  name           = var.bucket_name

  iam = {
    "roles/storage.objectUser" = concat(
      [
        "serviceAccount:${google_service_account.dataflow_worker.email}"
      ]
    )
  }
  force_destroy = true
  depends_on    = [google_kms_crypto_key_iam_member.gcs_sa_kms_access]
}

resource "google_project_iam_member" "dataflow_worker" {
  project = var.main_project_id
  role    = "roles/dataflow.worker"
  member  = "serviceAccount:${google_service_account.dataflow_worker.email}"
}

resource "google_dataflow_job" "job" {
  project = var.main_project_id
  name    = var.dataflow_name
  region  = var.region
  zone    = var.zone

  template_gcs_path = var.template_gcs_path
  temp_gcs_location = "gs://${module.gcs.bucket.name}/temp"

  # CIS Compliance Benchmark 4.1
  # CIS Compliance Benchmark 4.2
  service_account_email = google_service_account.dataflow_worker.email

  parameters = var.parameters

  network    = var.network_project_id
  subnetwork = data.google_compute_subnetwork.subnetwork.self_link

  ip_configuration = "WORKER_IP_PRIVATE" # Required for IL5

  kms_key_name = data.google_kms_crypto_key.default.id

  depends_on = [module.gcs, google_project_iam_member.dataflow_worker, google_kms_crypto_key_iam_member.dataflow_sa_kms_access]
}