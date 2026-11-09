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

# tfdoc:file:description Central hub VPC, Cloud NAT, DNS, and default NCC hub.

locals {
  _hub_project_id = module.hub-project.project_id
  _hub_project_aliases = {
    hub          = module.hub-project.project_id
    hub-host     = module.hub-project.project_id
    landing      = module.hub-project.project_id
    net-hub-host = module.hub-project.project_id
  }
  _hub_vpcs = merge(
    {
      hub     = module.hub-vpc.self_link
      landing = module.hub-vpc.self_link
    },
    var.centralized_egress.enabled
    ? { egress = module.egress-vpc[0].self_link }
    : {}
  )
  _default_ncc_spokes_vpcs = merge(
    {
      hub = {
        vpc                   = "$vpcs:hub"
        name                  = "hub-0"
        project_id            = "$project_ids:hub"
        group                 = "$ncc_groups:main/center"
        description           = "Central hub VPC spoke."
        labels                = tomap({})
        exclude_export_ranges = tolist(null)
        include_export_ranges = tolist(null)
      }
    },
    !var.centralized_egress.enabled ? {} : {
      egress = {
        vpc                   = "$vpcs:egress"
        name                  = "egress-0"
        project_id            = "$project_ids:hub"
        group                 = "$ncc_groups:main/center"
        description           = "Centralized SWP Internet Egress VPC spoke."
        labels                = tomap({})
        exclude_export_ranges = tolist(null)
        include_export_ranges = tolist(null)
      }
    },
    {
      for k, _ in var.envs_folders : lower(k) => {
        vpc                   = "$vpcs:${lower(k)}"
        name                  = "${lower(k)}-spoke-0"
        project_id            = "$project_ids:${lower(k)}"
        group                 = "$ncc_groups:main/edge"
        description           = "${k} environment spoke VPC."
        labels                = tomap({})
        exclude_export_ranges = tolist(null)
        include_export_ranges = tolist(null)
      }
    }
  )
  _default_ncc_hubs = !var.enable_default_ncc_hub ? {} : {
    main = {
      project_id      = "$project_ids:hub"
      description     = "Default Stage 2 hub and environment spoke NCC hub."
      export_psc      = true
      policy_mode     = "PRESET"
      preset_topology = "STAR"
      labels          = tomap({})
      groups = {
        center = {
          description = "Central hub and hybrid connectivity spokes."
          labels      = tomap({})
          auto_accept = ["$project_ids:hub"]
        }
        edge = {
          description = "Environment workload spoke VPCs."
          labels      = tomap({})
          auto_accept = [
            for k in sort(keys(var.envs_folders)) :
            "$project_ids:${lower(k)}"
          ]
        }
      }
      spokes = {
        vpcs              = local._default_ncc_spokes_vpcs
        tunnels           = {}
        vlan_attachments  = {}
        router_appliances = {}
      }
    }
  }
}

module "hub-project" {
  source = "../../../modules/project"
  providers = {
    google      = google.billing
    google-beta = google-beta.billing
  }
  billing_account = var.billing_account.id
  name            = "net-hub-host"
  lien_reason     = "Protected by default as a core project."
  parent          = var.folder_ids.networking
  prefix          = var.prefix
  services = concat([
    "compute.googleapis.com",
    "certificatemanager.googleapis.com",
    "dns.googleapis.com",
    "iap.googleapis.com",
    "networkmanagement.googleapis.com",
    "networksecurity.googleapis.com",
    "networkservices.googleapis.com",
    "servicedirectory.googleapis.com",
    "stackdriver.googleapis.com",
    "cloudkms.googleapis.com"
  ], local._ncc_enabled ? ["networkconnectivity.googleapis.com"] : [])
  shared_vpc_host_config = {
    enabled = true
  }
  iam = {
    "roles/dns.admin" = compact([
      try(local.service_accounts.project-factory-prod, null)
    ])
    (local.custom_roles.service_project_network_admin) = compact([
      try(local.service_accounts.project-factory-prod, null)
    ])
  }
}

resource "google_compute_project_metadata" "metadata_hub_project" {
  project = module.hub-project.project_id
  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
    enable-oslogin         = true # CIS Compliance Benchmark 4.4
  }
}

module "hub-vpc" {
  source                            = "../../../modules/net-vpc"
  project_id                        = module.hub-project.project_id
  name                              = "hub-0"
  delete_default_routes_on_create   = true
  firewall_policy_enforcement_order = "BEFORE_CLASSIC_FIREWALL"
  mtu                               = 1500
  subnets                           = try(var.subnets.hub, [])
  dns_policy = {
    inbound = true
    logging = var.dns.enable_logging
  }
  create_googleapis_routes = (
    var.psc_google_apis.enabled
    ? null
    : {
      private    = true
      restricted = true
    }
  )
  routes = local._default_egress_routes
}

module "hub-firewall-policy" {
  source    = "../../../modules/net-firewall-policy"
  name      = "${var.prefix}-hub-fw-policy-0"
  parent_id = module.hub-project.project_id
  region    = "global"
  attachments = {
    hub-0 = module.hub-vpc.id
  }
  security_profile_group_ids = var.security_profile_group_ids
  factories_config = {
    cidr_file_path = "${var.factories_config.data_dir}/cidrs.yaml"
    egress_rules_file_path = (
      "${var.factories_config.data_dir}/firewall-policies/hub-egress.yaml"
    )
    ingress_rules_file_path = (
      "${var.factories_config.data_dir}/firewall-policies/hub-ingress.yaml"
    )
  }
  ingress_rules = lookup(local._expanded_fw_ingress, "hub", {})
  egress_rules  = lookup(local._expanded_fw_egress, "hub", {})
}

module "hub-nat" {
  for_each = (
    var.enable_cloud_nat && !var.centralized_egress.enabled ? var.regions : {}
  )
  source         = "../../../modules/net-cloudnat"
  project_id     = module.hub-project.project_id
  region         = each.value
  name           = "hub-nat-${each.value}"
  router_create  = true
  router_name    = "hub-nat-${each.value}"
  router_network = module.hub-vpc.name
}

module "hub-dns-priv-gcp" {
  source     = "../../../modules/dns"
  project_id = module.hub-project.project_id
  name       = "org-domain"
  zone_config = {
    domain = lower("${var.organization.domain}.")
    private = {
      client_networks = [module.hub-vpc.self_link]
    }
  }
  recordsets = {
    "A localhost" = { records = ["127.0.0.1"] }
  }
}

module "hub-dns-policy-googleapis" {
  source     = "../../../modules/dns-response-policy"
  project_id = module.hub-project.project_id
  name       = "googleapis"
  rules      = local._psc_hub_dns_rules
  networks = {
    hub = module.hub-vpc.self_link
  }
}
