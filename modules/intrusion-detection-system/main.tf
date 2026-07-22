#/**
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
data "google_compute_network" "vpc_network" {
  name    = var.landing_network
  project = var.project
}

# Setup Private IP access ###
resource "google_compute_global_address" "ids_private_ip" {
  count = var.create_service_networking_connection ? 1 : 0

  name          = var.ids_private_ip_range_name
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = var.ids_private_ip_prefix_length
  network       = data.google_compute_network.vpc_network.id
  project       = var.project
  description   = "Private IP address access"
}

# Create Private Connection: ####
resource "google_service_networking_connection" "private_vpc_connection" {
  count = var.create_service_networking_connection ? 0 : 1

  network                 = data.google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.ids_private_ip[0].name]
  depends_on              = [google_compute_global_address.ids_private_ip]
}

# Creating the IDS Endpoint ####
resource "google_cloud_ids_endpoint" "ids_endpoint" {
  name              = var.ids_name
  location          = var.network_zone
  network           = data.google_compute_network.vpc_network.id
  severity          = var.severity
  project           = var.project
  threat_exceptions = var.threat_exceptions

  depends_on = [
    google_service_networking_connection.private_vpc_connection,
  ]
}

#Creating the packet mirroring policy for the subnet ####
resource "google_compute_packet_mirroring" "cloud_ids_packet_mirroring" {
  name        = var.packet_mirroring_policy_name
  description = "Packet mirroring policy description"
  project     = var.project
  region      = var.network_region
  network {
    url = data.google_compute_network.vpc_network.id
  }
  collector_ilb {
    url = google_cloud_ids_endpoint.ids_endpoint.endpoint_forwarding_rule
  }
  mirrored_resources {
    tags = var.tag_list == null ? [] : var.tag_list
    subnetworks {
      url = "https://www.googleapis.com/compute/v1/projects/${var.project}/regions/${var.network_region}/subnetworks/${var.subnet}"
    }
  }
  filter {
    ip_protocols = var.ip_protocols_filter
    cidr_ranges  = var.cidr_ranges_filter
    direction    = var.direction_filter
  }
  depends_on = [
    google_cloud_ids_endpoint.ids_endpoint,
  ]
}
