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

locals {
  # Grab all the keys from the secrets variable in order to grant permissions to secret manager service account
  all_kms_keys = distinct(flatten([
    for secret_id, secret_data in var.secrets : [
      secret_data.key
    ]
  ]))

  # Convert the secret variable to a format that is usable by the module
  secrets = {
    for secret_id, secret_data in var.secrets :
    secret_id => {
      # A user-managed replica in the configured location, encrypted with the
      # configured key.
      global_replica_locations = { (secret_data.location) = secret_data.key }
      expiration_config = (
        try(secret_data.expire_time, null) == null
        ? null
        : { time = secret_data.expire_time }
      )
      version_config = {
        destroy_ttl = try(secret_data.version_destroy_ttl, null)
      }
      iam = lookup(var.iam, secret_id, {})
    }
  }
}

data "google_project" "current" {
  project_id = var.main_project_id
}

# Enable the API service
resource "google_project_service" "secretmanager" {
  project            = var.main_project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Create service account (refers to the Google-managed Secret Manager Service Account)
resource "google_project_service_identity" "secretmanager" {
  provider = google-beta
  project  = var.main_project_id
  service  = "secretmanager.googleapis.com"

  depends_on = [google_project_service.secretmanager]
}

# Grant permissions to secret manager service account
resource "google_kms_crypto_key_iam_member" "secretmanager" {
  for_each      = toset(local.all_kms_keys)
  crypto_key_id = each.value
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-secretmanager.iam.gserviceaccount.com"

  depends_on = [google_project_service_identity.secretmanager]
}

# The secret-manager module rewrite in Cloud Foundation Fabric v44.2.0
# renamed the IAM binding resource, so the move keeps the existing bindings.
moved {
  from = module.secret-manager.google_secret_manager_secret_iam_binding.default
  to   = module.secret-manager.google_secret_manager_secret_iam_binding.authoritative
}

# Use the secret manager module to create the secrets
module "secret-manager" {
  source     = "../../../modules/secret-manager"
  project_id = var.main_project_id
  secrets    = local.secrets
  depends_on = [
    google_project_service.secretmanager,
    google_project_service_identity.secretmanager,
    google_kms_crypto_key_iam_member.secretmanager,
  ]
}

