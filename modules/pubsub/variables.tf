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
  description = "Topic-level IAM bindings (non-authoritative) in {ROLE => [MEMBERS]} format."
  type        = map(list(string))
  default     = {}
  nullable    = false
}

variable "iam_bindings" {
  description = "Authoritative IAM bindings for the Pub/Sub topic in {KEY => {role = ROLE, members = [], condition = {}}}. Keys are arbitrary identifiers. Use this to explicitly define all roles/members for a topic."
  type = map(object({
    members = list(string)
    role    = string
    condition = optional(object({
      expression  = string
      title       = string
      description = optional(string)
    }))
  }))
  nullable = false
  default  = {}
}

variable "iam_bindings_additive" {
  description = "Additive (non-authoritative) IAM bindings for the Pub/Sub topic. Keys are arbitrary identifiers. Use this to add individual members to specific roles without managing all members for that role."
  type = map(object({
    member = string
    role   = string
    condition = optional(object({
      expression  = string
      title       = string
      description = optional(string)
    }))
  }))
  nullable = false
  default  = {}
}

variable "kms_key" {
  description = "The full resource path of the Cloud KMS CryptoKey to use for Customer-Managed Encryption Keys (CMEK) on the Pub/Sub topic. Set to `null` to use Google-managed encryption."
  type        = string
  default     = null
}

variable "labels" {
  description = "Optional labels to apply to the Pub/Sub topic."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "message_retention_duration" {
  description = "The minimum duration (e.g., '10s', '24h', '7d') to retain a message after it is published to the topic. Minimum is 10 minutes, maximum is 7 days. Set to `null` to use default."
  type        = string
  default     = null
}

variable "name" {
  description = "The name of the Pub/Sub topic to be created."
  type        = string
}

variable "project_id" {
  description = "The Google Cloud Project ID where the Pub/Sub topic and subscriptions will be created."
  type        = string
}

variable "regions" {
  description = "A list of Google Cloud regions where messages published to the topic are allowed to be stored. If empty, the topic will use the default global storage policy."
  type        = list(string)
  default     = []
  nullable    = false
}

variable "schema" {
  description = "Optional topic schema configuration. If set, all messages in this topic should follow this schema."
  type = object({
    definition   = string
    msg_encoding = optional(string, "ENCODING_UNSPECIFIED")
    schema_type  = string
  })
  default = null
}

variable "subscriptions" {
  description = "Map of subscriptions to create for the topic. Keys are subscription names. Each value is an object configuring subscription properties (e.g., push configs, dead-letter policies, BigQuery/Cloud Storage exports, retry policies, IAM)."
  type = map(object({
    ack_deadline_seconds         = optional(number)
    enable_exactly_once_delivery = optional(bool, false)
    enable_message_ordering      = optional(bool, false)
    expiration_policy_ttl        = optional(string)
    filter                       = optional(string)
    iam                          = optional(map(list(string)), {}) # Non-authoritative IAM on subscription
    labels                       = optional(map(string))
    message_retention_duration   = optional(string)
    retain_acked_messages        = optional(bool, false)
    bigquery = optional(object({
      table                 = string
      drop_unknown_fields   = optional(bool, false)
      service_account_email = optional(string)
      use_table_schema      = optional(bool, false)
      use_topic_schema      = optional(bool, false)
      write_metadata        = optional(bool, false)
    }))
    cloud_storage = optional(object({
      bucket          = string
      filename_prefix = optional(string)
      filename_suffix = optional(string)
      max_duration    = optional(string)
      max_bytes       = optional(number)
      avro_config = optional(object({
        write_metadata = optional(bool, false)
      }))
    }))
    dead_letter_policy = optional(object({
      topic                 = string
      max_delivery_attempts = optional(number)
    }))
    iam_bindings = optional(map(object({
      members = list(string)
      role    = string
      condition = optional(object({
        expression  = string
        title       = string
        description = optional(string)
      }))
    })), {}) # Authoritative IAM on subscription
    iam_bindings_additive = optional(map(object({
      member = string
      role   = string
      condition = optional(object({
        expression  = string
        title       = string
        description = optional(string)
      }))
    })), {}) # Additive IAM on subscription
    push = optional(object({
      endpoint   = string
      attributes = optional(map(string))
      no_wrapper = optional(bool, false)
      oidc_token = optional(object({
        audience              = optional(string)
        service_account_email = string
      }))
    }))
    retry_policy = optional(object({
      minimum_backoff = optional(string)
      maximum_backoff = optional(string)
    }))
  }))
  default  = {}
  nullable = false
}

