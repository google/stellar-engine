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

variable "boot_disk_image" {
  description = "Boot disk image for Domain Controller VMs. Must be an approved, hardened Windows Server image (e.g., Windows Server 2022 Datacenter) meeting DISA STIG baselines."
  type        = string
  default     = "projects/windows-cloud/global/images/family/windows-2022"
}

variable "boot_disk_size" {
  description = "Boot disk size in GB for Domain Controller VMs. Must be at least as large as the boot image (100 GB recommended for Windows Server system files and updates)."
  type        = number
  default     = 100
}

variable "data_disk_size" {
  description = "Size in GB for the secondary persistent disk dedicated to the Active Directory database (NTDS) and SYSVOL logs."
  type        = number
  default     = 50
}

variable "domain_controllers" {
  description = "Detailed topology map of the target domain controllers."
  type = map(object({
    region     = string
    zone       = string
    subnetwork = string
  }))
}

variable "gcp_ntp_relay_ip" {
  description = "The internal IP address of the local GCP NTP Relay server that the DCs will sync time against."
  type        = string
}

variable "hub_project_id" {
  description = "The GCP project ID where Domain Controller resources will be deployed. Must be the project that owns the VPC (the Security Host Project), since Cloud Router, Cloud NAT, and firewall rules cannot cross-project reference networks."
  type        = string
}

variable "machine_type" {
  description = "Machine type for Domain r VMs. n2-standard-2 is sufficient for basic AD workloads. Change to n2-standard-4 for a larger VM."
  type        = string
  default     = "n2-standard-2"
}

variable "network" {
  description = "Self-link of the VPC network to attach Domain Controller VMs to."
  type        = string
}

variable "prefix" {
  description = "Prefix applied to resource names for org-level naming consistency (e.g. 'da1'). Set to null to disable prefixing."
  type        = string
  default     = null
  validation {
    condition     = var.prefix != ""
    error_message = "Prefix cannot be empty, use null instead."
  }
}

variable "shared_services_project_id" {
  description = "The GCP project ID where Domain Controller resources will be deployed."
  type        = string
}
