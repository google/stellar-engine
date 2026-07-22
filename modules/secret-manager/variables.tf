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
variable "iam" {
  description = "IAM bindings in {SECRET => {ROLE => [MEMBERS]}} format."
  type        = map(map(list(string)))
  default     = {}
}

variable "labels" {
  description = "Optional labels for each secret."
  type        = map(map(string))
  default     = {}
}

variable "project_id" {
  description = "Project ID where the secrets will be created."
  type        = string
}

variable "secrets" {
  description = "Map of secret configurations. Each key is the `secret_id` (name) of the secret. Each value is an object with optional `expire_time`, `version_destroy_ttl`, `locations` (list of regions for user-managed replication), and `keys` (a map where keys are replication locations (or 'global') and values are full KMS CryptoKey self-links for encryption)." # Clarified description
  type = map(object({
    expire_time         = optional(string)
    locations           = optional(list(string))
    keys                = optional(map(string))
    version_destroy_ttl = optional(string)
  }))
  default = {}
}

variable "versions" {
  description = "Optional map of secret versions to manage. Keys are `secret_id`s, values are maps where keys are internal version names and values are objects containing `enabled` (bool) and `data` (string, the actual secret content)."
  type = map(map(object({
    enabled = bool
    data    = string
  })))
  default = {}
}

