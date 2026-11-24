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
  _psc_dns_policy_rules_file = (
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
    local._psc_spoke_ips
  )
  _psc_service_directory_registration = {
    namespace = try(
      var.psc_google_apis.service_directory_registration.namespace,
      null
    )
    region = coalesce(
      try(var.psc_google_apis.service_directory_registration.region, null),
      var.regions.primary
    )
  }
  # Under bundle = "vpc-sc", never alias private.googleapis.com. or non-VPC-SC
  # domains onto the vpc-sc PSC IP because the vpc-sc bundle rejects them.
  _psc_non_vpcsc_bypass_rules = {
    googleapis-private = {
      dns_name   = "private.googleapis.com."
      behavior   = "bypassResponsePolicy"
      local_data = {}
    }
    dl = {
      dns_name   = "dl.google.com."
      behavior   = "bypassResponsePolicy"
      local_data = {}
    }
    gstatic-all = {
      dns_name   = "*.gstatic.com."
      behavior   = "bypassResponsePolicy"
      local_data = {}
    }
    packages-cloud = {
      dns_name   = "packages.cloud.google.com."
      behavior   = "bypassResponsePolicy"
      local_data = {}
    }
    packages-cloud-all = {
      dns_name   = "*.packages.cloud.google.com."
      behavior   = "bypassResponsePolicy"
      local_data = {}
    }
    source = {
      dns_name   = "source.developers.google.com."
      behavior   = "bypassResponsePolicy"
      local_data = {}
    }
  }
  _psc_dns_rules_by_vpc = {
    for vpc_key, ip in local._psc_ips_by_vpc : vpc_key => merge(
      var.dns_policy_rules,
      {
        accounts = {
          dns_name   = "accounts.google.com."
          behavior   = "bypassResponsePolicy"
          local_data = {}
        }
        googleapis-restricted = {
          dns_name   = "restricted.googleapis.com."
          behavior   = "bypassResponsePolicy"
          local_data = { A = { ttl = tonumber(null), rrdatas = [ip] } }
        }
      },
      var.psc_google_apis.bundle == "all-apis"
      ? {
        googleapis-private = {
          dns_name   = "private.googleapis.com."
          behavior   = "bypassResponsePolicy"
          local_data = { A = { ttl = tonumber(null), rrdatas = [ip] } }
        }
      }
      : local._psc_non_vpcsc_bypass_rules
    )
  }
  _psc_hub_dns_rules = lookup(
    local._psc_dns_rules_by_vpc, "hub", var.dns_policy_rules
  )
  _psc_spoke_dns_rules = {
    for k in keys(var.envs_folders) : k => lookup(
      local._psc_dns_rules_by_vpc, k, var.dns_policy_rules
    )
  }
  # Dedicated Private Google Access DNS rules for vdss-mgmt-0 and vdss-dmz-0
  # when landing switches to its local PSC IP, keeping VPC-SC working for the
  # management bastion and NGFW bootstrap traffic.
  _pga_mgmt_dmz_dns_rules = merge(
    var.dns_policy_rules,
    {
      accounts = {
        dns_name   = "accounts.google.com."
        behavior   = "bypassResponsePolicy"
        local_data = {}
      }
      googleapis-private = {
        dns_name = "private.googleapis.com."
        behavior = "bypassResponsePolicy"
        local_data = {
          A = {
            ttl = tonumber(null)
            rrdatas = [
              "199.36.153.8", "199.36.153.9", "199.36.153.10", "199.36.153.11"
            ]
          }
        }
      }
      googleapis-restricted = {
        dns_name = "restricted.googleapis.com."
        behavior = "bypassResponsePolicy"
        local_data = {
          A = {
            ttl = tonumber(null)
            rrdatas = [
              "199.36.153.4", "199.36.153.5", "199.36.153.6", "199.36.153.7"
            ]
          }
        }
      }
    }
  )
}

# Trusted landing hub VPC PSC endpoint for Google APIs (also serves on-prem
# via inbound DNS forwarding and Cloud Router route advertisement).

module "hub-psc-addresses" {
  count      = var.psc_google_apis.enabled ? 1 : 0
  source     = "../../../modules/net-address"
  project_id = module.vdss-host-project.project_id
  psc_addresses = {
    pschub0 = {
      address = var.psc_google_apis.hub_ip
      network = module.vdss-vpc.self_link
      service_attachment = {
        psc_service_attachment_link = var.psc_google_apis.bundle
        service_directory_registration = (
          local._psc_service_directory_registration
        )
      }
    }
  }
}

# Dedicated PGA Cloud DNS response policy for vdss-mgmt-0 and vdss-dmz-0 when
# landing-dns-policy-googleapis scopes to vdss-landing-0's PSC endpoint IP.

module "vdss-mgmt-dmz-dns-policy-googleapis" {
  count      = var.psc_google_apis.enabled ? 1 : 0
  source     = "../../../modules/dns-response-policy"
  project_id = module.vdss-host-project.project_id
  name       = "googleapis-mgmt-dmz"
  context    = local._dns_policy_context
  factories_config = {
    rules = local._psc_dns_policy_rules_file
  }
  rules = local._pga_mgmt_dmz_dns_rules
  networks = {
    dmz  = module.dmz-vpc.self_link
    mgmt = module.mgmt-vpc.self_link
  }
  depends_on = [module.landing-dns-policy-googleapis]
}

# Environment spoke VPC PSC endpoints for Google APIs (one per spoke VPC so
# traffic reaches Google APIs locally without NGFW SNAT hairpinning and without
# relying on non-transitive NCC or peering PSC forwarding).

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
          local._psc_service_directory_registration
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
    rules = local._psc_dns_policy_rules_file
  }
  rules = local._psc_spoke_dns_rules[each.key]
  networks = {
    (lower(each.key)) = module.env-spoke-vpc[each.key].self_link
  }
}
