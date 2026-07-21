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
}

variable "instance_name" {
  description = "Name of the SecurityCenter instance."
  type        = string
  default     = "acas-securitycenter"
}

variable "kms_key_name" {
  description = "Name of the KMS crypto key for disk encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "Name of the KMS keyring used for disk encryption."
  type        = string
}

variable "kms_project_id" {
  description = "Project ID where the KMS keyring resides (may differ from project_id in hub-and-spoke KMS architectures)."
  type        = string
}

variable "machine_type" {
  description = "Machine type for the SecurityCenter instance."
  type        = string
  default     = "n2d-standard-8"
}

variable "network_name" {
  description = "VPC network name."
  type        = string
}

variable "network_project_id" {
  description = "Project ID that hosts the VPC (same as project_id for non-Shared VPC)."
  type        = string
}

variable "project_id" {
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

variable "subnetwork_name" {
  description = "VPC subnetwork name."
  type        = string
}

variable "zone" {
  description = "GCP zone for the SC VM."
  type        = string
  default     = "us-east4-a"
}
