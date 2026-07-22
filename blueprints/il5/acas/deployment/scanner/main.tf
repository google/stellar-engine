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
  project_id = var.project_id
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
  project  = var.kms_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

data "google_storage_project_service_account" "gcs_sa" {
  project = var.project_id
}

locals {
  compute_agent_sa   = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
  gcs_agent          = "serviceAccount:${data.google_storage_project_service_account.gcs_sa.email_address}"
  compute_default_sa = "${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

# --- Project Services ---

resource "google_project_service" "services" {
  for_each = toset([
    "compute.googleapis.com",
    "cloudkms.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com"
  ])
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# --- Service Account ---

resource "google_service_account" "scanner" {
  account_id   = var.service_account_id
  display_name = "ACAS Nessus Scanner Service Account"
  project      = var.project_id
}

# --- KMS IAM ---

resource "google_project_iam_member" "kms_access" {
  # checkov:skip=CKV_GCP_46: The default compute service account requires KMS access to decrypt the boot image.
  # investigate/justify/resolve in future iterations
  for_each = toset([
    local.compute_agent_sa,
    local.gcs_agent,
    "serviceAccount:${local.compute_default_sa}",
    google_service_account.scanner.member
  ])
  project = var.kms_project_id
  role    = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member  = each.value
}

# --- ACAS Nessus Scanners ---

module "scanner-vms" {
  for_each   = var.scanner_configs
  source     = "../../../../../modules/compute-vm"
  project_id = var.project_id
  zone       = coalesce(each.value.zone, var.zone)
  name       = coalesce(each.value.instance_name, each.key)

  instance_type        = each.value.machine_type
  confidential_compute = coalesce(each.value.enable_confidential_compute, var.enable_confidential_compute)

  network_interfaces = [{
    network    = data.google_compute_network.network.self_link
    subnetwork = data.google_compute_subnetwork.subnetwork.self_link
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
    email = google_service_account.scanner.email
  }

  boot_disk = {
    initialize_params = {
      image = each.value.image
      size  = each.value.boot_disk_size
      type  = "pd-ssd"
    }
  }

  tags = ["acas-scanner"]

  depends_on = [
    google_project_service.services,
    google_project_iam_member.kms_access
  ]
}
