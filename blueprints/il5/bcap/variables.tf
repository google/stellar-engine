# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

variable "additional_regions" {
  description = "Optional map of 2 additional region slots (for example, { region3 = 'us-west1', region4 = 'us-west2' }) to expand from a 2-region 4-attachment topology to a 4-region 8-attachment topology."
  type        = map(string)
  default     = {}
  nullable    = false
  validation {
    condition = (
      length(var.additional_regions) == 0 ||
      length(var.additional_regions) == 2
    )
    error_message = "additional_regions must be empty (2-region topology) or contain exactly 2 entries (4-region topology)."
  }
  validation {
    condition = alltrue([
      for r in values(var.additional_regions) :
      can(regex("^[a-z]+-[a-z]+[0-9]+$", r))
    ])
    error_message = "Every value in additional_regions must be a valid GCP region name (for example, 'us-west1')."
  }
  validation {
    condition = length(distinct(concat(
      [var.region1, var.region2],
      values(var.additional_regions)
    ))) == 2 + length(var.additional_regions)
    error_message = "All regions across region1, region2, and additional_regions must be distinct."
  }
  validation {
    condition = alltrue([
      for k in keys(var.additional_regions) :
      !contains(["region1", "region2"], k)
    ])
    error_message = "additional_regions keys must not reuse 'region1' or 'region2'."
  }
}

