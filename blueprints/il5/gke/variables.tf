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

# --- Project Configuration ---
variable "main_project_id" {
  description = "The Google Cloud Project ID where the GKE cluster will be created."
  type        = string
}

variable "landing_project_id" {
  description = "The Google Cloud Project ID where the existing Shared VPC network is located."
  type        = string
}

variable "core_project_id" {
  description = "The Google Cloud Project ID where the existing Cloud KMS key is located."
  type        = string
}

# --- GCP Region ---
variable "gcp_region" {
  description = "The Google Cloud region where all resources will be deployed."
  type        = string
}

# --- Existing Infrastructure ---
variable "existing_network_name" {
  description = "The name of the existing Shared VPC network to use for the GKE cluster."
  type        = string
}

variable "existing_subnetwork_name" {
  description = "The name of the existing subnetwork to use for the GKE cluster."
  type        = string
}

variable "existing_subnetwork_secondary_range_pods_name" {
  description = "The name of the existing secondary IP range for GKE Pods."
  type        = string
}

variable "existing_subnetwork_secondary_range_services_name" {
  description = "The name of the existing secondary IP range for GKE Services."
  type        = string
}

variable "existing_kms_keyring_name" {
  description = "The name of the existing Cloud KMS Key Ring."
  type        = string
}

variable "existing_kms_key_name" {
  description = "The name of the existing Cloud KMS CryptoKey for boot disk encryption."
  type        = string
}

# --- GKE Cluster Configuration ---
variable "gke_cluster_name" {
  description = "The name of the GKE cluster."
  type        = string
  default     = "gke-cluster"
}

variable "enable_deletion_protection" {
  description = "Whether or not to allow Terraform to destroy the cluster. Recommended to be true for production."
  type        = bool
  default     = true
}

variable "gke_cluster_enable_private_endpoint" {
  description = "Enable a private endpoint for the GKE cluster master, disabling public access."
  type        = bool
  default     = true
}

variable "gke_cluster_master_global_access" {
  description = "WARNING: Expands the internal attack surface. Enable global access for the private master endpoint. If false, access is limited to the cluster's region."
  type        = bool
  default     = false
}

variable "master_authorized_ranges" {
  description = "A map of authorized networks that can access the GKE master endpoint. The key is a display name and the value is the CIDR range. Should be scoped as tightly as possible."
  type        = map(string)
  default     = {}
}

# --- Nodepool Configuration ---
variable "gke_initial_node_per_zone" {
  description = "The initial number of nodes for the default node pool."
  type        = number
  default     = 1
}

variable "gke_nodepool_name" {
  description = "The name of the additional GKE node pool."
  type        = string
  default     = "default-nodepool"
}

variable "nodepool_node_count" {
  description = "The initial number of nodes per zone for the additional node pool."
  type        = object({ initial = number })
  default     = { initial = 1 }
}

variable "node_machine_type" {
  description = "The machine type for the GKE nodes."
  type        = string
  default     = "n2d-standard-2"
}

variable "node_disk_size_gb" {
  description = "The boot disk size in GB for each GKE node."
  type        = number
  default     = 20
}

variable "node_config_tags" {
  description = "A list of network tags to apply to the GKE nodes."
  type        = list(string)
  default     = []
}

variable "remove_default_node_pool" {
  description = "Set to true to remove the default node pool created with the cluster. Requires at least one other node pool to be created."
  type        = bool
  default     = false
}

# --- Bastion Host Configuration ---
variable "bastion_vm_name" {
  description = "The name for the bastion host VM."
  type        = string
  default     = "gke-bastion-vm"
}

variable "bastion_vm_zone" {
  description = "The zone for the bastion host VM."
  type        = string
}

variable "bastion_vm_machine_type" {
  description = "The machine type for the bastion host VM."
  type        = string
  default     = "e2-medium"
}

variable "bastion_vm_image" {
  description = "The boot disk image for the bastion host VM."
  type        = string
  default     = "projects/cos-cloud/global/images/family/cos-stable"
}

