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
# SecurityCenter Management (SSH via IAP)
resource "google_compute_firewall" "acas_sc_ssh" {
  name    = "acas-sc-ssh"
  network = data.google_compute_network.network.self_link
  project = var.hub_project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  target_tags   = ["acas-sc"]
  source_ranges = distinct(concat(var.iap_source_ranges, var.admin_ssh_source_ranges))
}

# SecurityCenter Management (HTTPS Web UI)
resource "google_compute_firewall" "acas_sc_https" {
  name    = "acas-sc-https"
  network = data.google_compute_network.network.self_link
  project = var.hub_project_id

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  target_tags   = ["acas-sc"]
  source_ranges = distinct(concat(var.sc_mgmt_source_ranges, var.iap_source_ranges))
}
