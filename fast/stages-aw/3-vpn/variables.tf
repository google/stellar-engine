variable "aws_bgp_asn" {
  description = "BGP Autonomous System Number for AWS side."
  type        = number
  default     = 64512
}

variable "aws_redundancy_type" {
  description = "Redundancy type for the AWS external VPN gateway."
  type        = string
  default     = "FOUR_IPS_REDUNDANCY"
}

variable "aws_secret_version" {
  description = "The version of the secret to pull from Secret Manager for AWS VPN PSKs."
  type        = string
  default     = "latest"
}

variable "aws_tunnel_cipher_suite" {
  description = "The CNSA-compliant cipher suite for the AWS VPN tunnels. If null, the global tunnel_cipher_suite is used."
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

variable "aws_tunnel_details" {
  description = "Explicit configuration for the AWS tunnel peers."
  type = map(object({
    external_ip = string
    gcp_bgp_ip  = string
    aws_bgp_ip  = string
  }))
  default = null
}

variable "azure_bgp_asn" {
  description = "BGP Autonomous System Number for Azure side."
  type        = number
  default     = 65515
}

variable "azure_gateway_ip_0" {
  description = "The first public IP address of the Azure VPN gateway."
  type        = string
  default     = null
}

variable "azure_gateway_ip_1" {
  description = "The second public IP address of the Azure VPN gateway."
  type        = string
  default     = null
}

variable "azure_gcp_bgp_apipa_ip_0" {
  description = "GCP-side internal BGP IP for the first Azure tunnel."
  type        = string
  default     = "169.254.21.1"
}

variable "azure_gcp_bgp_apipa_ip_1" {
  description = "GCP-side internal BGP IP for the second Azure tunnel."
  type        = string
  default     = "169.254.21.5"
}

variable "azure_peer_bgp_apipa_ip_0" {
  description = "Azure-side internal BGP IP for the first Azure tunnel."
  type        = string
  default     = "169.254.21.2"
}

variable "azure_peer_bgp_apipa_ip_1" {
  description = "Azure-side internal BGP IP for the second Azure tunnel."
  type        = string
  default     = "169.254.21.6"
}

variable "azure_redundancy_type" {
  description = "Redundancy type for the Azure external VPN gateway."
  type        = string
  default     = "TWO_IPS_REDUNDANCY"
}

variable "create_gcp_vpn_tunnels_aws" {
  description = "Determines if the GCP VPN tunnels and BGP peering sessions for AWS should be created (gateways remain active)."
  type        = bool
  default     = true
}

variable "enable_azure_vpn" {
  description = "Set to false to destroy the Azure-related VPN tunnels and BGP peering sessions (leaving the gateways intact)."
  type        = bool
  default     = true
}

variable "enable_panorama_vpn" {
  description = "Set to false to destroy the Panorama-related VPN tunnels and BGP peering sessions (leaving the gateways and router intact)."
  type        = bool
  default     = true
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

variable "gcp_network_name" {
  description = "The name of your existing GCP VPC network."
  type        = string
}

variable "gcp_router_name" {
  description = "The name of the GCP Cloud Router."
  type        = string
  default     = null
}

variable "ike_version" {
  description = "The IKE protocol version used for the VPN tunnels."
  type        = number
  default     = 2
}

variable "mgmt_bgp_asn" {
  description = "MGMT router ASN."
  type        = number
  default     = 65200
}

variable "name_prefix" {
  description = "A prefix to use for resource names."
  type        = string
  default     = "ha-vpn"
}

variable "panorama_bgp_asn" {
  description = "BGP Autonomous System Number for Panorama side."
  type        = number
  default     = 65516
}

variable "panorama_gateway_ip_0" {
  description = "The first public IP address of the Panorama VPN gateway."
  type        = string
  default     = null
}

variable "panorama_gateway_ip_1" {
  description = "The second public IP address of the Panorama VPN gateway."
  type        = string
  default     = null
}

variable "panorama_gcp_bgp_apipa_ip_0" {
  description = "GCP-side internal BGP IP for the first Panorama tunnel."
  type        = string
  default     = "169.254.22.1"
}

variable "panorama_gcp_bgp_apipa_ip_1" {
  description = "GCP-side internal BGP IP for the second Panorama tunnel."
  type        = string
  default     = "169.254.22.5"
}

variable "panorama_peer_bgp_apipa_ip_0" {
  description = "Panorama-side internal BGP IP for the first Panorama tunnel."
  type        = string
  default     = "169.254.22.2"
}

variable "panorama_peer_bgp_apipa_ip_1" {
  description = "Panorama-side internal BGP IP for the second Panorama tunnel."
  type        = string
  default     = "169.254.22.6"
}

variable "panorama_project_id" {
  description = "The GCP Project ID where Panorama resources will be created (if different from global project_id)."
  type        = string
  default     = null
}

variable "panorama_redundancy_type" {
  description = "Redundancy type for the Panorama external VPN gateway."
  type        = string
  default     = "TWO_IPS_REDUNDANCY"
}

variable "panorama_router_name" {
  description = "The name of the Cloud Router for Panorama (if different from global gcp_router_name)."
  type        = string
  default     = null
}

variable "panorama_vpc_name" {
  description = "The name of the VPC network for Panorama (if different from global gcp_network_name)."
  type        = string
  default     = null
}

variable "project_id" {
  description = "The GCP Project ID where the resources will be created."
  type        = string
}

variable "region" {
  description = "The GCP region where the resources will be created."
  type        = string
}

variable "secret_name_aws_conn1_tun1" {
  description = "Secret Manager secret name for AWS Connection 1 Tunnel 1 PSK."
  type        = string
  default     = null
}

variable "secret_name_aws_conn1_tun2" {
  description = "Secret Manager secret name for AWS Connection 1 Tunnel 2 PSK."
  type        = string
  default     = null
}

variable "secret_name_aws_conn2_tun1" {
  description = "Secret Manager secret name for AWS Connection 2 Tunnel 1 PSK."
  type        = string
  default     = null
}

variable "secret_name_aws_conn2_tun2" {
  description = "Secret Manager secret name for AWS Connection 2 Tunnel 2 PSK."
  type        = string
  default     = null
}

variable "secret_name_azure_tunnel0" {
  description = "Secret Manager secret name for Azure Tunnel 0 PSK."
  type        = string
  default     = null
}

variable "secret_name_azure_tunnel1" {
  description = "Secret Manager secret name for Azure Tunnel 1 PSK."
  type        = string
  default     = null
}

variable "secret_name_panorama_tunnel0" {
  description = "Secret Manager secret name for Panorama Tunnel 0 PSK."
  type        = string
  default     = null
}

variable "secret_name_panorama_tunnel1" {
  description = "Secret Manager secret name for Panorama Tunnel 1 PSK."
  type        = string
  default     = null
}

variable "stack_type" {
  description = "The stack type for this VPN gateway. Possible values: IPV4_ONLY, IPV4_IPV6, IPV6_ONLY."
  type        = string
  default     = "IPV4_ONLY"
  validation {
    condition     = contains(["IPV4_ONLY", "IPV4_IPV6", "IPV6_ONLY"], var.stack_type)
    error_message = "The stack_type must be one of IPV4_ONLY, IPV4_IPV6, IPV6_ONLY."
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

variable "vpn_bgp_mask" {
  description = "The subnet mask length for the BGP APIPA IP ranges."
  type        = number
  default     = 30
}