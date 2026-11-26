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

locals {
  _all_regions = merge(
    {
      region1 = var.region1
      region2 = var.region2
    },
    var.additional_regions
  )
  _cidr_newbits = length(var.additional_regions) == 0 ? 1 : 2
  _ordered_subnet_keys = concat(
    ["subnet1", "subnet2"],
    sort([
      for k in keys(var.subnet_configs) : k
      if !contains(["subnet1", "subnet2"], k)
    ])
  )

  router_configs = var.router_configs
  subnet_configs = var.subnet_configs

  network_id = (
    var.create_vpc
    ? google_compute_network.vpc_network[0].id
    : data.google_compute_network.existing_vpc[0].id
  )
  network_self_link = (
    var.create_vpc
    ? google_compute_network.vpc_network[0].self_link
    : data.google_compute_network.existing_vpc[0].self_link
  )

  router_names = {
    for k, router in google_compute_router.routers : k => router.name
  }

  router_regions = {
    for k, v in var.router_configs : k => (
      v.region != null
      ? lookup(local._all_regions, v.region, v.region)
      : coalesce(
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
      )
    )
  }

  subnet_regions = {
    for k, v in var.subnet_configs : k => (
      v.region != null
      ? lookup(local._all_regions, v.region, v.region)
      : coalesce(
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
      )
    )
  }

  dod_split_cidr_blocks = {
    for idx, k in local._ordered_subnet_keys :
    k => cidrsubnet(var.dod_base_cidr_block, local._cidr_newbits, idx)
  }

  dod_advertised_ip_ranges = {
    for k, v in var.subnet_configs :
    local.dod_split_cidr_blocks[k] => "DoD-Assigned-Subnet-${v.name}"
  }
}

moved {
  from = google_compute_network.vpc_network
  to   = google_compute_network.vpc_network[0]
}

# VPC Network (created when create_vpc is true)
resource "google_compute_network" "vpc_network" {
  count                   = var.create_vpc ? 1 : 0
  project                 = var.hub_project_id
  name                    = var.network_name
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
  mtu                     = 1460
  description             = "VPC Network for BCAP deployment"
}

data "google_compute_network" "existing_vpc" {
  count   = var.create_vpc ? 0 : 1
  project = var.hub_project_id
  name    = var.network_name
}

# VPC Subnets (2 /25 subnets or 4 /26 subnets)
resource "google_compute_subnetwork" "bcap_subnets" {
  for_each = var.subnet_configs

  project                  = var.hub_project_id
  name                     = each.value.name
  ip_cidr_range            = local.dod_split_cidr_blocks[each.key]
  network                  = local.network_self_link
  region                   = local.subnet_regions[each.key]
  private_ip_google_access = var.subnet_private_ip_google_access
  description              = each.value.description

  dynamic "log_config" {
    for_each = var.subnet_enable_flow_logs ? [1] : []
    content {
      aggregation_interval = "INTERVAL_5_SEC"
      flow_sampling        = 1.0
      metadata             = "INCLUDE_ALL_METADATA"
      filter_expr          = "true"
    }
  }
}

# Cloud Routers (2 or 4 regions)
resource "google_compute_router" "routers" {
  for_each = local.router_configs

  project = var.hub_project_id
  name    = each.value.name
  network = local.network_self_link
  region  = local.router_regions[each.key]
  bgp {
    asn            = var.router_google_asn
    advertise_mode = "CUSTOM"

    dynamic "advertised_ip_ranges" {
      for_each = local.dod_advertised_ip_ranges
      content {
        range       = advertised_ip_ranges.key
        description = advertised_ip_ranges.value
      }
    }
  }

  description = each.value.description

  depends_on = [google_compute_subnetwork.bcap_subnets]
}

# VLAN Attachments (4 or 8 Partner Interconnect attachments)
resource "google_compute_interconnect_attachment" "attachments" {
  for_each = var.attachment_configs

  project     = var.hub_project_id
  name        = each.value.name
  description = each.value.description
  region      = local.router_regions[each.value.router_key]
  router      = local.router_names[each.value.router_key]

  type                     = "PARTNER"
  edge_availability_domain = each.value.edge_availability_domain
  mtu                      = each.value.mtu
  candidate_cloud_router_ip_address = (
    each.value.candidate_cloud_router_ip_address
  )
  candidate_customer_router_ip_address = (
    each.value.candidate_customer_router_ip_address
  )

  admin_enabled = true

  depends_on = [
    google_compute_router.routers
  ]
}