variable "attachment_configs" {
  description = "Configuration map for the Partner VLAN attachments required for 99.99% availability (4 for 2-region topology or 8 for 4-region topology). The region for each attachment is derived from its associated `router_key`. For Layer 2 Partner Interconnect, optionally specify paired `candidate_cloud_router_ip_address` and `candidate_customer_router_ip_address` IPv4 CIDRs."
  type = map(object({
    candidate_cloud_router_ip_address    = optional(string)
    candidate_customer_router_ip_address = optional(string)
    description                          = optional(string, "BCAP VLAN Attachment")
    edge_availability_domain             = string
    mtu                                  = optional(number, 1440)
    name                                 = string
    router_key                           = string
    vlan_id                              = optional(number, null)
  }))
  validation {
    condition = (
      (
        length(keys(var.attachment_configs)) == 4 ||
        length(keys(var.attachment_configs)) == 8
      ) &&
      length(keys(var.attachment_configs)) == (
        2 * (2 + length(var.additional_regions))
      )
    )
    error_message = "attachment_configs must provide 4 attachments (2-region topology) or 8 attachments (4-region topology), matching 2 per configured region."
  }
  validation {
    condition = alltrue([
      for k, v in var.attachment_configs :
      contains(
        ["AVAILABILITY_DOMAIN_1", "AVAILABILITY_DOMAIN_2"],
        v.edge_availability_domain
      )
    ])
    error_message = "The edge_availability_domain must be either AVAILABILITY_DOMAIN_1 or AVAILABILITY_DOMAIN_2."
  }
  validation {
    condition = alltrue([
      for k, v in var.attachment_configs :
      contains(keys(var.router_configs), v.router_key)
    ])
    error_message = "Each attachment router_key must match a key defined in router_configs."
  }
  validation {
    condition = length(distinct([
      for k, v in var.attachment_configs :
      "${v.router_key}-${v.edge_availability_domain}"
    ])) == 2 * (2 + length(var.additional_regions))
    error_message = "Attachments must cover every unique (router_key, edge_availability_domain) pair across all configured routers for 99.99% SLA."
  }
  validation {
    condition = length(distinct([
      for k, v in var.attachment_configs : "${v.router_key}/${v.name}"
    ])) == length(keys(var.attachment_configs))
    error_message = "Attachment names must be unique within each router and region."
  }
  validation {
    condition = alltrue([
      for k, v in var.attachment_configs : v.vlan_id == null
    ])
    error_message = "vlan_id cannot be set on PARTNER interconnect attachments because Google and the partner assign the 802.1Q VLAN tag."
  }
  validation {
    condition = alltrue([
      for k, v in var.attachment_configs : (
        (v.candidate_cloud_router_ip_address == null) ==
        (v.candidate_customer_router_ip_address == null)
      )
    ])
    error_message = "candidate_cloud_router_ip_address and candidate_customer_router_ip_address must both be set or both omitted."
  }
  validation {
    condition = alltrue([
      for _, v in var.attachment_configs : (
        v.candidate_cloud_router_ip_address == null ||
        v.candidate_customer_router_ip_address == null
        ? true
        : (
          can(cidrhost(v.candidate_cloud_router_ip_address, 0)) &&
          can(cidrhost(v.candidate_customer_router_ip_address, 0)) &&
          !can(regex(":", v.candidate_cloud_router_ip_address)) &&
          !can(regex(":", v.candidate_customer_router_ip_address)) &&
          try(
            split("/", v.candidate_cloud_router_ip_address)[1] ==
            split("/", v.candidate_customer_router_ip_address)[1],
            false
          ) &&
          (
            try(
              cidrsubnet(
                format("%s/16", split("/", v.candidate_cloud_router_ip_address)[0]),
                0,
                0
              ) == "169.254.0.0/16",
              false
            )
            ? try(tonumber(split("/", v.candidate_cloud_router_ip_address)[1]) == 29, false)
            : try(contains([29, 30], tonumber(split("/", v.candidate_cloud_router_ip_address)[1])), false)
          ) &&
          try(
            cidrsubnet(v.candidate_cloud_router_ip_address, 0, 0) ==
            cidrsubnet(v.candidate_customer_router_ip_address, 0, 0),
            false
          ) &&
          try(
            split("/", v.candidate_cloud_router_ip_address)[0] !=
            cidrhost(v.candidate_cloud_router_ip_address, 0) &&
            split("/", v.candidate_cloud_router_ip_address)[0] !=
            cidrhost(v.candidate_cloud_router_ip_address, -1) &&
            split("/", v.candidate_customer_router_ip_address)[0] !=
            cidrhost(v.candidate_customer_router_ip_address, 0) &&
            split("/", v.candidate_customer_router_ip_address)[0] !=
            cidrhost(v.candidate_customer_router_ip_address, -1),
            false
          ) &&
          alltrue([
            for blk in [
              "0.0.0.0/8",
              "10.0.0.0/8",
              "100.64.0.0/10",
              "127.0.0.0/8",
              "172.16.0.0/12",
              "192.0.0.0/24",
              "192.0.2.0/24",
              "192.88.99.0/24",
              "192.168.0.0/16",
              "198.18.0.0/15",
              "198.51.100.0/24",
              "203.0.113.0/24",
              "224.0.0.0/4",
              "240.0.0.0/4",
              ] : try(
              cidrsubnet(
                format(
                  "%s/%s",
                  split("/", v.candidate_cloud_router_ip_address)[0],
                  split("/", blk)[1]
                ),
                0,
                0
              ) != blk,
              false
            )
          ]) &&
          v.candidate_cloud_router_ip_address !=
          v.candidate_customer_router_ip_address
        )
      )
    ])
    error_message = "Candidate BGP IPs must be distinct non-network, non-broadcast IPv4 host CIDRs in the same non-private /29 or /30 subnet (/29 only within 169.254.0.0/16)."
  }
  validation {
    condition = alltrue(flatten([
      for k1, v1 in var.attachment_configs : [
        for k2, v2 in var.attachment_configs : (
          k1 == k2 ||
          v1.candidate_cloud_router_ip_address == null ||
          v2.candidate_cloud_router_ip_address == null ||
          try(
            cidrsubnet(
              format(
                "%s/%d",
                split("/", v1.candidate_cloud_router_ip_address)[0],
                min(
                  tonumber(split("/", v1.candidate_cloud_router_ip_address)[1]),
                  tonumber(split("/", v2.candidate_cloud_router_ip_address)[1])
                )
              ),
              0,
              0
              ) != cidrsubnet(
              format(
                "%s/%d",
                split("/", v2.candidate_cloud_router_ip_address)[0],
                min(
                  tonumber(split("/", v1.candidate_cloud_router_ip_address)[1]),
                  tonumber(split("/", v2.candidate_cloud_router_ip_address)[1])
                )
              ),
              0,
              0
            ),
            true
          )
        )
      ]
    ]))
    error_message = "Each attachment specifying candidate BGP IPs must use a non-overlapping subnet."
  }
}

variable "create_vpc" {
  description = "Create a new VPC network named by network_name. Set to false to attach BCAP subnets, routers, and VLAN attachments to an existing VPC network in hub_project_id."
  type        = bool
  default     = true
  nullable    = false
}

variable "dod_base_cidr_block" {
  description = "The base IPv4 /24 CIDR block assigned by the Department of Defense Network Information Center (DoD NIC), programmatically split into two /25 subnets (2-region) or four /26 subnets (4-region)."
  type        = string
  validation {
    condition = (
      can(cidrnetmask(var.dod_base_cidr_block))
      ? tonumber(split("/", var.dod_base_cidr_block)[1]) == 24
      : false
    )
    error_message = "dod_base_cidr_block must be a valid IPv4 /24 CIDR block (e.g., '10.0.0.0/24')."
  }
}

