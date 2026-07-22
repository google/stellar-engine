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
resource "google_compute_firewall" "default" {
  count         = var.firewall_create == true ? 1 : 0
  name          = "${var.name}-allow-ssh"
  project       = var.landing_project_id
  network       = var.network
  source_ranges = [var.ip_allocation]
  target_tags   = ["${var.name}-allow-ssh"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_network_attachment" "psc" {
  count                 = var.connection_type == "PRIVATE_SERVICE_CONNECT_INTERFACES" ? 1 : 0
  name                  = "datafusion-psc-attachment"
  project               = var.project_id
  region                = var.region
  connection_preference = "ACCEPT_AUTOMATIC"
  subnetworks           = [var.subnet]
}

resource "time_sleep" "psc_attachment_propagation" {
  count = var.connection_type == "PRIVATE_SERVICE_CONNECT_INTERFACES" ? 1 : 0

  create_duration = "5m"

  depends_on = [google_compute_network_attachment.psc]
}

resource "google_data_fusion_instance" "default" {
  name                          = var.name
  project                       = var.project_id
  region                        = var.region
  type                          = var.type
  description                   = var.description
  private_instance              = var.private_instance
  labels                        = var.labels
  enable_stackdriver_logging    = var.enable_stackdriver_logging
  enable_stackdriver_monitoring = var.enable_stackdriver_monitoring
  dataproc_service_account      = var.dataproc_service_account

  dynamic "network_config" {
    for_each = var.connection_type == "PRIVATE_SERVICE_CONNECT_INTERFACES" ? [1] : []
    content {
      connection_type = "PRIVATE_SERVICE_CONNECT_INTERFACES"
      private_service_connect_config {
        network_attachment     = google_compute_network_attachment.psc[0].id
        unreachable_cidr_block = var.unreachable_cidr_block
      }
    }
  }

  dynamic "network_config" {
    for_each = var.connection_type != "PRIVATE_SERVICE_CONNECT_INTERFACES" ? [1] : []
    content {
      network       = var.network
      ip_allocation = var.ip_allocation
    }
  }

  dynamic "accelerators" {
    for_each = var.accelerators != null ? [1] : []
    content {
      accelerator_type = var.accelerators.accelerator_type
      state            = var.accelerators.state
    }
  }

  dynamic "crypto_key_config" {
    for_each = var.kms_key != null ? [1] : []
    content {
      key_reference = var.kms_key
    }
  }

  depends_on = [
    google_compute_network_attachment.psc,
    time_sleep.psc_attachment_propagation
  ]
}
