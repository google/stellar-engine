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

# tfdoc:file:description Opt-in hybrid Cloud DNS forwarding zones.

locals {
  # When per-VPC PSC is enabled, spoke root DNS peering narrows from "." to
  # "${var.organization.domain}.". Add explicit per-domain peering zones on
  # each spoke so hybrid forwarding zones remain reachable through landing.
  _env_forwarding_zone_peerings = !var.psc_google_apis.enabled ? {} : merge([
    for env_k, _ in var.envs_folders : {
      for fz_k, fz_v in var.dns_forwarding_zones :
      "${lower(env_k)}-${fz_k}" => {
        env_key = env_k
        domain  = lower(fz_v.domain)
        name    = lower("${env_k}-fwd-peer-${fz_k}")
      }
      if lower(fz_v.domain) != lower("${var.organization.domain}.")
    }
  ]...)
}

module "landing-dns-forwarding-zones" {
  source      = "../../../modules/dns"
  for_each    = var.dns_forwarding_zones
  project_id  = module.vdss-host-project.project_id
  name        = lower("fwd-${each.key}")
  description = each.value.description
  context = {
    networks = local._ctx_vpcs
  }
  zone_config = {
    domain = lower(each.value.domain)
    forwarding = {
      forwarders = each.value.forwarders
      client_networks = coalesce(
        each.value.client_networks,
        [module.vdss-vpc.self_link]
      )
    }
  }
}

module "env-dns-peer-forwarding-zones" {
  source     = "../../../modules/dns"
  for_each   = local._env_forwarding_zone_peerings
  project_id = module.env-spoke-projects[each.value.env_key].project_id
  name       = each.value.name
  zone_config = {
    domain = each.value.domain
    peering = {
      client_networks = [module.env-spoke-vpc[each.value.env_key].self_link]
      peer_network    = module.vdss-vpc.self_link
    }
  }
}
