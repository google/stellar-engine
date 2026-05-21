/**
 * Copyright 2024 Google LLC
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

# tfdoc:file:description Landing VPC and related resources.

module "vdss-host-project" {
  source = "../../../modules/project"
  providers = {
    google      = google.billing
    google-beta = google-beta.billing
  }
  billing_account = var.billing_account.id
  name            = "net-vdss-host"
  lien_reason     = "Protected by default as a core project."
  parent          = var.folder_ids.networking
  prefix          = var.prefix
  services = [
    "compute.googleapis.com",
    "certificatemanager.googleapis.com",
    "dns.googleapis.com",
    "iap.googleapis.com",
    "networkmanagement.googleapis.com",
    "stackdriver.googleapis.com",
    "networkservices.googleapis.com",
    "cloudkms.googleapis.com"
  ]
  shared_vpc_host_config = {
    enabled = true
  }
  iam = {
    "roles/dns.admin" = compact([
      try(local.service_accounts.project-factory-prod, null)
    ])
  }
}

resource "google_compute_project_metadata" "metadata-vdss-host-project" {
  project = module.vdss-host-project.project_id
  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
    enable-oslogin         = true # CIS Compliance Benchmark 4.4
  }
}

# DMZ (untrusted) VPC
module "dmz-vpc" {
  source     = "../../../modules/net-vpc"
  project_id = module.vdss-host-project.project_id
  name       = "vdss-dmz-0"
  mtu        = 1500
  dns_policy = {
    inbound = true
    logging = var.dns.enable_logging
  }
  create_googleapis_routes = null
  subnets                  = try(var.subnets.dmz, [])
}

module "dmz-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.dmz-vpc.name
  default_rules_config = {
    disabled = true
  }
  named_ranges  = var.cidrs
  ingress_rules = try(var.firewall_rules.dmz.ingress, {})
  egress_rules  = try(var.firewall_rules.dmz.egress, {})
}


# Landing (trusted) VPC
module "vdss-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "vdss-landing-0"
  delete_default_routes_on_create = true
  mtu                             = 1500
  subnets                         = try(var.subnets.landing, [])
  dns_policy = {
    inbound = true
    logging = var.dns.enable_logging
  }
  # Set explicit routes for googleapis in case the default route is deleted
  create_googleapis_routes = {
    private    = true
    restricted = true
  }
}

module "vdss-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.vdss-vpc.name
  default_rules_config = {
    disabled = true
  }
  named_ranges  = var.cidrs
  ingress_rules = try(var.firewall_rules.vdss.ingress, {})
  egress_rules  = try(var.firewall_rules.vdss.egress, {})
}

# Mgmt (trusted) VPC
module "mgmt-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "vdss-mgmt-0"
  delete_default_routes_on_create = true
  mtu                             = 1500
  subnets                         = try(var.subnets.mgmt, [])
  dns_policy = {
    inbound = true
    logging = var.dns.enable_logging
  }
  # Set explicit routes for googleapis in case the default route is deleted
  create_googleapis_routes = {
    private    = true
    restricted = true
  }
}

module "mgmt-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.mgmt-vpc.name
  default_rules_config = {
    disabled = true
  }
  named_ranges  = var.cidrs
  ingress_rules = try(var.firewall_rules.mgmt.ingress, {})
  egress_rules  = try(var.firewall_rules.mgmt.egress, {})
}


# NAT
module "dmz-nat-primary" {
  source         = "../../../modules/net-cloudnat"
  project_id     = module.vdss-host-project.project_id
  region         = var.regions.primary
  name           = "nat-${var.regions.primary}"
  router_create  = true
  router_name    = "prod-nat-${var.regions.primary}"
  router_network = module.dmz-vpc.name
}

resource "google_compute_route" "mgmt-default" {
  name             = "default-route-mgmt"
  project          = module.vdss-host-project.project_id
  dest_range       = "0.0.0.0/0"
  network          = module.mgmt-vpc.name
  next_hop_gateway = "default-internet-gateway"
  priority         = 100
}

module "dmz-nat-mgmt" {
  source         = "../../../modules/net-cloudnat"
  project_id     = module.vdss-host-project.project_id
  region         = var.regions.primary
  name           = "nat-mgmt-${var.regions.primary}"
  router_create  = true
  router_name    = "prod-nat-mgmt-${var.regions.primary}"
  router_network = module.mgmt-vpc.name
}

#DNS
module "landing-dns-priv-gcp" {
  source     = "../../../modules/dns"
  project_id = module.vdss-host-project.project_id
  name       = "org-domain"
  zone_config = {
    domain = lower("${var.organization.domain}.")
    private = {
      client_networks = [module.vdss-vpc.self_link]
    }
  }
  recordsets = {
    "A localhost" = { records = ["127.0.0.1"] }
  }
}

# Google APIs via response policies

module "landing-dns-policy-googleapis" {
  source     = "../../../modules/dns-response-policy"
  project_id = module.vdss-host-project.project_id
  name       = "googleapis"
  rules      = var.dns_policy_rules
  networks = {
    landing = module.vdss-vpc.self_link
  }
}
