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
  description = "BGP Autonomous System Number for AWS side (64512-65534)."
  type        = number
}

variable "aws_vpc_id" {
  description = "The ID of your existing AWS VPC."
  type        = string
}

variable "gcp_bgp_asn" {
  description = "BGP Autonomous System Number for GCP side (64512-65534)."
  type        = number
}

variable "gcp_network_name" {
  description = "The name of your existing GCP VPC network."
  type        = string
}

variable "preshared_keys" {
  description = "Map of pre-shared keys with keys: conn1_tun1, conn1_tun2, conn2_tun1, conn2_tun2"
  type        = map(string)
  sensitive   = true
}

variable "vpn_name" {
  description = "A prefix to use for all resource names."
  default     = "ha-vpn-gcp-aws"
  type        = string
}
