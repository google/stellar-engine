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

  disa_relay_cidrs = [for s in var.disa_relay_hosts : "${s}/32"]

  startup_script = templatefile("${path.module}/startup-script.tpl", {
    smtp_hostname    = var.smtp_hostname
    smtp_domain      = var.smtp_domain
    disa_relay_host  = var.disa_relay_hosts[0]
    disa_relay_port  = var.disa_relay_port
    allowed_networks = join(" ", var.allowed_client_ranges)
  })
}

module "smtp-relay-sa" {
  source       = "../../../../modules/iam-service-account"
  project_id   = var.hub_project_id
  name         = "smtp-relay"
  display_name = "SMTP relay service account."
  prefix       = var.prefix
  iam          = {}
}

module "smtp-relay" {
  source        = "../../../../modules/compute-vm"
  project_id    = var.hub_project_id
  zone          = local.zone
  name          = var.instance_name_prefix
  instance_type = var.machine_type
  tags          = ["smtp-relay"]

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
    email = module.smtp-relay-sa.email
  }

  metadata = {
    startup-script         = local.startup_script
    block-project-ssh-keys = "true"
    serial-port-enable     = "false"
  }
}

resource "google_compute_firewall" "smtp-relay-egress-disa" {
  project   = var.hub_project_id
  name      = "smtp-relay-egress-disa"
  network   = var.network
  direction = "EGRESS"
  priority  = 500

  target_tags        = ["smtp-relay"]
  destination_ranges = local.disa_relay_cidrs

  allow {
    protocol = "tcp"
    ports    = [tostring(var.disa_relay_port)]
  }

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "smtp-relay-egress-rhui" {
  project   = var.hub_project_id
  name      = "smtp-relay-egress-rhui"
  network   = var.network
  direction = "EGRESS"
  priority  = 500

  target_tags        = ["smtp-relay"]
  destination_ranges = ["35.190.247.13/32"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "smtp-relay-egress-deny" {
  project   = var.hub_project_id
  name      = "smtp-relay-egress-deny"
  network   = var.network
  direction = "EGRESS"
  priority  = 65534

  target_tags        = ["smtp-relay"]
  destination_ranges = ["0.0.0.0/0"]

  deny {
    protocol = "all"
  }

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "smtp-relay-ingress-clients" {
  project   = var.hub_project_id
  name      = "smtp-relay-ingress-clients"
  network   = var.network
  direction = "INGRESS"
  priority  = 500

  target_tags   = ["smtp-relay"]
  source_ranges = var.allowed_client_ranges

  allow {
    protocol = "tcp"
    ports    = ["25"]
  }

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

module "smtp-relay-nat" {
  count          = var.create_cloud_nat ? 1 : 0
  source         = "../../../../modules/net-cloudnat"
  project_id     = var.hub_project_id
  region         = var.region
  name           = "smtp-relay-nat"
  router_network = var.network
  router_create  = true
  router_name    = "smtp-relay-router"

  config_source_subnetworks = {
    all = false
    subnetworks = [{
      self_link  = var.subnetwork
      all_ranges = true
    }]
  }
}
