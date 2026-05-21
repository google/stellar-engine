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

# tfdoc:file:description Dev spoke VPC and related resources.

locals {
  tenant_subnets_map_of_maps = {
    for pairing in setproduct(values(var.tenant_accounts), values(var.regions)) : "${pairing[0].main_project}-${pairing[1]}" => {
      "project"         = pairing[0].main_project,
      "tenant"          = pairing[0].tenant,
      "admin_principal" = pairing[0].admin_principal
      "region"          = pairing[1],
      "env"             = pairing[0].env
    }
  }
}
module "env-spoke-projects" {
  source = "../../../modules/project"
  providers = {
    google      = google.billing
    google-beta = google-beta.billing
  }
  for_each        = var.envs_folders
  billing_account = var.billing_account.id
  name            = lower("${each.key}-net-host")
  lien_reason     = "Protected by default as a core project."
  parent          = var.folder_ids.networking
  prefix          = var.prefix
  services = concat([
    "container.googleapis.com",
    "compute.googleapis.com",
    "dns.googleapis.com",
    "iap.googleapis.com",
    "networkmanagement.googleapis.com",
    "servicenetworking.googleapis.com",
    "stackdriver.googleapis.com",
    "vpcaccess.googleapis.com"
    ]
  )
  shared_vpc_host_config = {
    enabled = true
  }
  metric_scopes = [module.vdss-host-project.project_id]
  iam = {
    "roles/dns.admin" = compact([
      try(local.service_accounts.gke-dev, null),
      try(local.service_accounts.project-factory-dev, null),
      try(local.service_accounts.project-factory-prod, null),
    ])
  }
  #   # allow specific service accounts to assign a set of roles
  #   iam_bindings = {
  #     sa_delegated_grants = {
  #       role = "roles/resourcemanager.projectIamAdmin"
  #       members = compact([
  #         try(local.service_accounts.data-platform-dev, null),
  #         try(local.service_accounts.project-factory-dev, null),
  #         try(local.service_accounts.project-factory-prod, null),
  #         try(local.service_accounts.gke-dev, null),
  #       ])
  #       condition = {
  #         title       = "dev_stage3_sa_delegated_grants"
  #         description = "Development host project delegated grants."
  #         expression = format(
  #           "api.getAttribute('iam.googleapis.com/modifiedGrantsByRole', []).hasOnly([%s])",
  #           join(",", formatlist("'%s'", local.stage3_sas_delegated_grants))
  #         )
  #       }
  #     }
  #   }
}


module "env-spoke-vpc" {
  source   = "../../../modules/net-vpc"
  for_each = var.envs_folders

  project_id = module.env-spoke-projects[each.key].project_id

  name = lower("${each.key}-spoke-0")
  mtu  = 1500
  dns_policy = {
    logging = var.dns.enable_logging
  }
  delete_default_routes_on_create = true
  psa_configs                     = var.psa_ranges.dev
  # Set explicit routes for googleapis; send everything else to NVAs
  create_googleapis_routes = {
    private = true
  restricted = true }
  subnets = try(var.subnets[lower(each.key)], [])
  subnets_proxy_only = [{
    region        = var.regions.primary
    active        = true
    name          = lower("proxy-${var.regions.primary}")
    ip_cidr_range = var.proxy_subnets[each.key]
  }]

  shared_vpc_host             = true
  shared_vpc_service_projects = [for k, v in var.tenant_accounts : v.main_project if v.env == each.key]

}

# resource "google_network_connectivity_internal_range" "reserved_ranges" {
#   for_each          = var.envs_folders
#   name              = lower("${each.key}-range")
#   project           = module.env-spoke-projects[each.key].project_id
#   description       = "Automatically reserved range for ${each.key}"
#   network           = module.env-spoke-vpc[each.key].id
#   usage             = "FOR_VPC"
#   peering           = "FOR_SELF"
#   prefix_length     = 22
#   target_cidr_range = ["10.200.0.0/16", ]
# }

# resource "google_compute_subnetwork" "defaults" {
#   for_each      = var.envs_folders
#   name          = lower("${each.key}-default-0")
#   project       = module.env-spoke-projects[each.key].project_id
#   ip_cidr_range = google_network_connectivity_internal_range.reserved_ranges[each.key].ip_cidr_range
#   region        = var.regions.primary
#   network       = module.env-spoke-vpc[each.key].id
# }

module "env-spoke-firewall" {
  source   = "../../../modules/net-vpc-firewall"
  for_each = var.envs_folders

  project_id = module.env-spoke-projects[each.key].project_id
  network    = module.env-spoke-vpc[each.key].name
  default_rules_config = {
    disabled = true
  }
  named_ranges  = var.cidrs
  ingress_rules = try(var.firewall_rules[lower(each.key)].ingress, {})
  egress_rules  = try(var.firewall_rules[lower(each.key)].egress, {})
}

resource "time_sleep" "peering_delay" {
  for_each = var.envs_folders

  create_duration = "${index(keys(var.envs_folders), each.key) * 30}s"

  depends_on = [module.env-spoke-vpc]
}

module "peering-envs" {
  source   = "../../../modules/net-vpc-peering"
  for_each = var.envs_folders

  prefix        = lower("${each.key}-peering-0")
  local_network = module.env-spoke-vpc[each.key].self_link
  peer_network  = module.vdss-vpc.self_link
  routes_config = {
    local = {
      public_import = true
    }
    peer = {
      public_export = true
    }
  }

  depends_on = [
    time_sleep.peering_delay
  ]
}

# DNS
# GCP-specific environment zone

module "env-dns-priv-example" {
  source   = "../../../modules/dns"
  for_each = var.envs_folders

  project_id = module.env-spoke-projects[each.key].project_id
  name       = lower("${each.key}-org-domain")
  zone_config = {
    domain = lower("${each.key}.${var.organization.domain}.")
    private = {
      client_networks = [module.vdss-vpc.self_link]
    }
  }
  recordsets = {
    "A localhost" = { records = ["127.0.0.1"] }
  }
}

# root zone peering to landing to centralize configuration; remove if unneeded

module "env-dns-peer-landing-root" {
  source     = "../../../modules/dns"
  for_each   = var.envs_folders
  project_id = module.env-spoke-projects[each.key].project_id
  name       = lower("${each.key}-root-dns-peering")
  zone_config = {
    domain = "."
    peering = {
      client_networks = [module.env-spoke-vpc[each.key].self_link]
      peer_network    = module.vdss-vpc.self_link
    }
  }
}

resource "google_compute_subnetwork_iam_member" "allow-admin-principals" {
  for_each = local.tenant_subnets_map_of_maps
  project  = module.env-spoke-projects[each.value.env].project_id
  region   = each.value.region
  subnetwork = module.env-spoke-vpc[each.value.env].subnet_ids[
    "${each.value.region}/${one([
      for s in try(var.subnets[lower(each.value.env)], []) : s.name if s.tenant == each.value.tenant
    ])}"
  ]
  role   = "roles/compute.networkUser"
  member = each.value.admin_principal
}
