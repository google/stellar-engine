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

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.region
  project  = var.core_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

resource "google_project_service" "cloud_run" {
  project            = var.main_project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "binary_authorization" {
  project            = var.main_project_id
  service            = "binaryauthorization.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service_identity" "run_sa" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "run.googleapis.com"
  depends_on = [google_project_service.cloud_run]
}

resource "time_sleep" "cloud_run_agent_propagation" {
  create_duration = "60s"
  depends_on      = [google_project_service_identity.run_sa]
}

resource "google_service_account" "cloud_run_service_account" {
  account_id   = var.name
  display_name = "Cloud Run Service Account for ${var.name}"
  project      = var.main_project_id
}

# The invoker role is granted on the service or job that this blueprint
# creates, not on the project. The `iam` input of the Cloud Run module is
# authoritative for a role, so additive members keep other grants in place.
resource "google_cloud_run_v2_service_iam_member" "cloud_run_invoker" {
  count    = var.is_job ? 0 : 1
  project  = var.main_project_id
  location = var.region
  name     = module.cloud-run.resource_name
  role     = "roles/run.invoker"
  member   = google_service_account.cloud_run_service_account.member
}

resource "google_cloud_run_v2_job_iam_member" "cloud_run_invoker" {
  count    = var.is_job ? 1 : 0
  project  = var.main_project_id
  location = var.region
  name     = module.cloud-run.resource_name
  role     = "roles/run.invoker"
  member   = google_service_account.cloud_run_service_account.member
}

resource "google_kms_crypto_key_iam_member" "cloud_run_service_agent_kms_permissions" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.run_sa.member
  depends_on    = [time_sleep.cloud_run_agent_propagation]
}

moved {
  from = module.cloud_run
  to   = module.cloud-run
}

module "cloud-run" {
  source         = "../../../modules/cloud-run-v2/"
  project_id     = var.main_project_id
  name           = var.name
  region         = var.region
  encryption_key = data.google_kms_crypto_key.default.id
  type           = var.is_job ? "JOB" : "SERVICE"
  service_config = { ingress = var.ingress }
  binary_authorization = (
    var.binary_authorization_mode == "disabled" ? null : {
      use_default = var.binary_authorization_mode == "default" ? true : null
      policy = (
        var.binary_authorization_mode == "policy"
        ? var.binary_authorization_policy : null
      )
    }
  )

  containers = {
    (var.name) = {
      image = var.container_image
      env   = var.env_vars
      ports = {
        port = {
          container_port = var.port
        }
      }
      resources = {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle = var.cpu_idle
      }
    }
  }
  service_account_config = {
    create = false
    email  = google_service_account.cloud_run_service_account.email
  }
  deletion_protection = var.deletion_protection
  depends_on = [
    google_project_service.cloud_run,
    google_project_service.binary_authorization,
    google_kms_crypto_key_iam_member.cloud_run_service_agent_kms_permissions,
  ]
}