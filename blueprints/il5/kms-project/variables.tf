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

variable "core_project_id" {
  description = "The Google Cloud Project ID where the existing KMS KeyRing and CryptoKeys are actually provisioned (this could be the same as `main_project_id`)."
  type        = string
}

variable "email" {
  description = "Email address of a user to grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` on every key in `existing_kms_keys`. Set to null to skip the grant."
  type        = string
  # Made optional, as it might not always be used
  default = null
}

variable "existing_kms_keyring_name" {
  description = "The name of the existing Cloud KMS KeyRing to manage or apply policies to."
  type        = string
}

variable "existing_kms_keys" {
  description = "A map where keys are the names of existing CryptoKeys within the specified KeyRing, and values are objects defining additional properties (e.g., IAM members to add). The `iam_members` attribute maps a role to the members to grant it to on the key, and its member strings must be known at plan time."
  type = map(object({
    iam_members       = optional(map(list(string)), {}) # Example: { "roles/cloudkms.cryptoKeyEncrypterDecrypter" = ["serviceAccount:...", "user:..."] }
    rotation_period_s = optional(number)                # Example for managing rotation on existing keys (in seconds)
  }))
  default = {}
}

variable "gcp_region" {
  description = "The Google Cloud region where the existing KMS KeyRing is located. This will also be used as the default region for the provider."
  type        = string
}

variable "group_email" {
  description = "Email address of a Google group to grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` on every key in `existing_kms_keys`. Set to null to skip the grant."
  type        = string
  # Made optional, as it might not always be used
  default = null
}

variable "main_project_id" {
  description = "The Google Cloud Project ID where KMS-related IAM policies will be managed (i.e., the project where the existing KMS keys reside)."
  type        = string
}
