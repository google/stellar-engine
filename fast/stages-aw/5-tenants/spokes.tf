/**
 * Copyright 2023 Google LLC
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

# tfdoc:file:description VPC and spoke creation. 

# VPC network for each tenant environment
module "tenant-vpc" {
  source                          = "../../../modules/net-vpc"
  for_each                        = local.tenant_subnets_map_of_maps
  project_id                      = each.value.project
  name                            = "${each.value.tenant_key}-vpc"
  mtu                             = 1500
  delete_default_routes_on_create = true

  subnets = [
    {
      name          = "${each.value.tenant_key}-${each.value.region}-subnet"
      ip_cidr_range = var.tenant.spoke_subnets[each.value.env]
      region        = each.value.region
    }
  ]
  dns_policy = {
    inbound = true
    logging = true
  }
  create_googleapis_routes = null

}

# NCC spoke for each tenant environment
resource "google_network_connectivity_spoke" "tenant_spoke" {
  for_each = local.tenant_subnets_map_of_maps
  name     = "${each.value.env}-${each.value.tenant}-spoke"
  hub      = var.hub_id
  location = "global"
  project  = each.value.project
  group    = var.edge_group_id
  linked_vpc_network {
    uri = module.tenant-vpc[each.key].self_link
  }
}

# Default route for each tenant environment VPC
resource "google_compute_route" "tenant_default_route" {
  for_each     = local.tenant_subnets_map_of_maps
  name         = "${each.value.tenant_key}-default-route"
  project      = each.value.project
  dest_range   = "0.0.0.0/0"
  network      = module.tenant-vpc[each.key].self_link
  next_hop_ilb = var.ilb_ips["transit"]
  priority     = 100
}
