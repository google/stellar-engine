/**
 * Copyright 2023 Google LLC
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

variable "dataflow_worker_sa_id" {
  description = "Optional account ID for the Dataflow worker service account (6 to 30 lowercase alphanumeric characters or hyphens). Defaults to main_project_id when unset."
  type        = string
  default     = null
  validation {
    condition = (
      var.dataflow_worker_sa_id == null ||
      can(regex("^[a-z]([-a-z0-9]{4,28}[a-z0-9])$", var.dataflow_worker_sa_id))
    )
    error_message = "dataflow_worker_sa_id must be 6 to 30 lowercase letters, digits, or hyphens, starting with a letter and ending with a letter or digit."
  }
}

variable "firewall_name" {
  description = "The firewall name."
  type        = string
}

variable "kms_key_name" {
  description = "Short name of the existing KMS crypto key (for example `my-key`) used for encryption, not the full resource path. It is looked up in the key ring named by `kms_keyring_name`."
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
  default     = "us-east4-a"
}