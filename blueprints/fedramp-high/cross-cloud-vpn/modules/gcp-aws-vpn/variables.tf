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
