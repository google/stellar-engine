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

variable "admin_ssh_source_ranges" {
  description = "List of IP ranges allowed to SSH directly into the instance (e.g., from other clouds via VPN/Interconnect)."
  type        = list(string)
  default     = []
}

variable "boot_disk_size" {
  description = "Boot disk size in GB."
  type        = number
  default     = 100
}

variable "data_disk_size" {
  description = "Additional data disk size in GB."
  type        = number
  default     = 500
}

variable "enable_confidential_compute" {
  description = "Enable Confidential Compute for the SecurityCenter VM."
  type        = bool
  default     = true
}

variable "iap_source_ranges" {
  description = "List of IP ranges allowed to connect via Identity-Aware Proxy (IAP)."
  type        = list(string)
  default     = ["35.235.240.0/20"]
}

variable "image" {
  description = "The Golden Image to use for SecurityCenter."
  type        = string
  default     = null
}

variable "instance_name" {
  description = "Name of the SecurityCenter instance."
  type        = string
  default     = "acas-securitycenter"
}

variable "network" {
  description = "Self-link of the VPC network to attach Domain Controller VMs to."
  type        = string
}

variable "hub_project_id" {
  description = "Project ID that hosts the Shared VPC network."
  type        = string
}

variable "prefix" {
  description = "Prefix applied to resource names for org-level naming consistency. Set to null to disable prefixing."
  type        = string
  default     = null
  validation {
    condition     = var.prefix != ""
    error_message = "Prefix cannot be empty, use null instead."
  }
}

variable "shared_services_project_id" {
  description = "GCP project ID where SC resources will be created."
  type        = string
}

variable "region" {
  description = "GCP region for deployment."
  type        = string
  default     = "us-east4"
}

variable "sc_mgmt_source_ranges" {
  description = "List of IP ranges allowed to access the SecurityCenter Web UI (port 443)."
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "service_account_id" {
  description = "Service account ID for SC VM."
  type        = string
  default     = "acas-sc-sa"
}

variable "subnetwork" {
  description = "Self-link of the subnetwork to attach Domain Controller VMs to."
  type        = string
}

variable "zone" {
  description = "GCP zone for the SC VM."
  type        = string
  default     = "us-east4-a"
}

variable "machine_type" {
  description = "Machine type for the SecurityCenter instance."
  type        = string
  default     = "n2d-standard-8"
}

variable "automation" {
  description = "Automation resources created by the bootstrap stage. Used to write ACAS outputs to the GCS outputs bucket for downstream consumption."
  type = object({
    outputs_bucket = string
  })
}
