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
  region  = var.region # Assumes subnetwork is in the same region as the VM location variable
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

resource "google_kms_crypto_key_iam_member" "compute_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.compute.member
}

resource "google_kms_crypto_key_iam_member" "compute_agent_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
}

# Google Compute Engine VM Module
module "compute-engine-vm" {
  source        = "../../../modules/compute-vm"
  project_id    = var.main_project_id
  zone          = var.zone
  name          = var.instance_name
  instance_type = var.instance_type

  confidential_compute = true # CIS Compliance Benchmark 4.11 - Must use compliant instance type

  network_interfaces = [{
    network    = data.google_compute_network.network.self_link
    subnetwork = data.google_compute_subnetwork.subnetwork.self_link
  }]

  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
  }

  encryption = {
    kms_key_self_link = data.google_kms_crypto_key.default.id
  }

  # CIS Compliance Benchmark 4.1
  # CIS Compliance Benchmark 4.2
  service_account = {
    email = google_service_account.compute.email
  }

  # Persistent Disk Attached to the Compute Engine with KMS
  attached_disks = [
    {
      auto_delete       = var.auto_delete
      size              = 20
      name              = "data-disk"
      kms_key_self_link = data.google_kms_crypto_key.default.id
    }
  ]

  boot_disk = {
    initialize_params = {
      image = "cos-cloud/cos-stable"
    }
  }

  depends_on = [
    google_service_account.compute,
    google_kms_crypto_key_iam_member.compute_sa_kms_access,
    google_kms_crypto_key_iam_member.compute_agent_kms_access
  ]
}
