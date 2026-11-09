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

# tfdoc:file:description Workload spoke Shared VPCs, policies, NAT, and DNS.

locals {
  _fw_policy_dir = "${var.factories_config.data_dir}/firewall-policies"
  _spoke_fw_egress_files = {
    for k in keys(var.envs_folders) :
    k => "${local._fw_policy_dir}/${lower(k)}-egress.yaml"
  }
  _spoke_fw_ingress_files = {
    for k in keys(var.envs_folders) :
    k => "${local._fw_policy_dir}/${lower(k)}-ingress.yaml"
  }
  tenant_subnets_map_of_maps = {
    for pairing in setproduct(
      values(var.tenant_accounts),
      values(var.regions)
      ) : "${pairing[0].main_project}-${pairing[1]}" => {
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
    "networksecurity.googleapis.com",
    "servicedirectory.googleapis.com",
    "servicenetworking.googleapis.com",
    "stackdriver.googleapis.com",
    "vpcaccess.googleapis.com"
  ], local._ncc_enabled ? ["networkconnectivity.googleapis.com"] : [])
  shared_vpc_host_config = {
    enabled = true
  }
  metric_scopes = [module.hub-project.project_id]
  iam = merge(
    lookup(var.spoke_project_iam, lower(each.key), lookup(var.spoke_project_iam, each.key, {})),
    {
      "roles/dns.admin" = distinct(concat(
        compact([
          try(local.service_accounts["gke-${lower(each.key)}"], null),
          try(local.service_accounts["project-factory-${lower(each.key)}"], null),
        ]),
        lookup(
          lookup(var.spoke_project_iam, lower(each.key), lookup(var.spoke_project_iam, each.key, {})),
          "roles/dns.admin",
          []
        )
      ))
    }
  )
}

module "env-spoke-vpc" {
  source   = "../../../modules/net-vpc"
  for_each = var.envs_folders

  project_id                        = module.env-spoke-projects[each.key].project_id
  name                              = lower("${each.key}-spoke-0")
  mtu                               = 1500
  delete_default_routes_on_create   = true
  firewall_policy_enforcement_order = "BEFORE_CLASSIC_FIREWALL"
  dns_policy = {
    logging = var.dns.enable_logging
  }
  psa_configs = lookup(
    var.psa_ranges,
    lower(each.key),
    lookup(var.psa_ranges, each.key, [])
  )
  create_googleapis_routes = (
    var.psc_google_apis.enabled
    ? null
    : {
      directpath = false
      private    = true
      restricted = true
    }
  )
  routes  = local._default_egress_routes
  subnets = try(var.subnets[lower(each.key)], [])
  subnets_proxy_only = [{
    region        = var.regions.primary
    active        = true
    name          = lower("proxy-${var.regions.primary}")
    ip_cidr_range = var.proxy_subnets[each.key]
  }]

  shared_vpc_host = true
  shared_vpc_service_projects = [
    for k, v in var.tenant_accounts : v.main_project if v.env == each.key
  ]
}

module "env-spoke-firewall-policy" {
  source    = "../../../modules/net-firewall-policy"
  for_each  = var.envs_folders
  name      = lower("${var.prefix}-${each.key}-fw-policy-0")
  parent_id = module.env-spoke-projects[each.key].project_id
  region    = "global"
  attachments = {
    (lower("${each.key}-spoke-0")) = module.env-spoke-vpc[each.key].id
  }
  security_profile_group_ids = var.security_profile_group_ids
  factories_config = {
    cidr_file_path          = "${var.factories_config.data_dir}/cidrs.yaml"
    egress_rules_file_path  = local._spoke_fw_egress_files[each.key]
    ingress_rules_file_path = local._spoke_fw_ingress_files[each.key]
  }
  ingress_rules = lookup(local._expanded_fw_ingress, lower(each.key), {})
  egress_rules  = lookup(local._expanded_fw_egress, lower(each.key), {})
}

module "env-spoke-nat" {
  source = "../../../modules/net-cloudnat"
  for_each = (
    var.enable_cloud_nat && !var.centralized_egress.enabled
    ? var.envs_folders
    : {}
  )

  project_id     = module.env-spoke-projects[each.key].project_id
  region         = var.regions.primary
  name           = lower("${each.key}-nat-${var.regions.primary}")
  router_create  = true
  router_name    = lower("${each.key}-nat-${var.regions.primary}")
  router_network = module.env-spoke-vpc[each.key].name
}

# Environment private DNS zone and org-domain DNS peering to hub-0.

module "env-dns-priv-example" {
  source   = "../../../modules/dns"
  for_each = var.envs_folders

  project_id = module.env-spoke-projects[each.key].project_id
  name       = lower("${each.key}-org-domain")
  zone_config = {
    domain = lower("${each.key}.${var.organization.domain}.")
    private = {
      client_networks = [module.hub-vpc.self_link]
    }
  }
  recordsets = {
    "A localhost" = { records = ["127.0.0.1"] }
  }
}

module "env-dns-peer-hub-root" {
  source     = "../../../modules/dns"
  for_each   = var.envs_folders
  project_id = module.env-spoke-projects[each.key].project_id
  name       = lower("${each.key}-root-dns-peering")
  zone_config = {
    domain = (
      var.psc_google_apis.enabled
      ? lower("${var.organization.domain}.")
      : "."
    )
    peering = {
      client_networks = [module.env-spoke-vpc[each.key].self_link]
      peer_network    = module.hub-vpc.self_link
    }
  }
}

resource "google_compute_subnetwork_iam_member" "allow_admin_principals" {
  for_each = local.tenant_subnets_map_of_maps
  project  = module.env-spoke-projects[each.value.env].project_id
  region   = each.value.region
  subnetwork = module.env-spoke-vpc[each.value.env].subnet_ids[
    "${each.value.region}/${one([
      for s in try(var.subnets[lower(each.value.env)], []) :
      s.name if s.tenant == each.value.tenant
    ])}"
  ]
  role   = "roles/compute.networkUser"
  member = each.value.admin_principal
}
