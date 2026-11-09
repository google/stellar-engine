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

# tfdoc:file:description Optional centralized SWP next-hop Internet Egress VPC.

locals {
  _egress_psc_enabled = (
    var.centralized_egress.enabled && var.psc_google_apis.enabled
  )
  _egress_swp_ports = [
    for p in var.centralized_egress.ports : tostring(p)
  ]
  _egress_swp_subnet_id = try(
    module.egress-vpc[0].subnets["${var.regions.primary}/egress-swp-0"].id,
    null
  )
  _egress_default_ingress = {
    allow-swp-from-internal = {
      priority       = 1000
      action         = "allow"
      description    = "Allow spoke VPC traffic to Secure Web Proxy next-hop."
      enable_logging = true
      match = {
        source_ranges = lookup(
          var.cidrs,
          "rfc1918",
          ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
        )
        layer4_configs = [
          {
            protocol = "tcp"
            ports    = local._egress_swp_ports
          }
        ]
      }
    }
  }
}

module "egress-vpc" {
  count                             = var.centralized_egress.enabled ? 1 : 0
  source                            = "../../../modules/net-vpc"
  project_id                        = module.hub-project.project_id
  name                              = "egress-0"
  delete_default_routes_on_create   = true
  firewall_policy_enforcement_order = "BEFORE_CLASSIC_FIREWALL"
  mtu                               = 1500
  dns_policy = {
    logging = var.dns.enable_logging
  }
  create_googleapis_routes = (
    var.psc_google_apis.enabled
    ? null
    : {
      directpath = false
      private    = true
      restricted = true
    }
  )
  subnets = [
    {
      name                  = "egress-swp-0"
      ip_cidr_range         = var.centralized_egress.subnet_cidr
      region                = var.regions.primary
      description           = "Secure Web Proxy next-hop egress subnet."
      enable_private_access = true
    }
  ]
  subnets_proxy_only = [
    {
      name          = lower("proxy-${var.regions.primary}")
      ip_cidr_range = var.centralized_egress.proxy_subnet_cidr
      region        = var.regions.primary
      active        = true
    }
  ]
  routes = {
    default = {
      dest_range    = "0.0.0.0/0"
      next_hop      = "default-internet-gateway"
      next_hop_type = "gateway"
      priority      = 1000
    }
  }
}

module "egress-firewall-policy" {
  count     = var.centralized_egress.enabled ? 1 : 0
  source    = "../../../modules/net-firewall-policy"
  name      = "${var.prefix}-egress-fw-policy-0"
  parent_id = module.hub-project.project_id
  region    = "global"
  attachments = {
    egress-0 = module.egress-vpc[0].id
  }
  security_profile_group_ids = var.security_profile_group_ids
  factories_config = {
    cidr_file_path = "${var.factories_config.data_dir}/cidrs.yaml"
    egress_rules_file_path = (
      "${var.factories_config.data_dir}/firewall-policies/egress-egress.yaml"
    )
    ingress_rules_file_path = (
      "${var.factories_config.data_dir}/firewall-policies/egress-ingress.yaml"
    )
  }
  ingress_rules = merge(
    local._egress_default_ingress,
    lookup(local._expanded_fw_ingress, "egress", {})
  )
  egress_rules = lookup(local._expanded_fw_egress, "egress", {})
}

module "egress-nat" {
  count          = var.centralized_egress.enabled ? 1 : 0
  source         = "../../../modules/net-cloudnat"
  project_id     = module.hub-project.project_id
  region         = var.regions.primary
  name           = "egress-swp-nat-${var.regions.primary}"
  endpoint_types = ["ENDPOINT_TYPE_SWG"]
  router_create  = true
  router_name    = "egress-swp-nat-${var.regions.primary}"
  router_network = module.egress-vpc[0].name
}

module "egress-swp" {
  count        = var.centralized_egress.enabled ? 1 : 0
  source       = "../../../modules/net-swp"
  project_id   = module.hub-project.project_id
  region       = var.regions.primary
  name         = "egress-swp-0"
  network      = module.egress-vpc[0].id
  subnetwork   = local._egress_swp_subnet_id
  certificates = var.centralized_egress.certificates
  gateway_config = {
    addresses             = [var.centralized_egress.swp_ip]
    next_hop_routing_mode = true
    ports                 = local._egress_swp_ports
  }
  factories_config = {
    policy_rules = "${var.factories_config.data_dir}/swp-policy-rules"
    url_lists    = "${var.factories_config.data_dir}/swp-url-lists"
  }
  policy_rules = var.centralized_egress.policy_rules
  url_lists    = var.centralized_egress.url_lists
}

module "egress-psc-addresses" {
  count      = local._egress_psc_enabled ? 1 : 0
  source     = "../../../modules/net-address"
  project_id = module.hub-project.project_id
  psc_addresses = {
    pscegress0 = {
      address = var.psc_google_apis.egress_ip
      network = module.egress-vpc[0].self_link
      service_attachment = {
        psc_service_attachment_link = var.psc_google_apis.bundle
      }
    }
  }
}

module "egress-dns-priv-psc" {
  count      = local._egress_psc_enabled ? 1 : 0
  source     = "../../../modules/dns"
  project_id = module.hub-project.project_id
  name       = "egress-psc-googleapis"
  zone_config = {
    domain = "p.googleapis.com."
    private = {
      client_networks = [module.egress-vpc[0].self_link]
    }
  }
  recordsets = {
    "A *" = { records = [var.psc_google_apis.egress_ip] }
  }
}

module "egress-dns-policy-googleapis" {
  count      = local._egress_psc_enabled ? 1 : 0
  source     = "../../../modules/dns-response-policy"
  project_id = module.hub-project.project_id
  name       = "egress-googleapis"
  rules      = local._psc_egress_dns_rules
  networks = {
    egress = module.egress-vpc[0].self_link
  }
}
