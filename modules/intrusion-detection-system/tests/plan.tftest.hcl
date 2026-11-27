# Copyright 2026 Google LLC
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

mock_provider "google" {
  mock_data "google_compute_network" {
    defaults = {
      id = "projects/xxxx-prod-net-host/global/networks/prod-spoke-0"
    }
  }
}

mock_provider "google-beta" {}

variables {
  ids_name            = "xxxx-ids"
  landing_network     = "prod-spoke-0"
  landing_vpc_network = "prod-spoke-0"
  network_region      = "us-east4"
  network_zone        = "us-east4-c"
  project             = "xxxx-prod-net-host"
  subnet              = "prod-tenant-1-subnet"
}

run "combines_and_deduplicates_subnet_and_subnet_list" {
  command = plan

  variables {
    create_service_networking_connection = false
    subnet_list = [
      "prod-tenant-1-subnet",
      "prod-tenant-2-subnet",
      "https://www.googleapis.com/compute/v1/projects/xxxx-prod-net-host/regions/us-east4/subnetworks/prod-tenant-3-subnet",
    ]
  }

  assert {
    condition = toset([for s in google_compute_packet_mirroring.cloud_ids_packet_mirroring.mirrored_resources[0].subnetworks : s.url]) == toset([
      "https://www.googleapis.com/compute/v1/projects/xxxx-prod-net-host/regions/us-east4/subnetworks/prod-tenant-1-subnet",
      "https://www.googleapis.com/compute/v1/projects/xxxx-prod-net-host/regions/us-east4/subnetworks/prod-tenant-2-subnet",
      "https://www.googleapis.com/compute/v1/projects/xxxx-prod-net-host/regions/us-east4/subnetworks/prod-tenant-3-subnet",
    ])
    error_message = "Packet mirroring must include deduplicated entries from both subnet and subnet_list."
  }

  assert {
    condition     = length(google_compute_global_address.ids_private_ip) == 0 && length(google_service_networking_connection.private_vpc_connection) == 0
    error_message = "Service Networking PSA resources must be skipped when create_service_networking_connection is false."
  }
}
