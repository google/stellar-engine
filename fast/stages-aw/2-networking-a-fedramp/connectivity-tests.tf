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

locals {
}
resource "google_network_management_connectivity_test" "landing-test" {
  for_each = var.regions

  name    = "landing-subnet-test-${each.key}"
  project = module.vdss-host-project.project_id

  source {
    ip_address   = google_compute_address.source-addr[each.key].address
    project_id   = module.vdss-host-project.project_id
    network      = module.vdss-vpc.id
    network_type = "GCP_NETWORK"
  }
  destination {
    ip_address = "8.8.8.8"
    port       = 443
  }

  protocol = "TCP"
  labels = {
    env = "vdss"
  }
}

resource "google_compute_address" "source-addr" {
  project = module.vdss-host-project.project_id

  for_each     = var.regions
  name         = "landing-test-addr-${each.value}"
  subnetwork   = try(module.vdss-vpc.subnet_self_links["${each.value}/landing-default"], null)
  address_type = "INTERNAL"
  region       = each.value
}


resource "google_network_management_connectivity_test" "env-tests" {
  for_each = var.envs_folders

  name    = lower("${each.key}-host-project-test")
  project = module.env-spoke-projects[each.key].project_id

  source {
    ip_address   = google_compute_address.env-source-addrs[each.key].address
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
resource "google_compute_address" "env-source-addrs" {
  for_each = var.envs_folders

  project = module.env-spoke-projects[each.key].project_id

  name         = lower("${each.key}-test-addr")
  subnetwork   = module.env-spoke-vpc[each.key].subnets["${var.regions.primary}/${[for s in try(var.subnets[lower(each.key)], []) : s.name if s.tenant != null][0]}"].self_link
  address_type = "INTERNAL"
  region       = var.regions.primary
  depends_on   = [module.env-spoke-vpc]
}


# # These tests should fail
## This isn't doing what I want it to, but I really like the idea of having something like this to test for route leaking between the envs

# resource "google_network_management_connectivity_test" "fail-env-tests" {
#   for_each = var.envs_folders

#   name    = lower("must-fail-${each.key}-prod")
#   project = module.env-spoke-projects[each.key].project_id

#   source {
#     ip_address   = google_compute_address.env-source-addrs[each.key].address
#     project_id   = module.env-spoke-projects[each.key].project_id
#     network      = module.env-spoke-vpc[each.key].id
#     network_type = "GCP_NETWORK"
#   }
#   destination {
#     ip_address = google_compute_address.env-source-addrs["Prod"].address
#     project_id = module.env-spoke-projects["Prod"].project_id
#     network    = module.env-spoke-vpc["Prod"].id
#     port       = 443
#   }

#   protocol = "TCP"

# }