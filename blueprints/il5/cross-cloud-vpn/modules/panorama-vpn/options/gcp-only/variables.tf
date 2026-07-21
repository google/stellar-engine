variable "project_id" {
  description = "The GCP Project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for regional resources and secrets."
  type        = string
}

variable "name_prefix" {
  description = "The prefix to apply to the generated GCP VPN resources."
  type        = string
  default     = "ha-vpn-gcp-only"
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

variable "azure_gateway_ip_0" {
  description = "The public IP of the first instance of the Azure Virtual Network Gateway."
  type        = string
}

variable "azure_gateway_ip_1" {
  description = "The public IP of the second instance of the Azure Virtual Network Gateway."
  type        = string
}

variable "secret_name_tunnel0" {
  description = "The name of the regional secret in GCP Secret Manager for Tunnel 0."
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

variable "gcp_bgp_apipa_ip_0" {
  description = "The GCP BGP APIPA IP for Tunnel 0"
  type        = string
  default     = "169.254.21.1"
}

variable "azure_bgp_apipa_ip_0" {
  description = "The Azure BGP APIPA IP for Tunnel 0"
  type        = string
  default     = "169.254.21.2"
}

variable "gcp_bgp_apipa_ip_1" {
  description = "The GCP BGP APIPA IP for Tunnel 1"
  type        = string
  default     = "169.254.21.5"
}

variable "azure_bgp_apipa_ip_1" {
  description = "The Azure BGP APIPA IP for Tunnel 1"
  type        = string
  default     = "169.254.21.6"
}

variable "gcp_bgp_identifier_range" {
  description = "BGP Identifier range for the router."
  type        = string
  default     = null
}
