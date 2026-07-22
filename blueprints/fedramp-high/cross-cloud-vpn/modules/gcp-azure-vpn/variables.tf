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
  description = "The GCP Project ID where the resources will be created."
  type        = string
}

variable "region" {
  description = "The GCP region where the resources will be created."
  type        = string
}

variable "name_prefix" {
  description = "A prefix to use for all resource names."
  type        = string
  default     = "ha-vpn-gcp-azure"
}

variable "gcp_network_name" {
  description = "The name of your existing GCP VPC network."
  type        = string
}

variable "gcp_router_name" {
  description = "The name of the GCP Cloud Router to create."
  type        = string
  default     = null
}

variable "azure_bgp_asn" {
  description = "BGP Autonomous System Number for Azure side."
  type        = number
  validation {
    condition     = var.azure_bgp_asn >= 0 && var.azure_bgp_asn <= 4294967295
    error_message = "The Azure BGP ASN must be a valid 32-bit integer."
  }
}

variable "preshared_keys" {
  description = <<-EOT
    Map of pre-shared keys for the IPsec tunnels.
    Required keys: 'tunnel0', 'tunnel1'.
    
    Example:
    preshared_keys = {
      tunnel0 = "your-strong-preshared-key-1"
      tunnel1 = "your-strong-preshared-key-2"
    }
  EOT
  type        = map(string)
  sensitive   = true
  validation {
    condition     = contains(keys(var.preshared_keys), "tunnel0") && contains(keys(var.preshared_keys), "tunnel1")
    error_message = "The preshared_keys map must contain 'tunnel0' and 'tunnel1' keys."
  }
}
/*
variable "create_azure_resources" {
  description = "Determines if Terraform should manage the Azure side of the VPN (Local Network Gateways and Connections). If false (default), Terraform only creates GCP resources and assumes no API access to Azure. When false, you MUST provide azure_gateway_ip_0 and azure_gateway_ip_1."
  type        = bool
  default     = false
}

variable "azure_resource_group_name" {
  description = "The name of the Azure Resource Group containing the existing Virtual Network Gateway. REQUIRED ONLY if create_azure_resources is true. Ignored if create_azure_resources is false."
  type        = string
  default     = null
}

variable "azure_vpn_gateway_name" {
  description = "The name of the existing Azure Virtual Network Gateway to attach connections to. REQUIRED ONLY if create_azure_resources is true. Ignored if create_azure_resources is false."
  type        = string
  default     = null
}
*/
variable "azure_gateway_ip_0" {
  description = "The public IP of the first instance of the Azure VPN Gateway. REQUIRED if create_azure_resources is false. If create_azure_resources is true, this can be left null and will be automatically discovered via the Azure API."
  type        = string
  default     = null
  validation {
    condition     = var.azure_gateway_ip_0 == null ? true : can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.azure_gateway_ip_0))
    error_message = "The azure_gateway_ip_0 must be a valid IPv4 address."
  }
}

variable "azure_gateway_ip_1" {
  description = "The public IP of the second instance of the Azure VPN Gateway. REQUIRED if create_azure_resources is false. If create_azure_resources is true, this can be left null and will be automatically discovered via the Azure API."
  type        = string
  default     = null
  validation {
    condition     = var.azure_gateway_ip_1 == null ? true : can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.azure_gateway_ip_1))
    error_message = "The azure_gateway_ip_1 must be a valid IPv4 address."
  }
}

variable "gcp_bgp_apipa_ip_0" {
  description = "The GCP BGP APIPA IP for Tunnel 0 (e.g. 169.254.21.1)"
  type        = string
  default     = "169.254.21.1"
  validation {
    condition     = can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.gcp_bgp_apipa_ip_0))
    error_message = "The gcp_bgp_apipa_ip_0 must be a valid IPv4 address."
  }
}

variable "azure_bgp_apipa_ip_0" {
  description = "The Azure BGP APIPA IP for Tunnel 0 (e.g. 169.254.21.2)"
  type        = string
  default     = "169.254.21.2"
  validation {
    condition     = can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.azure_bgp_apipa_ip_0))
    error_message = "The azure_bgp_apipa_ip_0 must be a valid IPv4 address."
  }
}

variable "gcp_bgp_apipa_ip_1" {
  description = "The GCP BGP APIPA IP for Tunnel 1 (e.g. 169.254.21.5)"
  type        = string
  default     = "169.254.21.5"
  validation {
    condition     = can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.gcp_bgp_apipa_ip_1))
    error_message = "The gcp_bgp_apipa_ip_1 must be a valid IPv4 address."
  }
}

variable "azure_bgp_apipa_ip_1" {
  description = "The Azure BGP APIPA IP for Tunnel 1 (e.g. 169.254.21.6)"
  type        = string
  default     = "169.254.21.6"
  validation {
    condition     = can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.azure_bgp_apipa_ip_1))
    error_message = "The azure_bgp_apipa_ip_1 must be a valid IPv4 address."
  }
}


variable "stack_type" {
  description = "The stack type for this VPN gateway to identify the IP protocols that are enabled. Possible values: IPV4_ONLY, IPV4_IPV6, IPV6_ONLY."
  type        = string
  default     = "IPV4_ONLY"
  validation {
    condition     = contains(["IPV4_ONLY", "IPV4_IPV6", "IPV6_ONLY"], var.stack_type)
    error_message = "The stack_type must be one of IPV4_ONLY, IPV4_IPV6, IPV6_ONLY."
  }
}

variable "gateway_ip_version" {
  description = "The IP family of the gateway IPs for the HA-VPN gateway interfaces. Possible values: IPV4, IPV6."
  type        = string
  default     = "IPV4"
  validation {
    condition     = contains(["IPV4", "IPV6"], var.gateway_ip_version)
    error_message = "The gateway_ip_version must be one of IPV4, IPV6."
  }
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
  default = {
    phase1 = {
      encryption = ["AES-GCM-16-256"]
      integrity  = []
      prf        = ["PRF-HMAC-SHA2-384"]
      dh         = ["Group-20"]
    }
    phase2 = {
      encryption = ["AES-GCM-16-256"]
      integrity  = []
      pfs        = ["Group-20"]
    }
  }
}

variable "gcp_bgp_asn" {
  description = "BGP Autonomous System Number for the GCP Cloud Router."
  type        = number
  validation {
    condition     = var.gcp_bgp_asn >= 0 && var.gcp_bgp_asn <= 4294967295
    error_message = "The GCP BGP ASN must be a valid 32-bit integer."
  }
}

variable "gcp_bgp_identifier_range" {
  description = "Explicitly specifies a range of valid BGP Identifiers for this Router. It is provided as a link-local IPv4 range (from 169.254.0.0/16), of size at least /30. If null, GCP will auto-assign."
  type        = string
  default     = null
}
