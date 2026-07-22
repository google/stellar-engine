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
###############################################################################
#                                DtaFusion variables                          #
###############################################################################
variable "accelerators" {
  description = "Accelerators."
  type = object({
    accelerator_type = optional(string)
    state            = optional(string)
  })

  default = null
}

variable "connection_type" {
  description = "Connection type for datafusion."
  type        = string
  default     = "PRIVATE_SERVICE_CONNECT_INTERFACES"

  validation {
    condition     = contains(["PRIVATE_SERVICE_CONNECT_INTERFACES", "VPC_PEERING"], var.connection_type)
    error_message = "Only values \"PRIVATE_SERVICE_CONNECT_INTERFACES\" and \"VPC_PEERING\" allowed."
  }
}

variable "dataproc_service_account" {
  description = "Service account for DataProc connection."
  type        = string
  default     = null
}

variable "description" {
  description = "DataFusion instance description."
  type        = string
  default     = "Terraform managed."
}

variable "enable_stackdriver_logging" {
  description = "Option to enable Stackdriver Logging."
  type        = bool
  default     = false
}

variable "enable_stackdriver_monitoring" {
  description = "Option to enable Stackdriver Monitorig."
  type        = bool
  default     = false
}

variable "firewall_create" {
  description = "Create Network firewall rules to enable SSH."
  type        = bool
  default     = true
}

variable "ip_allocation" {
  description = "Ip allocated for datafusion instance when not using the auto created one and created outside of the module."
  type        = string
  default     = null
}

variable "ip_allocation_create" {
  description = "Create Ip range for datafusion instance."
  type        = bool
  default     = true
}

variable "kms_key" {
  description = "Full path to KMS key."
  type        = string
  default     = null
}

variable "labels" {
  description = "The resource labels for instance to use to annotate any related underlying resources, such as Compute Engine VMs."
  type        = map(string)
  default     = {}
}

variable "landing_project_id" {
  description = "Landing project ID."
  type        = string
}

variable "name" {
  description = "Name of the DataFusion instance."
  type        = string
}

variable "network" {
  description = "Name of the network in the project with which the tenant project will be peered for executing pipelines in the form of projects/{project-id}/global/networks/{network}."
  type        = string
}

variable "network_peering" {
  description = "Create Network peering between project and DataFusion tenant project."
  type        = bool
  default     = true
}

variable "private_instance" {
  description = "Create private instance."
  type        = bool
  default     = true
}

variable "project_id" {
  description = "Project ID."
  type        = string
}

variable "region" {
  description = "DataFusion region."
  type        = string
}

variable "subnet" {
  description = "Full path to subnet."
  type        = string
}

variable "type" {
  description = "Datafusion Instance type. It can be BASIC or ENTERPRISE (default value)."
  type        = string
  default     = "BASIC"
}

variable "unreachable_cidr_block" {
  description = "The CIDR block to which the CDF instance can't route traffic to in the consumer project VPC."
  type        = string
  default     = null
}
