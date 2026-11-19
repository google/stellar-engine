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

locals {
  # One entry per key, role and member in var.existing_kms_keys. The map key
  # is "<key name>/<role>/<member>", so each state address stays stable when
  # other members are added or removed. Every part of the map key must be
  # known at plan time: pass literal member strings, not values computed
  # from resources that the same apply creates. Null entries, null member
  # lists and null members are type-valid input and yield no grant.
  _existing_keys_iam_members = flatten([
    for key_name, key in var.existing_kms_keys : [
      for role, members in(key == null ? {} : key.iam_members) : [
        for member in distinct(compact(members == null ? [] : members)) : {
          key_name = key_name
          member   = member
          role     = role
        }
      ]
    ]
  ])
  existing_keys_iam_members = {
    for v in local._existing_keys_iam_members :
    "${v.key_name}/${v.role}/${v.member}" => v
  }
}

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

# Additive grants from the iam_members attribute of each existing key. Member
# resources leave bindings managed outside this blueprint untouched.
resource "google_kms_crypto_key_iam_member" "existing_keys" {
  for_each = local.existing_keys_iam_members
  crypto_key_id = (
    data.google_kms_crypto_key.existing_keys[each.value.key_name].id
  )
  role   = each.value.role
  member = each.value.member
}
