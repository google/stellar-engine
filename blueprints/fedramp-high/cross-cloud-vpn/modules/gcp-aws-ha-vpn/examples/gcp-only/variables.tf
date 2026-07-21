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
  default     = "ha-vpn-gcp-aws"
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

variable "aws_bgp_asn" {
  description = "The BGP ASN configured on the AWS side."
  type        = number
}

variable "aws_tunnel_details" {
  description = "Configuration details for the AWS peer."
  type = map(object({
    external_ip = string
    gcp_bgp_ip  = string
    aws_bgp_ip  = string
  }))
  default = null
}

variable "secret_name_conn1_tun1" {
  description = "The name of the regional secret in GCP Secret Manager for Connection 1 Tunnel 1."
  type        = string
}

variable "secret_name_conn1_tun2" {
  description = "The name of the regional secret in GCP Secret Manager for Connection 1 Tunnel 2."
  type        = string
}

variable "secret_name_conn2_tun1" {
  description = "The name of the regional secret in GCP Secret Manager for Connection 2 Tunnel 1."
  type        = string
}

variable "secret_name_conn2_tun2" {
  description = "The name of the regional secret in GCP Secret Manager for Connection 2 Tunnel 2."
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

variable "create_gcp_vpn_tunnels" {
  description = "Determines if the GCP VPN tunnels and BGP resources should be created. Set to false for the first stage."
  type        = bool
  default     = true
}
