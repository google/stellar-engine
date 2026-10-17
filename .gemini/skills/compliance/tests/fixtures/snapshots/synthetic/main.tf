# Copyright 2026 Google LLC
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

# Synthetic multi-resource fixture for characterization snapshots.

resource "google_compute_network" "core" {
  name                    = "core-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "app" {
  name          = "app-subnet"
  network       = google_compute_network.core.id
  region        = "us-east4"
  ip_cidr_range = "10.10.0.0/24"
}

resource "google_compute_firewall" "public_icmp" {
  name          = "allow-icmp-public"
  network       = google_compute_network.core.name
  direction     = "INGRESS"
  source_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "icmp"
  }
}

resource "google_compute_firewall" "internal_https" {
  name          = "allow-internal-https"
  network       = google_compute_network.core.name
  direction     = "INGRESS"
  source_ranges = ["10.10.0.0/24"]
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

resource "google_compute_firewall" "deny_all" {
  name          = "deny-all-ingress"
  network       = google_compute_network.core.name
  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]
  deny {
    protocol = "all"
  }
}

resource "google_compute_instance" "bastion" {
  name         = "bastion-vm"
  machine_type = "e2-small"
  zone         = "us-east4-a"
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }
  network_interface {
    subnetwork = google_compute_subnetwork.app.id
  }
}

resource "google_container_cluster" "gke" {
  name               = "app-cluster"
  location           = "us-east4"
  network            = google_compute_network.core.id
  subnetwork         = google_compute_subnetwork.app.id
  initial_node_count = 1
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = true
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
}

resource "google_sql_database_instance" "db" {
  name             = "app-db"
  database_version = "POSTGRES_15"
  region           = "us-east4"
  settings {
    tier = "db-custom-2-7680"
    ip_configuration {
      ipv4_enabled = false
    }
  }
}

resource "google_kms_key_ring" "ring" {
  name     = "app-ring"
  location = "us-east4"
}

resource "google_kms_crypto_key" "hsm_key" {
  name     = "hsm-sign-key"
  key_ring = google_kms_key_ring.ring.id
  purpose  = "ASYMMETRIC_SIGN"
  version_template {
    algorithm        = "EC_SIGN_P256_SHA256"
    protection_level = "HSM"
  }
}

resource "google_kms_crypto_key" "software_key" {
  name     = "software-data-key"
  key_ring = google_kms_key_ring.ring.id
  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "SOFTWARE"
  }
}

resource "google_storage_bucket" "logs" {
  name                        = "app-logs-bucket"
  location                    = "US-EAST4"
  uniform_bucket_level_access = true
}

resource "google_cloud_run_v2_service" "api" {
  name     = "api-service"
  location = "us-east4"
  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      ports {
        container_port = 8080
      }
    }
  }
}
