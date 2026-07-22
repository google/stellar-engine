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

variable "main_project_id" {
  description = "The Google Cloud Project ID where the NCC hub will be created."
  type        = string
}

variable "ncc_hub_name" {
  description = "The name of the created Network Connectivity Center hub."
  type        = string
  default     = "example-ncc-hub"
}

variable "psc_prop" {
  description = "Whether or not Private Service Connect connections can be propagated to other spokes in the network."
  type        = bool
  default     = false
}

variable "gcp_region" {
  description = "The Google Cloud region to be used as the default for regional resources and the provider. Note: NCC Hubs are global resources."
  type        = string
}

variable "spokes" {
  description = "A map of spoke names to VPC Network self-links (e.g., 'projects/<PROJECT_ID>/global/networks/<VPC_NAME>') to be added to the NCC hub."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "topology" {
  description = "The topology of the network. Can be MESH or STAR."
  type        = string
  default     = "MESH"
  validation {
    condition     = contains(["MESH", "STAR"], var.topology)
    error_message = "Invalid topology. Must be either 'MESH' or 'STAR'."
  }
}

