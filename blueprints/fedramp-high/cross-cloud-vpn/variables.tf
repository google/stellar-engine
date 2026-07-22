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

variable "aws_bgp_asn" {
  description = "BGP Autonomous System Number for AWS side."
  type        = number
}

variable "aws_region" {
  description = "The AWS region."
  type        = string
}

variable "aws_vpc_id" {
  description = "The ID of your existing AWS VPC."
  type        = string
}

variable "gcp_bgp_asn" {
  description = "BGP Autonomous System Number for GCP side."
  type        = number
}

variable "gcp_network_name" {
  description = "The name of your existing GCP VPC network."
  type        = string
}

variable "gcp_project_id" {
  description = "Your GCP Project ID."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region."
  type        = string
}

variable "tunnel_secret_names" {
  description = "Map of secret names in GCP Secret Manager for the 4 tunnels."
  type        = map(string)
}

variable "vpn_name" {
  description = "A prefix to use for all resource names."
  type        = string
}
