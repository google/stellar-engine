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

variable "enable_confidential_compute" {
  description = "Enable Confidential Compute for the Nessus Scanner VMs."
  type        = bool
  default     = true
}

variable "iap_source_ranges" {
  description = "List of IP ranges allowed to connect via Identity-Aware Proxy (IAP)."
  type        = list(string)
  default     = ["35.235.240.0/20"]
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
  description = "GCP project ID where scanner resources will be created."
  type        = string
}

variable "region" {
  description = "GCP region for deployment."
  type        = string
  default     = "us-east4"
}

variable "scan_target_destination_ranges" {
  description = "List of IP ranges that the Nessus Scanner is allowed to scan."
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "scanner_configs" {
  description = "Map of ACAS Nessus Scanner instances to create. Keys are logical scanner names."
  type = map(object({
    instance_name               = optional(string)
    machine_type                = optional(string, "n2d-standard-2")
    boot_disk_size              = optional(number, 100)
    image                       = optional(string)
    zone                        = optional(string)
    enable_confidential_compute = optional(bool)
  }))
}

variable "securitycenter_source_ranges" {
  description = "List of SecurityCenter IP ranges allowed to connect to the Scanner (port 8834)."
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "service_account_id" {
  description = "Service account ID for Nessus Scanner VMs."
  type        = string
  default     = "acas-scanner-sa"
}

variable "subnetwork" {
  description = "Self-link of the subnetwork to attach Domain Controller VMs to."
  type        = string
}

variable "zone" {
  description = "Default GCP zone for scanner VMs. Can be overridden per scanner in scanner_configs."
  type        = string
  default     = "us-east4-a"
}

variable "automation" {
  description = "Automation resources created by the bootstrap stage. Used to write ACAS outputs to the GCS outputs bucket for downstream consumption."
  type = object({
    outputs_bucket = string
  })
}
