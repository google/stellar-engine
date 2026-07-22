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
# tfdoc:file:description DNS zones and policies.

module "landing-dns-zone-private" {
  source     = "../../../modules/dns"
  project_id = module.vdss-host-project.project_id
  name       = lower("${var.prefix}-${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-vdss-org-domain-private")
  zone_config = {
    domain = lower("${var.prefix}-${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-vdss.private.${var.organization.domain}.")
    private = {
      client_networks = [module.vdss-vpc.self_link]
    }
  }
  recordsets = {
    "A localhost" = { records = ["127.0.0.1"] }
  }
}

module "landing-dns-policy-googleapis" {
  source     = "../../../modules/dns-response-policy"
  project_id = module.vdss-host-project.project_id
  name       = "googleapis"
  factories_config = {
    rules = var.factories_config.dns_policy_rules_file
  }
  networks = {
    landing = module.vdss-vpc.self_link
  }
}

