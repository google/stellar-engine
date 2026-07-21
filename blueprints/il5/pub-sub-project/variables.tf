/**
 * Copyright 2024 Google LLC
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
  description = "The allowed persistence regions for the Pub/Sub topic."
  type        = list(string)
  default     = ["us-east4"]
}
variable "core_project_id" {
  description = "Core project ID."
  type        = string
}
variable "kms_key_name" {
  description = "The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for disk encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type        = string
}

variable "main_project_id" {
  description = "Project ID."
  type        = string
}

variable "publisher_account_id" {
  description = "Publisher account ID."
  type        = string
}

variable "publisher_name" {
  description = "Publisher name."
  type        = string
}

variable "pubsub_topic" {
  description = "PubSub topic."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "subscriber_account_id" {
  description = "Subscriber account ID."
  type        = string
}

variable "subscriber_name" {
  description = "Subscriber name."
  type        = string
}
