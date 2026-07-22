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
locals {
  zone = "${var.region}-a"

  ntp_server_cidrs = [for s in var.ntp_servers : "${s}/32"]

  chrony_server_lines = join("\n", [
    for s in var.ntp_servers : "server ${s} iburst maxpoll 6"
  ])

  chrony_allow_lines = join("\n", [
    for c in var.allowed_client_ranges : "allow ${c}"
  ])

  startup_script = templatefile("${path.module}/startup-script.tpl", {
    server_lines = local.chrony_server_lines
    allow_lines  = local.chrony_allow_lines
  })
}

module "ntp-relay-sa" {
  source       = "../../../../modules/iam-service-account"
  project_id   = var.hub_project_id
  name         = "ntp-relay"
  display_name = "NTP relay service account."
  prefix       = var.prefix
  iam          = {}
}

module "ntp-relay" {
  source        = "../../../../modules/compute-vm"
  project_id    = var.hub_project_id
  zone          = local.zone
  name          = var.instance_name_prefix
  instance_type = var.machine_type
  tags          = ["ntp-relay"]

  boot_disk = {
    initialize_params = {
      image = var.boot_disk_image
      size  = var.boot_disk_size
    }
  }

  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  encryption = var.encryption_key == null ? null : {
    kms_key_self_link = var.encryption_key
  }

  network_interfaces = [{
    network    = var.network
    subnetwork = var.subnetwork
  }]

  service_account = {
    email = module.ntp-relay-sa.email
  }

  metadata = {
    startup-script         = local.startup_script
    block-project-ssh-keys = "true"
    serial-port-enable     = "false"
  }
}

resource "google_compute_firewall" "ntp-relay-egress-upstream" {
  project   = var.hub_project_id
  name      = "ntp-relay-egress-upstream"
  network   = var.network
  direction = "EGRESS"
  priority  = 500

  target_tags        = ["ntp-relay"]
  destination_ranges = local.ntp_server_cidrs

  allow {
    protocol = "udp"
    ports    = ["123"]
  }

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "ntp-relay-egress-deny" {
  project   = var.hub_project_id
  name      = "ntp-relay-egress-deny"
  network   = var.network
  direction = "EGRESS"
  priority  = 65534

  target_tags        = ["ntp-relay"]
  destination_ranges = ["0.0.0.0/0"]

  deny {
    protocol = "all"
  }

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "ntp-relay-ingress-clients" {
  project   = var.hub_project_id
  name      = "ntp-relay-ingress-clients"
  network   = var.network
  direction = "INGRESS"
  priority  = 500

  target_tags   = ["ntp-relay"]
  source_ranges = var.allowed_client_ranges

  allow {
    protocol = "udp"
    ports    = ["123"]
  }

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

module "ntp-relay-nat" {
  count          = var.create_cloud_nat ? 1 : 0
  source         = "../../../../modules/net-cloudnat"
  project_id     = var.hub_project_id
  region         = var.region
  name           = "ntp-relay-nat"
  router_network = var.network
  router_create  = true
  router_name    = "ntp-relay-router"

  config_source_subnetworks = {
    all = false
    subnetworks = [{
      self_link  = var.subnetwork
      all_ranges = true
    }]
  }
}
