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

locals {
  dod_advertised_ip_ranges = {
    (data.google_compute_subnetwork.subnet.ip_cidr_range) = "DoD-Assigned-Subnet-${var.subnetwork_name}"
  }

  router_configs = var.router_configs

  router_names = {
    router1 = google_compute_router.routers["router1"].name
    router2 = google_compute_router.routers["router2"].name
  }

  router_regions = {
    router1 = var.region1
    router2 = var.region2
  }
}

data "google_compute_subnetwork" "subnet" {
  name    = var.subnetwork_name
  project = var.hub_project_id
  region  = var.subnetwork_region
}

data "google_compute_network" "vpc" {
  name    = var.network_name
  project = var.hub_project_id
}

# Cloud Routers (x2)
resource "google_compute_router" "routers" {
  for_each = local.router_configs

  project = var.hub_project_id
  name    = each.value.name
  network = data.google_compute_network.vpc.self_link
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
}

# VLAN Attachments (x4)
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
  vlan_tag8021q            = each.value.vlan_id

  admin_enabled = true

  depends_on = [
    google_compute_router.routers
  ]
}
