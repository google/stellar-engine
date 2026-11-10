/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

# tfdoc:file:description Network Management connectivity tests and addresses.

locals {
  _hub_test_regions = !local._has_internet_egress ? {} : {
    for k, r in var.regions : k => r
    if length([for s in try(var.subnets.hub, []) : s.name if s.region == r]) > 0
  }
  _hub_test_internal_addrs = {
    for k, r in local._hub_test_regions : "hub-test-addr-${r}" => {
      region = r
      subnetwork = module.hub-vpc.subnet_self_links[
        "${r}/${[for s in var.subnets.hub : s.name if s.region == r][0]}"
      ]
    }
  }
  _env_test_subnet_links = {
    for k in keys(var.envs_folders) : k => module.env-spoke-vpc[k].subnets[
      "${var.regions.primary}/${[
        for s in try(var.subnets[lower(k)], []) :
        s.name if s.tenant != null
      ][0]}"
    ].self_link
  }
}

module "hub-test-addresses" {
  count              = length(local._hub_test_internal_addrs) > 0 ? 1 : 0
  source             = "../../../modules/net-address"
  project_id         = module.hub-project.project_id
  internal_addresses = local._hub_test_internal_addrs
}

resource "google_network_management_connectivity_test" "hub_test" {
  for_each = local._hub_test_regions

  name    = "hub-subnet-test-${each.key}"
  project = module.hub-project.project_id

  source {
    ip_address = (
      module.hub-test-addresses[0]
      .internal_addresses["hub-test-addr-${each.value}"]
      .address
    )
    project_id   = module.hub-project.project_id
    network      = module.hub-vpc.id
    network_type = "GCP_NETWORK"
  }
  destination {
    ip_address = "8.8.8.8"
    port       = 443
  }

  protocol = "TCP"
  labels = {
    env = "hub"
  }
}

module "env-test-addresses" {
  for_each   = local._has_internet_egress ? var.envs_folders : {}
  source     = "../../../modules/net-address"
  project_id = module.env-spoke-projects[each.key].project_id
  internal_addresses = {
    (lower("${each.key}-test-addr")) = {
      region     = var.regions.primary
      subnetwork = local._env_test_subnet_links[each.key]
    }
  }
  depends_on = [module.env-spoke-vpc]
}

resource "google_network_management_connectivity_test" "env_tests" {
  for_each = local._has_internet_egress ? var.envs_folders : {}

  name    = lower("${each.key}-host-project-test")
  project = module.env-spoke-projects[each.key].project_id

  source {
    ip_address = (
      module.env-test-addresses[each.key]
      .internal_addresses[lower("${each.key}-test-addr")]
      .address
    )
    project_id   = module.env-spoke-projects[each.key].project_id
    network      = module.env-spoke-vpc[each.key].id
    network_type = "GCP_NETWORK"
  }
  destination {
    ip_address = "8.8.8.8"
    port       = 443
  }

  protocol = "TCP"
  labels = {
    env = lower(each.key)
  }
}
