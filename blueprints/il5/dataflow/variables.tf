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
variable "allowed_firewall_ports" {
  description = "The allowed ports for the firewall. Dataflow requires 12345 and 12346."
  type        = list(string)
  default     = [12345, 12346]
}

variable "allowed_source_ranges" {
  description = "These are the allowed source ranges."
  type        = list(string)
}

variable "bucket_name" {
  description = "This is the name of the bucket."
  type        = string
}

variable "core_project_id" {
  description = "Core Project ID."
  type        = string
}

variable "dataflow_name" {
  description = "Name of the Dataflow project."
  type        = string
}

variable "firewall_name" {
  description = "The firewall name."
  type        = string
}

variable "kms_key_name" {
  description = "The full self-link (projects/../locations/../cryptoKeys/..) of the existing KMS key to use for encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type        = string
}

variable "main_project_id" {
  description = "The ID of the project in which to provision resources."
  type        = string
}

variable "network_name" {
  description = "The network name."
  type        = string
}

variable "network_project_id" {
  description = "Project that the Compute Engine VPC is located."
  type        = string
}

variable "parameters" {
  description = "Dataflow Paramaters."
  type        = map(string)
}

variable "prefix" {
  description = "This is the prefix for all resources."
  type        = string
}

variable "region" {
  description = "The region in which to provision resources."
  type        = string
  default     = "us-east4"
}

variable "storage_class" {
  description = "This is the storage class of the storage bucket."
  type        = string
}

variable "subnetwork_name" {
  description = "The subnet name."
  type        = string
}

variable "template_gcs_path" {
  description = "This is the template path of the dataflow job."
  type        = string
}

variable "zone" {
  description = "This is the name of the zone."
  type        = string
  default     = "us-east4"
}