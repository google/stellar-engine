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
  # Define the configurations for both VPCs in a map for use with for_each
  vpc_configs = {
    "local" = {
      project_id        = var.local_vpc_project_id
      name              = var.local_vpc_name
      subnetwork_prefix = var.local_subnetwork_prefix_name
      cidrs             = [var.local_subnetwork_cidr_a, var.local_subnetwork_cidr_b, var.local_subnetwork_cidr_c]
      secondary_cidrs_a = var.local_secondary_ip_ranges_cidr_a
      secondary_cidrs_b = var.local_secondary_ip_ranges_cidr_b
    }
    "peer" = {
      project_id        = var.peer_vpc_project_id_to_create
      name              = var.peer_vpc_name_to_create
      subnetwork_prefix = var.peer_subnetwork_prefix_name
      cidrs             = [var.peer_subnetwork_cidr_a, var.peer_subnetwork_cidr_b, var.peer_subnetwork_cidr_c]
      secondary_cidrs_a = var.peer_secondary_ip_ranges_cidr_a
      secondary_cidrs_b = var.peer_secondary_ip_ranges_cidr_b
    }
  }

  # Collect all unique project IDs where VPCs will be provisioned by this blueprint
  # This is used to ensure APIs are enabled in all relevant projects.
  all_vpc_project_ids = toset(distinct(
    [
      var.local_vpc_project_id,
      var.peer_vpc_project_id_to_create
    ]
  ))
}

# Explicitly enable the Compute Engine API in all relevant projects
resource "google_project_service" "compute_api" {
  for_each           = local.all_vpc_project_ids
  project            = each.key
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# --- Create VPC Networks ---
module "vpc_networks" {
  source                          = "../../../modules/net-vpc"
  for_each                        = local.vpc_configs
  project_id                      = each.value.project_id
  name                            = each.value.name
  auto_create_subnetworks         = false
  delete_default_routes_on_create = true
  routing_mode                    = "REGIONAL"
  subnets = [
    {
      name          = "${each.value.subnetwork_prefix}-a"
      region        = var.gcp_region
      description   = "Subnet a simple subnet for ${each.key} VPC"
      ip_cidr_range = each.value.cidrs[0]
      flow_logs_config = { # CIS Compliance Benchmark 3.8
        aggregation_interval = "INTERVAL_5_SEC"
        flow_sampling        = 1.0
        metadata             = "INCLUDE_ALL_METADATA"
        filter_expression    = "false"
      }
    },
    {
      name                  = "${each.value.subnetwork_prefix}-b-no-pga"
      region                = var.gcp_region
      ip_cidr_range         = each.value.cidrs[1]
      description           = "Subnet b with no PGA for ${each.key} VPC"
      enable_private_access = false
      flow_logs_config = { # CIS Compliance Benchmark 3.8
        aggregation_interval = "INTERVAL_5_SEC"
        flow_sampling        = 1.0
        metadata             = "INCLUDE_ALL_METADATA"
        filter_expression    = "false"
      }
    },
    {
      name          = "${each.value.subnetwork_prefix}-c-secondary-ranges"
      region        = var.gcp_region
      ip_cidr_range = each.value.cidrs[2]
      description   = "Subnet c with secondary ranges for ${each.key} VPC"
      secondary_ip_ranges = {
        a = each.value.secondary_cidrs_a
        b = each.value.secondary_cidrs_b
      }
      flow_logs_config = { # CIS Compliance Benchmark 3.8
        aggregation_interval = "INTERVAL_5_SEC"
        flow_sampling        = 1.0
        metadata             = "INCLUDE_ALL_METADATA"
        filter_expression    = "false"
      }
    }
  ]
  dns_policy = {
    logging = true # CIS Compliance Benchmark 2.12
  }
  depends_on = [google_project_service.compute_api]
}


# Create VPC peering using Google Module
# Google Cloud Platform (GCP) VPC peering has a maximum of 25 connections per project to a single VPC network.
module "peering" {
  source        = "../../../modules/net-vpc-peering"
  prefix        = "peer"
  local_network = module.vpc_networks["local"].id
  peer_network  = module.vpc_networks["peer"].id
  # The depends_on block here is necessary because peering resources depend on the Compute API being
  # enabled in *both* projects before creation. Terraform doesn't implicitly infer this
  # dependency from module.vpc_networks.
  depends_on = [
    google_project_service.compute_api
  ]
}

