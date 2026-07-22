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
# tfdoc:file:description VPCs, Firewalls, NATs, and Routes.

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
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/dmz"
  }
}

module "dmz-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.dmz-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/dmz"
  }
}

# Landing (trusted) VPC
module "vdss-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "vdss-landing-0"
  delete_default_routes_on_create = true
  mtu                             = 1500
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/landing"
  }
  dns_policy = {
    inbound = true
    logging = var.dns.enable_logging
  }
  create_googleapis_routes = null
}

module "vdss-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.vdss-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/vdss"
  }
}

# Mgmt (trusted) VPC
module "mgmt-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "vdss-mgmt-0"
  delete_default_routes_on_create = true
  mtu                             = 1500
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/mgmt"
  }
  dns_policy = {
    inbound = true
    logging = var.dns.enable_logging
  }
  psa_configs = [{
    ranges = {
      redis = "10.84.130.0/24"
    }
  }]
  create_googleapis_routes = null
}

module "mgmt-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.mgmt-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/mgmt"
  }
}

# CSP Landing VPC
module "csp-landing-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "csp-landing"
  delete_default_routes_on_create = true
  mtu                             = 1500
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/csp"
  }
}

module "csp-spoke-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.csp-landing-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/csp"
  }
}

# BCAP Spoke VPC
module "bcap-spoke-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "bcap-landing"
  delete_default_routes_on_create = true
  mtu                             = 1500
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/bcap"
  }
}

module "bcap-spoke-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.bcap-spoke-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/bcap"
  }
}

# Interconnect Spoke VPC
module "interconnect-spoke-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "interconnect-landing"
  delete_default_routes_on_create = true
  mtu                             = 1500
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/interconnect"
  }
}

module "interconnect-spoke-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.interconnect-spoke-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/interconnect"
  }
}

# --- Hub VPCs (Internal Environment Hubs) ---

# Dev Hub VPC
module "tenant-transit-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "tenant-transit"
  delete_default_routes_on_create = true
  mtu                             = 1500
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/transit"
  }
}

module "tenant-transit-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.tenant-transit-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/transit"
  }
}

# Shared Services VPC
module "shared-services-vpc" {
  source                          = "../../../modules/net-vpc"
  project_id                      = module.vdss-host-project.project_id
  name                            = "shared-services"
  delete_default_routes_on_create = true
  mtu                             = 1500
  factories_config = {
    context        = { regions = var.regions }
    subnets_folder = "${var.factories_config.data_dir}/subnets/sharedsvcs"
  }
  subnets_proxy_only = [{
    region        = var.regions.primary
    active        = true
    name          = lower("sharedsvcs-${var.regions.primary}-proxy-0")
    ip_cidr_range = local.proxy_subnets["sharedsvcs"]
  }]
}

module "shared-services-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = module.vdss-host-project.project_id
  network    = module.shared-services-vpc.name
  default_rules_config = {
    disabled = true
  }
  factories_config = {
    cidr_tpl_file = "${var.factories_config.data_dir}/cidrs.yaml"
    rules_folder  = "${var.factories_config.data_dir}/firewall-rules/sharedsvcs"
  }
}

resource "google_compute_route" "shared_svcs_default_route_nva" {
  name       = "shared-svcs-default-route-nva"
  project    = module.vdss-host-project.project_id
  dest_range = "0.0.0.0/0"
  network    = module.shared-services-vpc.self_link

  next_hop_ilb = module.ilb-nva-vdss[var.regions.primary].forwarding_rules[""].ip_address
  priority     = 100

  depends_on = [
    google_network_connectivity_spoke.landing,
    google_network_connectivity_spoke.sharedsvcs
  ]
}

# --- Routes ---

resource "google_compute_route" "mgmt-default" {
  name             = "default-route-mgmt"
  project          = module.vdss-host-project.project_id
  dest_range       = "0.0.0.0/0"
  network          = module.mgmt-vpc.name
  next_hop_gateway = "default-internet-gateway"
  priority         = 100
}

resource "google_compute_route" "csp_spoke_default" {
  name         = "csp-spoke-default-route-nva"
  project      = module.vdss-host-project.project_id
  dest_range   = "0.0.0.0/0"
  network      = module.csp-landing-vpc.self_link
  next_hop_ilb = module.ilb-nva-vdss[var.regions.primary].forwarding_rules[""].ip_address
  priority     = 10
  depends_on = [
    google_network_connectivity_spoke.landing,
    google_network_connectivity_spoke.csp_spoke
  ]
}

resource "google_compute_route" "bcap_spoke_default" {
  name         = "bcap-spoke-default-route-nva"
  project      = module.vdss-host-project.project_id
  dest_range   = "0.0.0.0/0"
  network      = module.bcap-spoke-vpc.self_link
  next_hop_ilb = module.ilb-nva-bcap[var.regions.primary].forwarding_rules[""].id
  priority     = 10
  depends_on = [
    google_network_connectivity_spoke.landing,
    google_network_connectivity_spoke.bcap_spoke
  ]
}

resource "google_compute_route" "interconnect_spoke_default" {
  name         = "interconnect-spoke-default-route-nva"
  project      = module.vdss-host-project.project_id
  dest_range   = "0.0.0.0/0"
  network      = module.interconnect-spoke-vpc.self_link
  next_hop_ilb = module.ilb-nva-interconnect[var.regions.primary].forwarding_rules[""].id
  priority     = 10
  depends_on = [
    google_network_connectivity_spoke.landing,
    google_network_connectivity_spoke.interconnect_spoke
  ]
}

# --- NAT ---

module "dmz-nat-primary" {
  source         = "../../../modules/net-cloudnat"
  project_id     = module.vdss-host-project.project_id
  region         = var.regions.primary
  name           = "nat-${var.regions.primary}"
  router_create  = true
  router_name    = "prod-nat-${var.regions.primary}"
  router_network = module.dmz-vpc.name
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

# --- PSC & Service Networking ---
resource "google_compute_global_address" "psc_googleapis" {
  name         = "psc-googleapis"
  project      = module.vdss-host-project.project_id
  address_type = "INTERNAL"
  purpose      = "PRIVATE_SERVICE_CONNECT"
  network      = module.vdss-vpc.self_link
  address      = "10.84.255.255"
}

resource "google_compute_global_forwarding_rule" "psc_googleapis" {
  name                  = "pscapis"
  project               = module.vdss-host-project.project_id
  target                = "vpc-sc"
  network               = module.vdss-vpc.self_link
  ip_address            = google_compute_global_address.psc_googleapis.id
  load_balancing_scheme = ""
}
