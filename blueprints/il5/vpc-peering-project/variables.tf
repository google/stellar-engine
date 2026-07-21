/**
 * Copyright 2023 Google LLC
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
  description = "The Main Project ID."
  type        = string
}

variable "network_name" {
  description = "The name of the VPC."
  type        = string
  #Example   default     = "vpc-blueprint-connect"
}

variable "network_project_id" {
  description = "Project that the VPC is located."
  type        = string
}

variable "peer_network_name" {
  description = "The name of the peering VPC."
  type        = string
}

variable "peer_project_id" {
  description = "The peering project ID."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "secondary_ip_ranges_cidr_a" {
  description = "The Secondary IP CIDR."
  type        = string
  #Example default ="192.168.0.0/24"
}

variable "secondary_ip_ranges_cidr_b" {
  description = "The Secondary IP CIDR."
  type        = string
  #Example default ="192.168.1.0/24"
}

variable "subnetwork_cidr_a" {
  description = "The Subnet CIDR."
  type        = string
  #Example default ="10.200.12.0/25"
}

variable "subnetwork_cidr_b" {
  description = "The Subnet CIDR."
  type        = string
  #Example default ="10.200.12.0/25"
}

variable "subnetwork_cidr_c" {
  description = "The Subnet CIDR."
  type        = string
  #Example default ="10.200.12.0/25"
}

variable "subnetwork_prefix_name" {
  description = "The name of the Subnet Prefix."
  type        = string
  #Example   default     = "subnet-blueprint"
}
