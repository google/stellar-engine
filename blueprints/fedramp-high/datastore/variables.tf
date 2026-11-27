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

variable "app_engine_integration_mode" {
  description = "App Engine integration mode for the Datastore mode database: ENABLED or DISABLED."
  type        = string
  default     = "DISABLED"
  validation {
    condition = (
      var.app_engine_integration_mode == null
      ? true
      : contains(["ENABLED", "DISABLED"], var.app_engine_integration_mode)
    )
    error_message = "Allowed values are ENABLED or DISABLED."
  }
}

variable "backup_schedule" {
  description = "Optional backup schedule configuration for the Datastore mode database."
  type = object({
    retention         = string
    daily_recurrence  = optional(bool, false)
    weekly_recurrence = optional(string)
  })
  default = null
}

variable "concurrency_mode" {
  description = "Optional concurrency control mode: OPTIMISTIC, PESSIMISTIC, or OPTIMISTIC_WITH_ENTITY_GROUPS."
  type        = string
  default     = null
  validation {
    condition = (
      var.concurrency_mode == null
      ? true
      : contains(
        ["OPTIMISTIC", "PESSIMISTIC", "OPTIMISTIC_WITH_ENTITY_GROUPS"],
        var.concurrency_mode
      )
    )
    error_message = "Allowed values are OPTIMISTIC, PESSIMISTIC, or OPTIMISTIC_WITH_ENTITY_GROUPS."
  }
}

variable "database_create" {
  description = "Whether to create the Firestore in Datastore mode database or manage indexes on an existing database."
  type        = bool
  default     = true
  nullable    = false
}

variable "database_name" {
  description = "Name of the Firestore in Datastore mode database."
  type        = string
  default     = "(default)"
  nullable    = false
}

variable "deletion_policy" {
  description = "Terraform deletion policy when destroying the database resource: ABANDON or DELETE."
  type        = string
  default     = "ABANDON"
  nullable    = false
  validation {
    condition     = contains(["ABANDON", "DELETE"], var.deletion_policy)
    error_message = "Allowed values are ABANDON or DELETE."
  }
}

variable "deletion_protection" {
  description = "Whether to enable GCP deletion protection on the Datastore mode database."
  type        = bool
  default     = true
  nullable    = false
}

variable "index_file" {
  description = "Path relative to the blueprint directory for a Datastore YAML index file used when `indexes` is null."
  type        = string
  default     = "index.yaml"
}

variable "indexes" {
  description = "Explicit composite index definitions managed via google_firestore_index; overrides `index_file` when set."
  type = map(object({
    api_scope  = optional(string)
    collection = string
    fields = list(object({
      field_path   = optional(string)
      order        = optional(string)
      array_config = optional(string)
      vector_config = optional(object({
        dimension = optional(number)
        flat      = optional(bool)
      }))
    }))
    query_scope = optional(string)
  }))
  default = null
}

variable "kms_key_name" {
  description = "Optional full Cloud KMS CryptoKey resource ID used for Customer-Managed Encryption Keys."
  type        = string
  default     = null
}

variable "main_project_id" {
  description = "Google Cloud project ID hosting the Datastore mode database and indexes."
  type        = string
  nullable    = false
}

variable "region" {
  description = "Google Cloud location or region for the Datastore mode database."
  type        = string
  nullable    = false
}
