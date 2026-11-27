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

variable "connection_type" {
  description = "Private Data Fusion connection type ('PRIVATE_SERVICE_CONNECT_INTERFACES' or 'VPC_PEERING')."
  type        = string
  default     = "PRIVATE_SERVICE_CONNECT_INTERFACES"
  validation {
    condition     = contains(["PRIVATE_SERVICE_CONNECT_INTERFACES", "VPC_PEERING"], var.connection_type)
    error_message = "Connection type must be PRIVATE_SERVICE_CONNECT_INTERFACES or VPC_PEERING."
  }
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "ip_allocation" {
  description = "Allocated /22 CIDR range for Data Fusion private instances when connection_type is VPC_PEERING."
  type        = string
  default     = null
  validation {
    condition     = var.connection_type != "VPC_PEERING" || (var.ip_allocation != null && trimspace(var.ip_allocation) != "")
    error_message = "An explicit ip_allocation CIDR range is required when connection_type is VPC_PEERING."
  }
}

variable "kms_key_name" {
  description = "Full path to KMS key for pubsub."
  type        = string
  default     = null
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Project id."
  type        = string
}

variable "name" {
  description = "Name of DataFusion instance."
  type        = string
}

variable "network_name" {
  description = "Full path to VPC."
  type        = string
}

variable "network_project_id" {
  description = "Landing project id."
  type        = string
}

variable "region" {
  description = "Location to deploy job."
  type        = string
}

variable "subnetwork_name" {
  description = "Full path to subnet."
  type        = string
}

variable "unreachable_cidr_block" {
  description = "Optional /25 CIDR block to assign to the Data Fusion PSC instance when connection_type is PRIVATE_SERVICE_CONNECT_INTERFACES."
  type        = string
  default     = null
}
