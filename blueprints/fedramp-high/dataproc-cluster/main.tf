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
data "google_project" "current" {
  project_id = var.main_project_id
}

data "google_project" "landing_project" {
  project_id = var.network_project_id
}

data "google_project" "core_project" {
  project_id = var.core_project_id
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

resource "google_project_service" "dataproc_api" {
  project            = var.main_project_id
  service            = "dataproc.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "dataproc_vm" {
  account_id   = "dp-${var.main_project_id}"
  display_name = "Dataproc Worker Service Account"
}

resource "google_compute_firewall" "dataproc" {
  project = var.network_project_id
  name    = var.firewall_name
  network = data.google_compute_network.network.self_link
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
  source_ranges = ["10.128.0.0/9"]
}

module "gcs" {
  source         = "../../../modules/gcs"
  prefix         = "tmp"
  project_id     = var.main_project_id
  location       = var.region
  storage_class  = "STANDARD"
  encryption_key = data.google_kms_crypto_key.default.id
  name           = var.dataproc_bucket_name

  iam = {
    "roles/storage.objectViewer" = concat(
      [
        google_service_account.dataproc_vm.member
      ]
    )
    "roles/storage.objectCreator" = concat(
      [
        google_service_account.dataproc_vm.member
      ]
    )
  }

  force_destroy = true

  depends_on = [
    google_kms_crypto_key_iam_binding.dataproc_kms
  ]
}

module "dataproc_cluster" {
  source     = "../../../modules/dataproc"
  project_id = var.main_project_id
  name       = var.dataproc_cluster_name
  region     = var.region
  dataproc_config = {
    cluster_config = {
      encryption_config = {
        kms_key_name = data.google_kms_crypto_key.default.id
      }

      staging_bucket = module.gcs.name
      temp_bucket    = module.gcs.name
      gce_cluster_config = {
        internal_ip_only       = true
        service_account        = google_service_account.dataproc_vm.email
        service_account_scopes = ["cloud-platform"]
        subnetwork             = data.google_compute_subnetwork.subnetwork.id
        tags                   = ["dataproc"]
        zone                   = "${var.region}-c"
      }
    }
  }
  depends_on = [
    google_kms_crypto_key_iam_binding.dataproc_kms
  ]
}
