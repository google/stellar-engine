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

data "google_project" "current" {
  project_id = var.shared_services_project_id
}

data "google_compute_network" "network" {
  name    = split("/", var.network)[length(split("/", var.network)) - 1]
  project = var.hub_project_id
}

data "google_compute_image" "sc_golden" {
  family  = "acas-sc-golden"
  project = var.shared_services_project_id
}


locals {
  prefix             = var.prefix == null ? "" : "${var.prefix}-"
  compute_agent_sa   = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
  compute_default_sa = "${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

# --- KMS Key Lookup ---

data "google_kms_key_ring" "default" {
  name     = "${local.prefix}acas-keyring-${var.region}"
  location = var.region
  project  = var.shared_services_project_id
}

data "google_kms_crypto_key" "default" {
  name     = "acas"
  key_ring = data.google_kms_key_ring.default.id
}

# --- Project Services ---

resource "google_project_service" "services" {
  for_each = toset([
    "compute.googleapis.com",
    "cloudkms.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com"
  ])
  project            = var.shared_services_project_id
  service            = each.value
  disable_on_destroy = false
}

# --- Service Account ---

resource "google_service_account" "sc" {
  account_id   = var.service_account_id
  display_name = "ACAS SecurityCenter Service Account"
  project      = var.shared_services_project_id
}

# --- KMS IAM ---

resource "google_kms_crypto_key_iam_member" "kms_access" {
  for_each = toset([
    local.compute_agent_sa,
    "serviceAccount:${local.compute_default_sa}",
    google_service_account.sc.member
  ])
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
}

# --- ACAS SecurityCenter ---

module "sc-vm" {
  source     = "../../../../../modules/compute-vm"
  project_id = var.shared_services_project_id
  zone       = var.zone
  name       = var.instance_name

  instance_type        = var.machine_type
  confidential_compute = var.enable_confidential_compute

  network_interfaces = [{
    network    = var.network
    subnetwork = var.subnetwork
  }]

  metadata = {
    enable-oslogin         = true
    block-project-ssh-keys = true
  }

  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  encryption = {
    kms_key_self_link = data.google_kms_crypto_key.default.id
  }

  service_account = {
    email = google_service_account.sc.email
  }

  boot_disk = {
    initialize_params = {
      image = coalesce(var.image, data.google_compute_image.sc_golden.self_link)
      size  = var.boot_disk_size
      type  = "pd-ssd"
    }
  }

  attached_disks = [
    {
      auto_delete       = false
      size              = var.data_disk_size
      name              = "${var.instance_name}-data"
      kms_key_self_link = data.google_kms_crypto_key.default.id
      options = {
        type = "pd-ssd"
      }
    }
  ]

  tags = ["acas-sc"]

  depends_on = [
    google_project_service.services,
    google_kms_crypto_key_iam_member.kms_access
  ]
}


