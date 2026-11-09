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

# tfdoc:file:description Landing VPC, Cloud NAT, DNS, and default NCC hub.

locals {
  _hub_project_id = module.landing-project.project_id
  _hub_project_aliases = {
    landing       = module.landing-project.project_id
    landing-host  = module.landing-project.project_id
    net-landing-0 = module.landing-project.project_id
  }
  _hub_vpcs = {
    landing = module.landing-vpc.self_link
  }
  _default_ncc_spokes_vpcs = merge(
    {
      landing = {
        vpc                   = "$vpcs:landing"
        name                  = "landing-0"
        project_id            = "$project_ids:landing"
        group                 = "$ncc_groups:landing/center"
        description           = "Landing VPC spoke."
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
        group                 = "$ncc_groups:landing/edge"
        description           = "${k} environment spoke VPC."
        labels                = tomap({})
        exclude_export_ranges = tolist(null)
        include_export_ranges = tolist(null)
      }
    }
  )
  _default_ncc_hubs = !var.enable_default_ncc_hub ? {} : {
    landing = {
      project_id      = "$project_ids:landing"
      description     = "Default Stage 2 landing and environment NCC hub."
      export_psc      = true
      policy_mode     = "PRESET"
      preset_topology = "STAR"
      labels          = tomap({})
      groups = {
        center = {
          description = "Central landing and hybrid connectivity spokes."
          labels      = tomap({})
          auto_accept = ["$project_ids:landing"]
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

module "landing-project" {
  source = "../../../modules/project"
  providers = {
    google      = google.billing
    google-beta = google-beta.billing
  }
  billing_account = var.billing_account.id
  name            = "net-landing-0"
  lien_reason     = "Protected by default as a core project."
  parent          = var.folder_ids.networking
  prefix          = var.prefix
  services = concat([
    "compute.googleapis.com",
    "certificatemanager.googleapis.com",
    "dns.googleapis.com",
    "iap.googleapis.com",
    "networkmanagement.googleapis.com",
    "stackdriver.googleapis.com",
    "networkservices.googleapis.com",
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

resource "google_compute_project_metadata" "metadata_landing_project" {
  project = module.landing-project.project_id
  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
    enable-oslogin         = true # CIS Compliance Benchmark 4.4
  }
}

module "landing-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.landing-project.project_id
  name                            = "landing-0"
  delete_default_routes_on_create = true
  mtu                             = 1500
  subnets                         = try(var.subnets.landing, [])
  dns_policy = {
    inbound = true
    logging = var.dns.enable_logging
  }
  create_googleapis_routes = {
    private    = true
    restricted = true
  }
  routes = var.enable_cloud_nat ? {
    default = {
      dest_range    = "0.0.0.0/0"
      next_hop      = "default-internet-gateway"
      next_hop_type = "gateway"
      priority      = 1000
    }
  } : {}
}

module "landing-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.landing-project.project_id
  network    = module.landing-vpc.name
  default_rules_config = {
    disabled = true
  }
  named_ranges  = var.cidrs
  ingress_rules = try(var.firewall_rules.landing.ingress, {})
  egress_rules  = try(var.firewall_rules.landing.egress, {})
}

module "landing-nat" {
  for_each       = var.enable_cloud_nat ? var.regions : {}
  source         = "../../../modules/net-cloudnat"
  project_id     = module.landing-project.project_id
  region         = each.value
  name           = "landing-nat-${each.value}"
  router_create  = true
  router_name    = "landing-nat-${each.value}"
  router_network = module.landing-vpc.name
}

module "landing-dns-priv-gcp" {
  source     = "../../../modules/dns"
  project_id = module.landing-project.project_id
  name       = "org-domain"
  zone_config = {
    domain = lower("${var.organization.domain}.")
    private = {
      client_networks = [module.landing-vpc.self_link]
    }
  }
  recordsets = {
    "A localhost" = { records = ["127.0.0.1"] }
  }
}

module "landing-dns-policy-googleapis" {
  source     = "../../../modules/dns-response-policy"
  project_id = module.landing-project.project_id
  name       = "googleapis"
  rules      = var.dns_policy_rules
  networks = {
    landing = module.landing-vpc.self_link
  }
}
