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
  description = "Deprecated unused input retained for backwards compatibility; Cloud KMS keys in var.secrets encode their host project in each CryptoKey self-link."
  type        = string
  default     = null
}

variable "gcp_region" {
  description = "The Google Cloud region to be used as the default for regional resources and the provider. Note: Secret Manager secrets are regional resources."
  type        = string
  default     = "us-east4"
}

variable "iam" {
  description = "IAM bindings in {SECRET => {ROLE => [MEMBERS]}} format."
  type        = map(map(list(string)))
  default     = {}
}

variable "main_project_id" {
  description = "The Google Cloud Project ID where the secrets will be created."
  type        = string
}

variable "secrets" {
  description = "Map of secret configurations keyed by secret ID. Each value specifies regional replication 'location', a matching-region KMS CryptoKey self-link 'key', and optional 'expire_time' and 'version_destroy_ttl'."
  type = map(object({
    location            = string # A location is required for every secret
    key                 = string # A key is required for the location (the key and secret must be in the same region)
    expire_time         = optional(string)
    version_destroy_ttl = optional(string)
  }))
  default = {}
}
