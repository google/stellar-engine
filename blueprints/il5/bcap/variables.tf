variable "attachment_configs" {
  description = "Configuration map for the four Partner VLAN attachments required for 99.99% availability. The region for each attachment is derived from its associated `router_key`."
  type = map(object({
    name                     = string
    description              = optional(string, "BCAP VLAN Attachment")
    router_key               = string
    edge_availability_domain = string
    mtu                      = optional(number, 1440)
    vlan_id                  = optional(number, null)
  }))
  validation {
    condition     = length(keys(var.attachment_configs)) == 4
    error_message = "Exactly four attachment configurations must be provided for 99.99% availability."
  }
  validation {
    condition = alltrue([
      for k, v in var.attachment_configs : contains(["AVAILABILITY_DOMAIN_1", "AVAILABILITY_DOMAIN_2"], v.edge_availability_domain)
    ])
    error_message = "The edge_availability_domain must be either AVAILABILITY_DOMAIN_1 or AVAILABILITY_DOMAIN_2."
  }
  validation {
    condition = alltrue([
      for k, v in var.attachment_configs : contains(["router1", "router2"], v.router_key)
    ])
    error_message = "The router_key must be either 'router1' or 'router2'."
  }
}

variable "dod_base_cidr_block" {
  description = "The base /24 CIDR block assigned by the Department of Defense Network Information Center (DoD NIC), which will be programmatically split into two /25 subnets."
  type        = string
  validation {
    condition     = can(cidrhost(var.dod_base_cidr_block, 0)) && tonumber(split("/", var.dod_base_cidr_block)[1]) == 24
    error_message = "dod_base_cidr_block must be a valid /24 CIDR block (e.g., '10.0.0.0/24')."
  }
}

variable "hub_project_id" {
  description = "The GCP project ID where BCAP resources (VPC, Subnets, Routers, Attachments) will be deployed."
  type        = string
}

variable "network_name" {
  description = "The name for the Virtual Private Cloud (VPC) network to be created."
  type        = string
}

variable "region1" {
  description = "The primary GCP region for BCAP deployment (hosts router1, subnet1, and their associated VLAN attachments)."
  type        = string
}

variable "region2" {
  description = "The secondary GCP region for BCAP deployment (hosts router2, subnet2, and their associated VLAN attachments)."
  type        = string
}

variable "router_configs" {
  description = "Configuration map for the two Cloud Routers. Names are user-defined; regions are derived from `region1` (for router1) and `region2` (for router2). Keys must be 'router1' and 'router2'."
  type = map(object({
    name        = string
    description = optional(string, "BCAP Cloud Router")
  }))
  validation {
    condition     = length(keys(var.router_configs)) == 2 && contains(keys(var.router_configs), "router1") && contains(keys(var.router_configs), "router2")
    error_message = "The router_configs map must contain exactly two entries with keys 'router1' and 'router2'."
  }
}

variable "router_google_asn" {
  description = "Autonomous System Number (ASN) for the Google side of the BGP sessions on Cloud Routers (should be 16550 for Partner Interconnect)."
  type        = number
  default     = 16550
}

variable "subnet_configs" {
  description = "Configuration map for the two DoD subnets. Names are user-defined; IP CIDRs are derived from 'dod_base_cidr_block'; regions are derived from `region1` (for subnet1) and `region2` (for subnet2). Keys must be 'subnet1' and 'subnet2'."
  type = map(object({
    name        = string
    description = optional(string, "BCAP DoD Subnet")
  }))
  validation {
    condition     = length(keys(var.subnet_configs)) == 2 && contains(keys(var.subnet_configs), "subnet1") && contains(keys(var.subnet_configs), "subnet2")
    error_message = "The subnet_configs map must contain exactly two entries with keys 'subnet1' and 'subnet2'."
  }
}

variable "subnet_enable_flow_logs" {
  description = "Enable VPC flow logs for the created DoD subnets."
  type        = bool
  default     = true
}

variable "subnet_private_ip_google_access" {
  description = "Enable Private Google Access for the created DoD subnets."
  type        = bool
  default     = true
}
