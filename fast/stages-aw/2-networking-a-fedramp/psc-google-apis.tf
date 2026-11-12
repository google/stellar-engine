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

# tfdoc:file:description Per-VPC Private Service Connect endpoints for APIs.

locals {
  _sorted_env_keys = sort(keys(var.envs_folders))
  _psc_spoke_ips = {
    for idx, k in local._sorted_env_keys : k => lookup(
      var.psc_google_apis.spoke_ips,
      k,
      lookup(
        var.psc_google_apis.spoke_ips,
        lower(k),
        cidrhost("10.255.255.0/24", 10 + idx)
      )
    )
  }
  _psc_spoke_fr_names = {
    for k in keys(var.envs_folders) : k => substr(
      "psc${replace(lower(k), "/[^a-z0-9]/", "")}0",
      0,
      20
    )
  }
  _dns_rules_file_candidate = coalesce(
    var.factories_config.dns_policy_rules_file,
    "${var.factories_config.data_dir}/dns-policy-rules.yaml"
  )
  _dns_policy_rules_file = (
    fileexists(pathexpand(local._dns_rules_file_candidate))
    ? local._dns_rules_file_candidate
    : (
      fileexists("${path.module}/data/dns-policy-rules.yaml")
      ? "${path.module}/data/dns-policy-rules.yaml"
      : null
    )
  )
  _dns_policy_context = {
    addresses = {
      googleapis_cname = (
        var.psc_google_apis.enabled && var.psc_google_apis.bundle == "vpc-sc"
        ? "restricted.googleapis.com."
        : "private.googleapis.com."
      )
    }
  }
  _psc_ips_by_vpc = !var.psc_google_apis.enabled ? {} : merge(
    { hub = var.psc_google_apis.hub_ip },
    local._egress_psc_enabled ? { egress = var.psc_google_apis.egress_ip } : {},
    local._psc_spoke_ips
  )
  _psc_dns_rules_by_vpc = {
    for vpc_key, ip in local._psc_ips_by_vpc : vpc_key => merge(
      var.dns_policy_rules,
      {
        googleapis-private = {
          dns_name   = "private.googleapis.com."
          behavior   = "bypassResponsePolicy"
          local_data = { A = { ttl = tonumber(null), rrdatas = [ip] } }
        }
        googleapis-restricted = {
          dns_name   = "restricted.googleapis.com."
          behavior   = "bypassResponsePolicy"
          local_data = { A = { ttl = tonumber(null), rrdatas = [ip] } }
        }
      }
    )
  }
  _psc_hub_dns_rules = lookup(
    local._psc_dns_rules_by_vpc, "hub", var.dns_policy_rules
  )
  _psc_egress_dns_rules = lookup(
    local._psc_dns_rules_by_vpc, "egress", var.dns_policy_rules
  )
  _psc_spoke_dns_rules = {
    for k in keys(var.envs_folders) : k => lookup(
      local._psc_dns_rules_by_vpc, k, var.dns_policy_rules
    )
  }
}

# Central Hub VPC PSC Endpoint for Google APIs (also serves on-prem via inbound
# DNS forwarding and Cloud Router route advertisement).

module "hub-psc-addresses" {
  count      = var.psc_google_apis.enabled ? 1 : 0
  source     = "../../../modules/net-address"
  project_id = module.hub-project.project_id
  psc_addresses = {
    pschub0 = {
      address = var.psc_google_apis.hub_ip
      network = module.hub-vpc.self_link
      service_attachment = {
        psc_service_attachment_link = var.psc_google_apis.bundle
        service_directory_registration = (
          var.psc_google_apis.service_directory_registration
        )
      }
    }
  }
}

# Environment Spoke VPC PSC Endpoints for Google APIs (one per spoke VPC
# because PSC endpoints for Google APIs are not transitive across NCC).

module "env-psc-addresses" {
  for_each   = var.psc_google_apis.enabled ? var.envs_folders : {}
  source     = "../../../modules/net-address"
  project_id = module.env-spoke-projects[each.key].project_id
  psc_addresses = {
    (local._psc_spoke_fr_names[each.key]) = {
      address = local._psc_spoke_ips[each.key]
      network = module.env-spoke-vpc[each.key].self_link
      service_attachment = {
        psc_service_attachment_link = var.psc_google_apis.bundle
        service_directory_registration = (
          var.psc_google_apis.service_directory_registration
        )
      }
    }
  }
}

module "env-dns-policy-googleapis" {
  for_each   = var.psc_google_apis.enabled ? var.envs_folders : {}
  source     = "../../../modules/dns-response-policy"
  project_id = module.env-spoke-projects[each.key].project_id
  name       = lower("${each.key}-googleapis")
  context    = local._dns_policy_context
  factories_config = {
    rules = local._dns_policy_rules_file
  }
  rules = local._psc_spoke_dns_rules[each.key]
  networks = {
    (lower(each.key)) = module.env-spoke-vpc[each.key].self_link
  }
}
