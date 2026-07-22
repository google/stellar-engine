#/**
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
variable "project_id" {
  description = "Id of the project you will like to use."
  type        = string
  default     = null
}

variable "network_region" {
  description = "Region that network exist in"
  type        = string
  default     = "us-east4"
}

variable "network_zone" {
  description = "Network zone for IDS"
  type        = string
  default     = "us-east4-c"
}

variable "instance_list" {
  description = "Instance list to monitor with Cloud IDS"
  type        = list(string)
  default     = null
}

variable "subnet_list" {
  description = "Subnet list to monitor with Cloud IDS"
  type        = list(any)
  default     = null
}

variable "ids_private_ip_prefix_length" {
  type    = string
  default = 24
}

variable "ids_private_ip_range_name" {
  type    = string
  default = "ids-private-address-1"
}

variable "ip_protocols_filter" {
  description = "IP Protocols filter for packet mirroing policy."
  type        = list(any)
  default     = null
}

variable "cidr_ranges_filter" {
  description = " ranges that apply as a filter on ingress or egress IP in the IPV4 header"
  type        = list(any)
  default     = null
}
variable "direction_filter" {
  description = "Direction of traffic to mirror. Possible values are INGRESS, EGRESS, and BOTH."
  type        = string
  default     = "BOTH"
}

variable "ids_name" {
  description = "Name of IDS."
  type        = string
}

variable "severity" {
  description = "Display name of the service account to create."
  type        = string
  default     = "MEDIUM"
}

variable "threat_exceptions" {
  description = "Threat_exceptions list to excluded from generating alerts. Limit: 99 IDs."
  default     = null
}

variable "tag_list" {
  description = "Tag list to monitor with Cloud IDS"
  type        = list(string)
  default     = null
}

variable "packet_mirroring_policy_name" {
  description = "Name of packet mirror policy"
  type        = string
  default     = "testpolicy"
}

variable "create_service_networking_connection" {
  description = "Whether to create service networking connection and IP range."
  type        = bool
  default     = true
}

variable "landing_vpc_network" {
  type        = string
  description = "VPC network name for IDS"
}

variable "subnet" {
  type        = string
  description = "subnet used for IDS"
  nullable    = true
  default     = null
}

variable "project" {
  description = "GCP Project ID to deploy into"
  type        = string
}

variable "landing_network" {
  type        = string
  description = "Landing network name for IDS"
}
