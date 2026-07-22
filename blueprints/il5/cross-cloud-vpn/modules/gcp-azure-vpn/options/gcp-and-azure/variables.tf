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

variable "project_id" {
  description = "The GCP Project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for regional resources and secrets."
  type        = string
}

variable "azure_subscription_id" {
  description = "The Azure Subscription ID."
  type        = string
}

variable "name_prefix" {
  description = "The prefix to apply to the generated VPN resources across both clouds."
  type        = string
  default     = "ha-vpn-gcp-azure"
}

variable "gcp_network_name" {
  description = "The name of the existing GCP VPC network."
  type        = string
}

variable "gcp_router_name" {
  description = "The name of the GCP Cloud Router to create."
  type        = string
  default     = null
}

variable "azure_bgp_asn" {
  description = "The BGP ASN configured on the Azure side."
  type        = number
}

variable "azure_resource_group_name" {
  description = "The name of the Azure Resource Group housing the Virtual Network Gateway."
  type        = string
}

variable "azure_vpn_gateway_name" {
  description = "The name of the existing Azure Virtual Network Gateway to attach connections to."
  type        = string
}

variable "secret_name_tunnel0" {
  description = "The name of the global secret in GCP Secret Manager for Tunnel 0."
  type        = string
}

variable "secret_name_tunnel1" {
  description = "The name of the regional secret in GCP Secret Manager for Tunnel 1."
  type        = string
}

variable "stack_type" {
  description = "The stack type for this VPN gateway. Possible values: IPV4_ONLY, IPV4_IPV6, IPV6_ONLY."
  type        = string
  default     = "IPV4_ONLY"
}

variable "gateway_ip_version" {
  description = "The IP family of the gateway IPs for the HA-VPN gateway interfaces. Possible values: IPV4, IPV6."
  type        = string
  default     = "IPV4"
}

variable "tunnel_cipher_suite" {
  description = "The CNSA-compliant cipher suite for the VPN tunnels. Phase 1 and Phase 2 configurations."
  type = object({
    phase1 = optional(object({
      encryption = optional(list(string))
      integrity  = optional(list(string))
      prf        = optional(list(string))
      dh         = optional(list(string))
    }))
    phase2 = optional(object({
      encryption = optional(list(string))
      integrity  = optional(list(string))
      pfs        = optional(list(string))
    }))
  })
  default = null
}

variable "gcp_bgp_asn" {
  description = "BGP Autonomous System Number for the GCP Cloud Router."
  type        = number
}
