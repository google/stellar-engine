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
module "cloud_ids" {
  source                       = "../../../modules/intrusion-detection-system"
  project                      = var.network_project_id
  landing_vpc_network          = var.network_name # Duplicate variable (landing_network)
  network_region               = var.region
  network_zone                 = data.google_compute_zones.available.names[0]
  landing_network              = var.network_name # Duplicate variable (landing_vpc_network)
  subnet                       = var.subnetwork_name
  subnet_list                  = var.subnetwork_list
  ids_private_ip_range_name    = "${var.prefix}-ids-private-address"
  ids_private_ip_prefix_length = var.ids_private_ip_prefix_length
  ids_name                     = "${var.prefix}-${var.ids_name}"
  severity                     = var.severity
  packet_mirroring_policy_name = "${var.prefix}-${var.packet_mirroring_policy_name}"

  depends_on = [google_project_service.net-host-services]
}