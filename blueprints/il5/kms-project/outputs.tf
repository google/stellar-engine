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
output "managed_keyring_id" {
  description = "The fully qualified ID of the existing KMS KeyRing being managed by this blueprint."
  value       = data.google_kms_key_ring.existing_keyring.id
}

output "managed_keyring_name" {
  description = "The name of the existing KMS KeyRing being managed by this blueprint."
  value       = data.google_kms_key_ring.existing_keyring.name
}

output "managed_key_self_links" {
  description = "A map of names to self-links for the existing CryptoKeys being managed by this blueprint."
  value = {
    for key_name, key_data in data.google_kms_crypto_key.existing_keys :
    key_name => key_data.id
  }
}

output "managed_key_ids" {
  description = "A map of names to fully qualified IDs for the existing CryptoKeys being managed by this blueprint."
  value = {
    for key_name, key_data in data.google_kms_crypto_key.existing_keys :
    key_name => key_data.id
  }
}

