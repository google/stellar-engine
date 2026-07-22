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
      locations = [secret_data.location]                       # Convert single string to list of strings
      keys      = { (secret_data.location) = secret_data.key } # Convert single string to map of strings
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

# Use the secret manager module to create the secrets
module "secret-manager" {
  source     = "../../../modules/secret-manager"
  project_id = var.main_project_id
  secrets    = local.secrets
  iam        = var.iam
  depends_on = [
    google_project_service.secretmanager,
    google_project_service_identity.secretmanager,
    google_kms_crypto_key_iam_member.secretmanager,
  ]
}

