/**
 * Copyright 2022 Google LLC
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

data "google_compute_default_service_account" "default" {
  project = data.google_project.project.project_id
}

data "google_compute_zones" "available" {
  region  = var.region
  project = data.google_project.project.project_id
  status  = "UP"
}
data "google_compute_subnetwork" "default" {
  name    = var.subnetwork_name
  project = var.net_project
}

data "google_compute_subnetwork" "proxy" {
  name    = "${var.env}-${var.region}-proxy-0"
  project = var.net_project
}

# Custom service account with compute engine role
resource "google_service_account" "compute" {
  account_id = "cnap-app-compute-sa"
  project    = data.google_project.project.project_id
}

# Demo App config
module "cos-demo-config" {
  source          = "../../../modules/cloud-config-container/cos-generic-metadata"
  for_each        = local.vms
  container_image = each.value.container_image
  container_name  = "demo"
  docker_args     = "--publish 8080:8080"
  run_commands    = ["systemctl daemon-reload", "systemctl start demo", ]
}

resource "google_compute_region_instance_template" "cos-template" {
  for_each     = local.vms
  project      = data.google_project.project.project_id
  name_prefix  = "${var.prefix}-template-${each.key}"
  region       = var.region
  machine_type = var.machine_type

  tags = ["${var.prefix}-ids"]
  network_interface {
    network    = data.google_compute_network.network.id
    subnetwork = data.google_compute_subnetwork.default.self_link
  }
  // Create a new boot disk from an image
  disk {
    source_image = "cos-cloud/cos-stable"
    type         = "PERSISTENT"
    disk_encryption_key {
      kms_key_self_link = module.kms.keys.default.id
    }
  }

  metadata = {
    user-data = module.cos-demo-config[each.key].cloud_config
  }
  # CIS Compliance Benchmark 4.1
  # CIS Compliance Benchmark 4.2
  service_account {
    email  = google_service_account.compute.email
    scopes = ["cloud-platform"]
  }

  # CIS Compliance Benchmark 4.11
  confidential_instance_config {
    enable_confidential_compute = false # This is rejecting my instance type, n2d-highcpu-2 which is supported. I think it's a bug
  }
  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_region_health_check" "http-region-health-check" {
  for_each = local.vms
  project  = data.google_project.project.project_id

  name = "${var.prefix}-app-healthcheck-${each.key}"

  timeout_sec        = 5
  check_interval_sec = 20

  http_health_check {
    port = "8080"
  }
}

module "cos-mig" {
  for_each          = local.vms
  source            = "../../../modules/compute-mig"
  project_id        = data.google_project.project.project_id
  location          = var.region
  name              = "${var.prefix}-cos-${each.key}"
  instance_template = google_compute_region_instance_template.cos-template[each.key].self_link
  target_size       = 1
  auto_healing_policies = {
    health_check      = google_compute_region_health_check.http-region-health-check[each.key].self_link
    initial_delay_sec = 60
  }

  named_ports = {
    http = 8080
  }
  update_policy = {
    minimal_action = "REPLACE"
    type           = "PROACTIVE"
    min_ready_sec  = 300
    max_surge = {
      fixed = length(data.google_compute_zones.available)
    }
    max_unavailable = {
      fixed = 0
    }
  }
}

# Google KMS Module
module "kms" {
  source     = "../../../modules/kms"
  project_id = data.google_project.project.project_id
  keys = {
    "default" = {
      rotation_period = "7776000s" # CIS Compliance Benchmark 1.10
      purpose         = "ENCRYPT_DECRYPT"
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    }
  }

  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      google_service_account.compute.member,
      data.google_compute_default_service_account.default.member
    ]
  }
  keyring = {
    location = var.region
    name     = "cnap-keyring"
  }

}

resource "google_compute_firewall" "allow-app" {
  name    = "cnap-app-firewall"
  network = data.google_compute_network.network.id

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  target_tags = ["${var.prefix}-ids"]
  source_ranges = [
    # Health Check sources
    "35.191.0.0/16",
    "130.211.0.0/22",
    "209.85.152.0/22",
    "209.85.204.0/22",
    # IAP Sources
    "35.235.240.0/20",
    data.google_compute_subnetwork.proxy.ip_cidr_range
  ]
}