/**
 * Copyright 2024 Google LLC
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

data "google_project" "current" {}

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

resource "google_service_account" "compute" {
  account_id = var.compute_service_account_id
  project    = var.main_project_id
}

resource "google_compute_firewall" "default" {
  project = var.network_project_id
  name    = "allow-web"
  network = data.google_compute_network.network.self_link
  allow {
    protocol = "tcp"
    ports    = var.allowed_firewall_ports
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
  source_ranges = var.allowed_source_ranges
}

module "bastion-vm" {
  source     = "../../../modules/compute-vm"
  project_id = var.main_project_id
  zone       = var.zone
  name       = var.instance_name

  confidential_compute = true # CIS Compliance Benchmark 4.11 - Must use compliant instance and image types

  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
  }

  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  instance_type = var.instance_type
  network_interfaces = [{
    network    = data.google_compute_network.network.self_link
    subnetwork = data.google_compute_subnetwork.subnetwork.self_link
  }]

  # CIS Compliance Benchmark 4.1
  # CIS Compliance Benchmark 4.2
  service_account = {
    email = google_service_account.compute.email
  }
  encryption = {
    kms_key_self_link = data.google_kms_crypto_key.default.id
  }
  snapshot_schedules = {
    daily-backup = {
      schedule = {
        daily = {
          days_in_cycle = 1
          start_time    = "04:00"
        }
      }
      retention_policy = {
        max_retention_days = 14
      }
    }
  }

  attached_disks = [
    {
      auto_delete = true
      size        = 10
      name        = var.disk_name
      snapshot_schedule = ["daily-backup"]
      initialize_params = {
        image = var.image
      }
      kms_key_self_link = data.google_kms_crypto_key.default.id
    }
  ]

  boot_disk = {
    snapshot_schedule = ["daily-backup"]
    initialize_params = {
      image = var.image
    }
  }
  depends_on = [
    google_kms_crypto_key_iam_member.bastion_sa_kms_access
  ]
}

resource "google_kms_crypto_key_iam_member" "bastion_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.compute.member
}

resource "google_kms_crypto_key_iam_member" "crypto_key" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
}