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

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "developer_registries" {
  description = "A map of developer registries and readers/writers for those developer registries."
  type = map(object({
    readers = optional(list(string))
    writers = optional(list(string))
  }))
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
  description = "GCP Project to deploy Google Artifact Registries into."
  type        = string
}

variable "network_project_id" {
  description = "Project that the Consumer Compute Engine VPC is located."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy Consumer VM into."
  type        = string
}

variable "subnetwork_name" {
  description = "VPC Subnet to deploy Consumer VM into."
  type        = string
}

variable "vpc_network_name" {
  description = "Name of the VPC where the subnet is deployed."
  type        = string
  default     = ""
  nullable    = false
}
