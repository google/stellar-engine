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
  description = "The allowed ports for the firewall."
  type        = list(string)
}

variable "allowed_source_ranges" {
  description = "These are the allowed source ranges."
  type        = list(string)
}

variable "compute_service_account_id" {
  description = "This is the compute service account id."
  type        = string
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "disk_name" {
  description = "This is the disk name."
  type        = string
}

variable "image" {
  description = "Disk image."
  type        = string
  default     = "cos-cloud/cos-stable"
}

variable "instance_name" {
  description = "This is the instance name."
  type        = string
}

variable "instance_type" {
  description = "Instance type."
  type        = string
  default     = "n2d-standard-2"
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
  description = "This is the ID of project."
  type        = string
}

variable "network_name" {
  description = "VPC to use."
  type        = string
}

variable "network_project_id" {
  description = "Project that the Compute Engine VPC is located."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "subnetwork_name" {
  description = "Subnet to use."
  type        = string
}

variable "zone" {
  description = "This is the zone of the instance."
  type        = string
}
