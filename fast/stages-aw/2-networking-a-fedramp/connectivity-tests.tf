# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

resource "google_network_management_connectivity_test" "landing_test" {
  for_each = var.enable_cloud_nat ? var.regions : {}

  name    = "landing-subnet-test-${each.key}"
  project = module.landing-project.project_id

  source {
    ip_address   = google_compute_address.source_addr[each.key].address
    project_id   = module.landing-project.project_id
    network      = module.landing-vpc.id
    network_type = "GCP_NETWORK"
  }
  destination {
    ip_address = "8.8.8.8"
    port       = 443
  }

  protocol = "TCP"
  labels = {
    env = "landing"
  }
}

resource "google_compute_address" "source_addr" {
  for_each     = var.enable_cloud_nat ? var.regions : {}
  project      = module.landing-project.project_id
  name         = "landing-test-addr-${each.value}"
  subnetwork   = try(module.landing-vpc.subnet_self_links["${each.value}/landing-default"], null)
  address_type = "INTERNAL"
  region       = each.value
}

moved {
  from = google_network_management_connectivity_test.env-tests
  to   = google_network_management_connectivity_test.env_tests
}

resource "google_network_management_connectivity_test" "env_tests" {
  for_each = var.enable_cloud_nat ? var.envs_folders : {}

  name    = lower("${each.key}-host-project-test")
  project = module.env-spoke-projects[each.key].project_id

  source {
    ip_address   = google_compute_address.env_source_addrs[each.key].address
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

moved {
  from = google_compute_address.env-source-addrs
  to   = google_compute_address.env_source_addrs
}

resource "google_compute_address" "env_source_addrs" {
  for_each = var.enable_cloud_nat ? var.envs_folders : {}

  project = module.env-spoke-projects[each.key].project_id

  name = lower("${each.key}-test-addr")
  subnetwork = module.env-spoke-vpc[each.key].subnets[
    "${var.regions.primary}/${[for s in try(var.subnets[lower(each.key)], []) : s.name if s.tenant != null][0]}"
  ].self_link
  address_type = "INTERNAL"
  region       = var.regions.primary
  depends_on   = [module.env-spoke-vpc]
}
