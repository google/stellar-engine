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
variable "allowed_persistence_regions" {
  description = "A list of Google Cloud regions where messages are allowed to be stored. If empty, the topic will use the default global storage policy."
  type        = list(string)
  default     = ["us-east4"]
}

variable "core_project_id" {
  description = "The Google Cloud Project ID where the existing KMS KeyRing and CryptoKeys are provisioned."
  type        = string
}

variable "kms_key_name" {
  description = "The full resource path of the existing Cloud KMS CryptoKey to use for Customer-Managed Encryption Keys (CMEK) on the Pub/Sub topic."
  type        = string
}

variable "kms_keyring_name" {
  description = "The name of the existing Cloud KMS Key Ring to use for Pub/Sub topic encryption."
  type        = string
}

variable "main_project_id" {
  description = "The Google Cloud Project ID where the Pub/Sub topic and associated service accounts will be created."
  type        = string
}

variable "publisher_account_id" {
  description = "The ID for the custom service account created for the Pub/Sub publisher (e.g., 'my-publisher-sa')."
  type        = string
  default     = "pubsub-publisher-sa"
}

variable "publisher_name" {
  description = "The display name for the custom Pub/Sub publisher service account."
  type        = string
  default     = "Pub/Sub Publisher Service Account"
}

variable "pubsub_topic" {
  description = "The name of the Pub/Sub topic to be created by this blueprint."
  type        = string
}

variable "gcp_region" {
  description = "The Google Cloud region to be used for Pub/Sub topic deployment and as the default for the provider."
  type        = string
}

variable "subscriber_account_id" {
  description = "The ID for the custom service account created for the Pub/Sub subscriber (e.g., 'my-subscriber-sa')."
  type        = string
  default     = "pubsub-subscriber-sa"
}

variable "subscriber_name" {
  description = "The display name for the custom Pub/Sub subscriber service account."
  type        = string
  default     = "Pub/Sub Subscriber Service Account"
}