variable "hub_project_id" {
  description = "The GCP project ID where BCAP resources (VPC, Subnets, Routers, Attachments) will be deployed."
  type        = string
}

variable "network_name" {
  description = "The name for the Virtual Private Cloud (VPC) network to create when create_vpc is true, or look up when create_vpc is false."
  type        = string
}

variable "region1" {
  description = "The primary GCP region for BCAP deployment (hosts router1, subnet1, and their associated VLAN attachments)."
  type        = string
  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]+$", var.region1))
    error_message = "region1 must be a valid GCP region name (for example, 'us-central1')."
  }
}

variable "region2" {
  description = "The secondary GCP region for BCAP deployment (hosts router2, subnet2, and their associated VLAN attachments)."
  type        = string
  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]+$", var.region2))
    error_message = "region2 must be a valid GCP region name (for example, 'us-east4')."
  }
}

variable "router_configs" {
  description = "Configuration map for the Cloud Routers (2 for 2-region topology or 4 for 4-region topology). Keys must include 'router1' and 'router2'; additional routers match additional_regions keys or set region."
  type = map(object({
    name        = string
    description = optional(string, "BCAP Cloud Router")
    region      = optional(string)
  }))
  validation {
    condition = (
      length(keys(var.router_configs)) == 2 + length(var.additional_regions) &&
      contains(keys(var.router_configs), "router1") &&
      contains(keys(var.router_configs), "router2")
    )
    error_message = "router_configs must include 'router1' and 'router2' and match the total region count (2 or 4)."
  }
  validation {
    condition = (
      toset([
        for k, v in var.router_configs : try(
          v.region != null ? lookup(
            merge(
              { region1 = var.region1, region2 = var.region2 },
              var.additional_regions
            ),
            v.region,
            v.region
            ) : coalesce(
            k == "router1" ? var.region1 : null,
            k == "router2" ? var.region2 : null,
            lookup(
              var.additional_regions,
              replace(k, "/^router/", "region"),
              null
            ),
            lookup(var.additional_regions, k, null),
            lookup(var.additional_regions, trimprefix(k, "router_"), null),
            lookup(var.additional_regions, trimprefix(k, "router-"), null)
          ),
          ""
        )
        ]) == toset(concat(
        [var.region1, var.region2],
        values(var.additional_regions)
      ))
    )
    error_message = "Every configured region across region1, region2, and additional_regions must map to a unique router in router_configs."
  }
}

variable "router_google_asn" {
  description = "Autonomous System Number (ASN) for the Google side of the BGP sessions on Cloud Routers (should be 16550 for Partner Interconnect)."
  type        = number
  default     = 16550
}

variable "subnet_configs" {
  description = "Configuration map for the DoD subnets (2 for 2-region topology or 4 for 4-region topology). IP CIDRs are split from dod_base_cidr_block. Keys must include 'subnet1' and 'subnet2'; additional subnets match additional_regions keys or set region."
  type = map(object({
    name        = string
    description = optional(string, "BCAP DoD Subnet")
    region      = optional(string)
  }))
  validation {
    condition = (
      length(keys(var.subnet_configs)) == 2 + length(var.additional_regions) &&
      contains(keys(var.subnet_configs), "subnet1") &&
      contains(keys(var.subnet_configs), "subnet2")
    )
    error_message = "subnet_configs must include 'subnet1' and 'subnet2' and match the total region count (2 or 4)."
  }
  validation {
    condition = (
      toset([
        for k, v in var.subnet_configs : try(
          v.region != null ? lookup(
            merge(
              { region1 = var.region1, region2 = var.region2 },
              var.additional_regions
            ),
            v.region,
            v.region
            ) : coalesce(
            k == "subnet1" ? var.region1 : null,
            k == "subnet2" ? var.region2 : null,
            lookup(
              var.additional_regions,
              replace(k, "/^subnet/", "region"),
              null
            ),
            lookup(var.additional_regions, k, null),
            lookup(var.additional_regions, trimprefix(k, "subnet_"), null),
            lookup(var.additional_regions, trimprefix(k, "subnet-"), null)
          ),
          ""
        )
        ]) == toset(concat(
        [var.region1, var.region2],
        values(var.additional_regions)
      ))
    )
    error_message = "Every configured region across region1, region2, and additional_regions must map to a unique subnet in subnet_configs."
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
