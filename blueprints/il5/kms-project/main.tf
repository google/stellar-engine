/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

data "google_project" "current" {
  project_id = var.main_project_id
}

# Data source to reference the existing KMS KeyRing
data "google_kms_key_ring" "existing_keyring" {
  name     = var.existing_kms_keyring_name
  location = var.gcp_region
  project  = var.core_project_id # The project where the existing KMS keys are provisioned
}

# Data source to reference existing CryptoKeys defined in the blueprint's inputs
data "google_kms_crypto_key" "existing_keys" {
  for_each = var.existing_kms_keys # Iterate over the map of existing keys provided
  name     = each.key              # Key is the crypto key's short name
  key_ring = data.google_kms_key_ring.existing_keyring.id
}

locals {
  key_rotation_periods = {
    for k, v in var.existing_kms_keys :
    k => coalesce(v.rotation_period_s, var.rotation_period_s)
  }
  key_iam_bindings = merge([
    for k, v in var.existing_kms_keys : merge([
      for role, members in coalesce(v.iam_members, {}) : {
        for member in members :
        "${k}-${role}-${member}" => {
          crypto_key_id = data.google_kms_crypto_key.existing_keys[k].id
          role          = role
          member        = member
        }
      }
    ]...)
  ]...)
}

resource "google_kms_crypto_key_iam_member" "key_iam_members" {
  for_each      = local.key_iam_bindings
  crypto_key_id = each.value.crypto_key_id
  role          = each.value.role
  member        = each.value.member
}

# Grant permissions (or manage existing IAM bindings) on existing CryptoKeys
resource "google_kms_crypto_key_iam_member" "default_encrypter_decrypter" {
  # If var.email is null, for_each will be an empty map, and no resources will be created.
  # This correctly replaces the 'count' logic.
  for_each      = var.email != null ? data.google_kms_crypto_key.existing_keys : {}
  crypto_key_id = each.value.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "user:${var.email}"
}

resource "google_kms_crypto_key_iam_member" "default_group_encrypter_decrypter" {
  # If var.group_email is null, for_each will be an empty map, and no resources will be created.
  for_each      = var.group_email != null ? data.google_kms_crypto_key.existing_keys : {}
  crypto_key_id = each.value.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "group:${var.group_email}"
}

