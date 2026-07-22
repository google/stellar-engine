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

provider "google" {
  alias   = "host_network"
  project = var.net_project
}

resource "google_compute_firewall" "gitlab_health_checks" {
  provider = google.host_network

  name    = "allow-gitlab-health-checks"
  network = var.network
  project = var.net_project

  priority  = 1000
  direction = "INGRESS"

  source_ranges = [
    "35.191.0.0/16",   # Google LB Health Checks (Global)
    "130.211.0.0/22",  # Google LB Health Checks (Regional)
    "209.85.152.0/22", # Google Cloud Uptime Checks (Monitoring)
    "209.85.204.0/22"  # Google Cloud Uptime Checks (Monitoring)
  ]

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8443", "10256"]
  }

  target_service_accounts = [google_service_account.gitlab-sa.email]
}

resource "google_compute_firewall" "allow_gitlab_external_access" {
  provider = google.host_network

  name    = "allow-gitlab-external-access"
  network = var.network
  project = var.net_project

  priority  = 1000
  direction = "INGRESS"

  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  target_service_accounts = [google_service_account.gitlab-sa.email]
}
