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
  observability_roles = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  bastion_metadata = {
    block-project-ssh-keys = true    # CIS Compliance Benchmark 4.3
    enable-oslogin         = "TRUE"  # CIS Compliance Benchmark 4.4
    serial-port-enable     = "false" # CIS Compliance Benchmark 4.5
  }
  bastion_shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  bastion_snapshot_schedules = {
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
  compute_service_agent = format(
    "serviceAccount:service-%s@compute-system.iam.gserviceaccount.com",
    data.google_project.current.number
  )
  primary_addresses = (
    var.static_internal_ip == null
    ? null
    : { internal = var.static_internal_ip }
  )
  additional_observability_iam = {
    for item in flatten([
      for k, v in var.additional_bastions : [
        for role in local.observability_roles : {
          key     = "${k}/${role}"
          bastion = k
          role    = role
        }
      ]
      if coalesce(v.enable_observability_iam, var.enable_observability_iam)
    ]) : item.key => item
  }
}

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

data "google_compute_subnetwork" "additional" {
  for_each = {
    for k, v in var.additional_bastions : k => v.subnetwork_name
    if v.subnetwork_name != null
  }
  name    = each.value
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

resource "google_project_iam_member" "bastion_observability" {
  for_each = (
    var.enable_observability_iam ? local.observability_roles : toset([])
  )
  project = var.main_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.compute.email}"
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
  # Target the bastion service account so the rule does not apply to
  # every instance in the shared network.
  target_service_accounts = [google_service_account.compute.email]
  source_ranges           = var.allowed_source_ranges
}

module "bastion-vm" {
  source     = "../../../modules/compute-vm"
  project_id = var.main_project_id
  zone       = var.zone
  name       = var.instance_name

  # CIS Compliance Benchmark 4.11 requires compliant instance and image types.
  confidential_compute = "SEV"
  metadata             = local.bastion_metadata
  shielded_config      = local.bastion_shielded_config
  machine_type         = var.instance_type
  network_interfaces = [{
    network    = data.google_compute_network.network.self_link
    subnetwork = data.google_compute_subnetwork.subnetwork.self_link
    addresses  = local.primary_addresses
  }]

  # CIS Compliance Benchmark 4.1
  # CIS Compliance Benchmark 4.2
  service_account = {
    email = google_service_account.compute.email
  }
  encryption = {
    kms_key_self_link = data.google_kms_crypto_key.default.id
  }
  snapshot_schedules = local.bastion_snapshot_schedules

  attached_disks = {
    (var.disk_name) = {
      auto_delete       = true
      snapshot_schedule = ["daily-backup"]
      initialize_params = {
        size = 10
      }
    }
  }

  boot_disk = {
    snapshot_schedule = ["daily-backup"]
    source = {
      image = var.image
    }
  }
  depends_on = [
    google_kms_crypto_key_iam_member.crypto_key
  ]
}

resource "google_service_account" "additional" {
  for_each   = var.additional_bastions
  account_id = each.value.compute_service_account_id
  project    = var.main_project_id
}

resource "google_project_iam_member" "additional_observability" {
  for_each = local.additional_observability_iam
  project  = var.main_project_id
  role     = each.value.role
  member = format(
    "serviceAccount:%s",
    google_service_account.additional[each.value.bastion].email
  )
}

resource "google_compute_firewall" "additional" {
  for_each = var.additional_bastions
  project  = var.network_project_id
  name     = coalesce(each.value.firewall_name, "allow-bastion-${each.key}")
  network  = data.google_compute_network.network.self_link
  allow {
    protocol = "tcp"
    ports = (
      each.value.allowed_firewall_ports != null
      ? each.value.allowed_firewall_ports
      : var.allowed_firewall_ports
    )
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
  target_service_accounts = [
    google_service_account.additional[each.key].email
  ]
  source_ranges = (
    each.value.allowed_source_ranges != null
    ? each.value.allowed_source_ranges
    : var.allowed_source_ranges
  )
}

module "additional-bastion-vm" {
  for_each   = var.additional_bastions
  source     = "../../../modules/compute-vm"
  project_id = var.main_project_id
  zone       = coalesce(each.value.zone, var.zone)
  name       = coalesce(each.value.instance_name, each.key)

  confidential_compute = "SEV"
  metadata             = local.bastion_metadata
  shielded_config      = local.bastion_shielded_config
  machine_type         = coalesce(each.value.instance_type, var.instance_type)
  network_interfaces = [{
    network = data.google_compute_network.network.self_link
    subnetwork = (
      each.value.subnetwork_name == null
      ? data.google_compute_subnetwork.subnetwork.self_link
      : data.google_compute_subnetwork.additional[each.key].self_link
    )
    addresses = (
      each.value.static_internal_ip == null
      ? null
      : { internal = each.value.static_internal_ip }
    )
  }]

  service_account = {
    email = google_service_account.additional[each.key].email
  }
  encryption = {
    kms_key_self_link = data.google_kms_crypto_key.default.id
  }
  snapshot_schedules = local.bastion_snapshot_schedules

  attached_disks = {
    (coalesce(each.value.disk_name, var.disk_name)) = {
      auto_delete       = true
      snapshot_schedule = ["daily-backup"]
      initialize_params = {
        size = 10
      }
    }
  }

  boot_disk = {
    snapshot_schedule = ["daily-backup"]
    source = {
      image = coalesce(each.value.image, var.image)
    }
  }
  depends_on = [
    google_kms_crypto_key_iam_member.crypto_key
  ]
}

resource "google_kms_crypto_key_iam_member" "crypto_key" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = local.compute_service_agent
}
