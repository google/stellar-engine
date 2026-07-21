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
  default     = "ha-vpn-gcp-aws"
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

variable "aws_bgp_asn" {
  description = "BGP Autonomous System Number for AWS side."
  type        = number
  validation {
    condition     = var.aws_bgp_asn >= 0 && var.aws_bgp_asn <= 4294967295
    error_message = "The AWS BGP ASN must be a valid 32-bit integer."
  }
}

variable "preshared_keys" {
  description = <<-EOT
    Map of pre-shared keys for the IPsec tunnels.
    Required keys: 'conn1_tun1', 'conn1_tun2', 'conn2_tun1', 'conn2_tun2'.
    
    Example:
    preshared_keys = {
      conn1_tun1 = "your-strong-preshared-key-1"
      conn1_tun2 = "your-strong-preshared-key-2"
      conn2_tun1 = "your-strong-preshared-key-3"
      conn2_tun2 = "your-strong-preshared-key-4"
    }
  EOT
  type        = map(string)
  sensitive   = true
  validation {
    condition     = contains(keys(var.preshared_keys), "conn1_tun1") && contains(keys(var.preshared_keys), "conn1_tun2") && contains(keys(var.preshared_keys), "conn2_tun1") && contains(keys(var.preshared_keys), "conn2_tun2")
    error_message = "The preshared_keys map must contain 'conn1_tun1', 'conn1_tun2', 'conn2_tun1', and 'conn2_tun2' keys."
  }
}

variable "create_aws_resources" {
  description = "Determines if Terraform should manage the AWS side of the VPN (Virtual Private Gateways and Connections). If false (default), Terraform only creates GCP resources and assumes no API access to AWS. When false, you MUST provide aws_tunnel_details unless create_gcp_vpn_tunnels is also false."
  type        = bool
  default     = false
}

variable "create_gcp_vpn_tunnels" {
  description = "Determines if the GCP VPN tunnels and BGP resources should be created. Set to false for the first stage of a multi-cloud VPN setup when AWS tunnel details are not yet available."
  type        = bool
  default     = true
}

variable "aws_vpc_id" {
  description = "The ID of the existing AWS VPC to attach connections to. REQUIRED ONLY if create_aws_resources is true. Ignored if create_aws_resources is false."
  type        = string
  default     = null
}

variable "aws_tunnel_details" {
  description = <<-EOT
    The explicit configuration for the AWS tunnel peers. REQUIRED ONLY if create_aws_resources is false. 
    Map of 4 AWS tunnels with their external IPs and BGP IPs.
    Must contain exactly 4 keys: 'tun1', 'tun2', 'tun3', 'tun4'.
    
    Example:
    aws_tunnel_details = {
      tun1 = { external_ip = "203.0.113.1", gcp_bgp_ip = "169.254.21.2/30", aws_bgp_ip = "169.254.21.1" }
      tun2 = { external_ip = "203.0.113.2", gcp_bgp_ip = "169.254.22.2/30", aws_bgp_ip = "169.254.22.1" }
      tun3 = { external_ip = "203.0.113.3", gcp_bgp_ip = "169.254.23.2/30", aws_bgp_ip = "169.254.23.1" }
      tun4 = { external_ip = "203.0.113.4", gcp_bgp_ip = "169.254.24.2/30", aws_bgp_ip = "169.254.24.1" }
    }
  EOT
  type = map(object({
    external_ip = string
    gcp_bgp_ip  = string
    aws_bgp_ip  = string
  }))
  default = null
  validation {
    condition = var.aws_tunnel_details == null ? true : (
      can(var.aws_tunnel_details["tun1"]) &&
      can(var.aws_tunnel_details["tun2"]) &&
      can(var.aws_tunnel_details["tun3"]) &&
      can(var.aws_tunnel_details["tun4"])
    )
    error_message = "If provided, aws_tunnel_details must include exactly keys for tun1, tun2, tun3, and tun4."
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
