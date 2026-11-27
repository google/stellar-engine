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
  # The spoke VPC module already creates the service networking connection
  # for environments with PSA ranges, so the default allocation only covers
  # the remaining ones. The condition mirrors the psa_configs expression
  # passed to the spoke VPC module, including its fallback to the dev ranges.
  psa_default_envs = {
    for k, v in var.envs_folders : k => v
    if length(try(
      var.psa_ranges[lower(k)],
      var.psa_ranges[k],
      var.psa_ranges["dev"],
      []
    )) == 0
  }
}

resource "google_compute_global_address" "private_service_connect_ip" {
  for_each = local.psa_default_envs

  project       = module.env-spoke-vpc[each.key].project_id
  name          = "default-peering"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 22
  network       = module.env-spoke-vpc[each.key].self_link
}

resource "google_service_networking_connection" "default" {
  for_each                = local.psa_default_envs
  network                 = module.env-spoke-vpc[each.key].self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_connect_ip[each.key].name]
}
