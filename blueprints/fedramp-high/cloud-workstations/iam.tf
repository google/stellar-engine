# Copyright 2025 Google LLC
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

resource "google_service_account" "workstation_config_key_user" {
  project      = var.main_project_id
  account_id   = "workstation-config-kms"
  display_name = "Workstation Config Service Account"
}

resource "google_kms_crypto_key_iam_member" "workstations_sa_kms_permissions" {
  crypto_key_id = local.key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.workstation_config_key_user.email}"
}

# The Cloud Workstations service agent attaches the cluster and its VMs to one
# subnetwork, so it holds the role on that subnetwork and not on the project.
resource "google_compute_subnetwork_iam_member" "network_user" {
  project    = local.landing_project
  region     = var.region
  subnetwork = var.subnetwork_name
  role       = "roles/compute.networkUser"
  member     = local.workstation_default_sa
  depends_on = [google_project_service.workstations]
}

# Workstation VMs pull a private image only as a service account that the
# workstation configuration names, so the account exists only when
# var.image_repository names the repository that holds var.image.
module "workstation-vm-sa" {
  source       = "../../../modules/iam-service-account"
  count        = local.image_repository == null ? 0 : 1
  project_id   = var.main_project_id
  name         = "workstation-vm"
  display_name = "Workstation VM Service Account"
  # Cloud Logging and Cloud Monitoring accept log entries and metrics for a
  # project only, so these roles have no narrower resource to bind to.
  iam_project_roles = {
    (var.main_project_id) = [
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter",
    ]
  }
}

resource "google_artifact_registry_repository_iam_member" "artifact_registry_reader" {
  count      = local.image_repository == null ? 0 : 1
  project    = coalesce(local.image_repository.project_id, var.main_project_id)
  location   = local.image_repository.location
  repository = local.image_repository.name
  role       = "roles/artifactregistry.reader"
  member     = module.workstation-vm-sa[0].iam_email
}
