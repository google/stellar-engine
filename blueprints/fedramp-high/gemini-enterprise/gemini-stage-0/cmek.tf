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
  kms_rotation_period = "7776000s" # 90 days

  # Determine if we have a US Keyring
  has_us_keyring = var.us_keyring_name != ""

  # ID of the KeyRing to use (Created or Existing)
  keyring_id = local.has_us_keyring ? data.google_kms_key_ring.existing[0].id : google_kms_key_ring.created[0].id

  # Determine if we need to create a new Key
  create_key = var.kms_key_id == "" && var.enable_data_store_cmek

  # Final CMEK Key ID - Only explicitly set if we are enabling Data Store CMEK
  # If enable_data_store_cmek is false, this should be null to avoid attaching it to resources
  cmek_key_id = var.enable_data_store_cmek ? (local.create_key ? google_kms_crypto_key.gemini_enterprise[0].id : var.kms_key_id) : null
}

# ---------------------------------------------------------------------------- #
# 1. KeyRing (US Multi-Region)
# ---------------------------------------------------------------------------- #

# Create KeyRing if name not provided
resource "google_kms_key_ring" "created" {
  count    = local.has_us_keyring ? 0 : 1
  name     = "${title(var.environment)}-${var.tenant}-keyring"
  location = "us"
  project  = var.kms_project_id
}

# Read KeyRing if name provided
data "google_kms_key_ring" "existing" {
  count    = local.has_us_keyring ? 1 : 0
  name     = basename(var.us_keyring_name)
  location = "us"
  project  = var.kms_project_id
}

# ---------------------------------------------------------------------------- #
# 2. Crypto Key (Gemini Enterprise)
# ---------------------------------------------------------------------------- #

# Create Key if kms_key_id is not provided
resource "google_kms_crypto_key" "gemini_enterprise" {
  count           = local.create_key ? 1 : 0
  name            = "gemini-enterprise"
  key_ring        = local.keyring_id
  purpose         = "ENCRYPT_DECRYPT"
  rotation_period = local.kms_rotation_period

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

# If NOT creating keys (kms_key_id IS provided)
# Usage for IAM binding validation/lookup if needed:
data "google_kms_crypto_key" "provided" {
  count    = var.enable_data_store_cmek && var.kms_key_id != null && var.kms_key_id != "" ? 1 : 0
  name     = basename(var.kms_key_id)
  key_ring = element(split("/cryptoKeys/", var.kms_key_id), 0)
}

# ---------------------------------------------------------------------------- #
# 3. IAM Bindings
# ---------------------------------------------------------------------------- #

# Grant Discovery Engine Service Agent access
resource "google_kms_crypto_key_iam_member" "discoveryengine_sa_kms_access" {
  count         = local.cmek_key_id != null ? 1 : 0
  crypto_key_id = local.cmek_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"

  depends_on = [
    google_project_service_identity.discoveryengine,
    time_sleep.wait_for_services
  ]
}

# Grant Cloud Storage Service Agent access
resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access" {
  count         = local.cmek_key_id != null ? 1 : 0
  crypto_key_id = local.cmek_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"

  depends_on = [
    google_project_service_identity.storage,
    time_sleep.wait_for_services
  ]
}

# Grant BigQuery Service Agent access
resource "google_kms_crypto_key_iam_member" "bq_sa_kms_access" {
  count         = local.cmek_key_id != null ? 1 : 0
  crypto_key_id = local.cmek_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:bq-${data.google_project.project.number}@bigquery-encryption.iam.gserviceaccount.com"

  depends_on = [
    google_project_service_identity.bigquery,
    time_sleep.wait_for_services
  ]
}