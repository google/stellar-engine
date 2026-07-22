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
resource "google_compute_global_address" "private_service_connect_ip" {
  for_each = var.envs_folders

  project       = module.env-spoke-vpc[each.key].project_id
  name          = "default-peering"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 22
  network       = module.env-spoke-vpc[each.key].self_link
}

resource "google_service_networking_connection" "default" {
  for_each                = var.envs_folders
  network                 = module.env-spoke-vpc[each.key].self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_connect_ip[each.key].name]
}
