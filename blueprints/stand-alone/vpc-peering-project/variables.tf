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
  description = "The Google Cloud Project ID where the peering connection will be managed (should be one of the VPC projects)."
  type        = string
}

variable "gcp_region" {
  description = "The Google Cloud region where both VPCs and their subnets will be deployed."
  type        = string
}

# --- Local VPC Configuration (First VPC to be created by this blueprint) ---
variable "local_vpc_name" {
  description = "The name of the first VPC network to be created by this blueprint."
  type        = string
}

variable "local_vpc_project_id" {
  description = "The Google Cloud Project ID where the first VPC network will be created."
  type        = string
}

variable "local_subnetwork_prefix_name" {
  description = "The prefix name for subnets within the first VPC network."
  type        = string
  default     = "local-subnet"
}

variable "local_subnetwork_cidr_a" {
  description = "The primary IP CIDR range for the first subnet in the local VPC (e.g., '10.100.0.0/24')."
  type        = string
}

variable "local_subnetwork_cidr_b" {
  description = "The primary IP CIDR range for the second subnet in the local VPC (e.g., '10.100.1.0/24')."
  type        = string
}

variable "local_subnetwork_cidr_c" {
  description = "The primary IP CIDR range for the third subnet in the local VPC (e.g., '10.100.2.0/24')."
  type        = string
}

variable "local_secondary_ip_ranges_cidr_a" {
  description = "The secondary IP CIDR range 'a' for a subnet in the local VPC (e.g., '192.168.0.0/24')."
  type        = string
}

variable "local_secondary_ip_ranges_cidr_b" {
  description = "The secondary IP CIDR range 'b' for a subnet in the local VPC (e.g., '192.168.1.0/24')."
  type        = string
}

# --- Peer VPC Configuration (Second VPC to be created by this blueprint) ---
variable "peer_vpc_name_to_create" {
  description = "The name of the second VPC network to be created by this blueprint (this will be the 'peer' side)."
  type        = string
}

variable "peer_vpc_project_id_to_create" {
  description = "The Google Cloud Project ID where the second VPC network will be created (this will be the 'peer' side)."
  type        = string
}

variable "peer_subnetwork_prefix_name" {
  description = "The prefix name for subnets within the second VPC network (the 'peer' side)."
  type        = string
  default     = "peer-subnet"
}

variable "peer_subnetwork_cidr_a" {
  description = "The primary IP CIDR range for the first subnet in the peer VPC (e.g., '10.200.0.0/24')."
  type        = string
}

variable "peer_subnetwork_cidr_b" {
  description = "The primary IP CIDR range for the second subnet in the peer VPC (e.g., '10.200.1.0/24')."
  type        = string
}

variable "peer_subnetwork_cidr_c" {
  description = "The primary IP CIDR range for the third subnet in the peer VPC (e.g., '10.200.2.0/24')."
  type        = string
}

variable "peer_secondary_ip_ranges_cidr_a" {
  description = "The secondary IP CIDR range 'a' for a subnet in the peer VPC (e.g., '192.168.2.0/24')."
  type        = string
}

variable "peer_secondary_ip_ranges_cidr_b" {
  description = "The secondary IP CIDR range 'b' for a subnet in the peer VPC (e.g., '192.168.3.0/24')."
  type        = string
}

