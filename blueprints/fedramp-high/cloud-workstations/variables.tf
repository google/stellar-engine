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

variable "cluster_id" {
  description = "The ID of the workstation cluster."
  type        = string
  default     = "example-workstation-cluster"
}

variable "config_id" {
  description = "The ID of the workstation configuration."
  type        = string
  default     = "example-workstation-config"
}

variable "core_project_id" {
  description = "The Project ID where the kms key is located."
  type        = string
  default     = null
}

variable "image" { # https://cloud.google.com/workstations/docs/preconfigured-base-images
  description = "Container image used by the workstations."
  type        = string
  default     = null
}

variable "kms_key_name" {
  description = "The name of the kms key."
  type        = string
}

variable "kms_keyring_name" {
  description = "The keyring of the kms key."
  type        = string
}

variable "machine_type" {
  description = "Type of GCE machine for the workstation configuration."
  type        = string
  default     = "e2-standard-4"
}

variable "main_project_id" {
  description = "The Project ID where the workstations will be created."
  type        = string
}

variable "network_name" {
  description = "The name of the network."
  type        = string
}

variable "network_project_id" {
  description = "The ID of the landing zone project where the VPC is located."
  type        = string
  default     = null
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
}

variable "subnetwork_name" {
  description = "The name of the subnet."
  type        = string
}

variable "workstations" {
  description = "The workstations that will be created based on the configuration."
  type = map(object({
    env   = optional(map(string))
    users = optional(list(string))
  }))
}