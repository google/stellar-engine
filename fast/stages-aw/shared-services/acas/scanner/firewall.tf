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
# Scanner Management (SSH via IAP)
resource "google_compute_firewall" "acas_scanner_ssh" {
  name    = "acas-scanner-ssh"
  network = data.google_compute_network.network.self_link
  project = var.hub_project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  target_tags   = ["acas-scanner"]
  source_ranges = distinct(concat(var.iap_source_ranges, var.admin_ssh_source_ranges))
}

# Scanner Management (SecurityCenter communication + Nessus Web UI)
resource "google_compute_firewall" "acas_scanner_sc_mgmt" {
  name    = "acas-scanner-sc-mgmt"
  network = data.google_compute_network.network.self_link
  project = var.hub_project_id

  allow {
    protocol = "tcp"
    ports    = ["8834"]
  }

  target_tags   = ["acas-scanner"]
  source_ranges = distinct(concat(var.securitycenter_source_ranges, var.iap_source_ranges))
}

# Scanner to Targets: Outbound scanning traffic
resource "google_compute_firewall" "acas_scanner_to_targets_egress" {
  name      = "acas-scanner-to-targets-egress"
  network   = data.google_compute_network.network.self_link
  project   = var.hub_project_id
  direction = "EGRESS"

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }

  target_tags        = ["acas-scanner"]
  destination_ranges = var.scan_target_destination_ranges
}

# Target Ingress: Inbound scanning traffic from Scanner to scanned hosts
resource "google_compute_firewall" "acas_targets_ingress_from_scanner" {
  name      = "acas-targets-ingress-from-scanner"
  network   = data.google_compute_network.network.self_link
  project   = var.hub_project_id
  direction = "INGRESS"

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }

  source_tags = ["acas-scanner"]
}
