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

variable "bigtable_service_account_id" {
  description = "The Service Account for Bigtable."
  type        = string
}

variable "cluster_id" {
  description = "The Bigtable cluster ID."
  type        = string
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "instance_name" {
  description = "Provide the name of the Bigtable."
  type        = string
}

variable "kms_key_name" {
  description = "The Cloud KMS key for encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Main project ID."
  type        = string
}

variable "num_nodes" {
  description = "Number of nodes in the Bigtable cluster."
  type        = number
  default     = 1
}

variable "region" {
  description = "Google Cloud Region."
  type        = string
  default     = "us-east4"
}

variable "storage_type" {
  description = "Either SSD or HDD."
  type        = string
  default     = "SSD"
}

variable "table" {
  description = "Table to create in the bigtable instance. Default is null."
  type = map(object({
    split_keys      = optional(list(string))
    column_families = map(object({}))
  }))
  default = {
    "Test" = {
      column_families = {}
    }
  }
}

variable "zone" {
  description = "Google Cloud Zone."
  type        = string
  default     = "us-east4-a"
}