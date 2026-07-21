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

variable "hub_project_id" {
  description = "The GCP project ID where BCAP resources (VPC, Subnets, Routers, Attachments) will be deployed."
  type        = string
}

variable "network_name" {
  description = "VPC network name."
  type        = string
}

variable "region1" {
  description = "The primary GCP region for BCAP deployment (hosts router1 and their associated VLAN attachments)."
  type        = string
}

variable "region2" {
  description = "The secondary GCP region for BCAP deployment (hosts router2 and their associated VLAN attachments)."
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

variable "subnetwork_name" {
  description = "VPC subnetwork name."
  type        = string
}

variable "subnetwork_region" {
  description = "VPC subnetwork region."
  type        = string
}
