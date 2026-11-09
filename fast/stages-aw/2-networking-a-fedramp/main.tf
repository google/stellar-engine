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

# tfdoc:file:description Networking folder and hierarchical policy.

locals {
  essential_contacts = (
    var.essential_contacts == null
    ? {}
    : try(
      { for k, v in tomap(var.essential_contacts) : k => tolist(v) },
      tostring(var.essential_contacts) == "" ? {} : { (tostring(var.essential_contacts)) = ["ALL"] }
    )
  )
  custom_roles = {
    service_project_network_admin = try(
      var.custom_roles.service_project_network_admin,
      "roles/compute.networkAdmin"
    )
  }
  service_accounts = {
    for k, v in coalesce(var.service_accounts, {}) :
    k => "serviceAccount:${v}" if v != null
  }
  _has_internet_egress = (
    var.centralized_egress.enabled || var.enable_cloud_nat
  )
  _default_egress_routes = (
    var.centralized_egress.enabled
    ? {
      default = {
        dest_range    = "0.0.0.0/0"
        next_hop      = var.centralized_egress.swp_ip
        next_hop_type = "ip"
        priority      = 1000
      }
    }
    : (
      var.enable_cloud_nat
      ? {
        default = {
          dest_range    = "0.0.0.0/0"
          next_hop      = "default-internet-gateway"
          next_hop_type = "gateway"
          priority      = 1000
        }
      }
      : {}
    )
  )
  _expanded_fw_ingress = {
    for net, pol in var.firewall_policy_rules : lower(net) => {
      for rk, rv in pol.ingress : rk => merge(rv, {
        match = merge(rv.match, {
          destination_ranges = (
            rv.match.destination_ranges == null
            ? null
            : flatten([
              for r in rv.match.destination_ranges :
              lookup(var.cidrs, r, [r])
            ])
          )
          source_ranges = (
            rv.match.source_ranges == null
            ? null
            : flatten([
              for r in rv.match.source_ranges :
              lookup(var.cidrs, r, [r])
            ])
          )
        })
      })
    }
  }
  _expanded_fw_egress = {
    for net, pol in var.firewall_policy_rules : lower(net) => {
      for rk, rv in pol.egress : rk => merge(rv, {
        match = merge(rv.match, {
          destination_ranges = (
            rv.match.destination_ranges == null
            ? null
            : flatten([
              for r in rv.match.destination_ranges :
              lookup(var.cidrs, r, [r])
            ])
          )
          source_ranges = (
            rv.match.source_ranges == null
            ? null
            : flatten([
              for r in rv.match.source_ranges :
              lookup(var.cidrs, r, [r])
            ])
          )
        })
      })
    }
  }
}

module "folder" {
  source        = "../../../modules/folder"
  parent        = "organizations/${var.organization.id}"
  name          = "Networking"
  folder_create = var.folder_ids.networking == null
  id            = var.folder_ids.networking
  contacts      = local.essential_contacts
  firewall_policy = {
    name   = "default"
    policy = module.firewall-policy-default.id
  }
}

module "firewall-policy-default" {
  source    = "../../../modules/net-firewall-policy"
  name      = coalesce(var.factories_config.firewall_policy_name, "${var.prefix}-net-default")
  parent_id = module.folder.id
  factories_config = {
    cidr_file_path          = "${var.factories_config.data_dir}/cidrs.yaml"
    ingress_rules_file_path = "${var.factories_config.data_dir}/hierarchical-ingress-rules.yaml"
  }
}
