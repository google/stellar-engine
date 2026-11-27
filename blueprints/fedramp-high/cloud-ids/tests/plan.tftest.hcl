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
  mock_data "google_project" {
    defaults = {
      number     = "987654321098"
      project_id = "xxxx-prod-net-host"
    }
  }
  mock_data "google_compute_zones" {
    defaults = {
      names = ["us-east4-a", "us-east4-b", "us-east4-c"]
    }
  }
  mock_data "google_compute_network" {
    defaults = {
      id = "projects/xxxx-prod-net-host/global/networks/prod-spoke-0"
    }
  }
}

mock_provider "google-beta" {}

variables {
  ids_name           = "ids-name-00"
  main_project_id    = "xxxx-main-0"
  network_name       = "prod-spoke-0"
  network_project_id = "xxxx-prod-net-host"
  prefix             = "xxxx"
  region             = "us-east4"
}

run "plan_defaults_use_network_project_and_skip_psa" {
  command = plan

  assert {
    condition     = data.google_project.project.project_id == "xxxx-prod-net-host" && data.google_compute_zones.available.project == "xxxx-prod-net-host"
    error_message = "Zone lookup must query network_project_id rather than main_project_id."
  }

  assert {
    condition     = contains(keys(google_project_service.net_host_services), "servicenetworking.googleapis.com")
    error_message = "servicenetworking.googleapis.com must be enabled on network_project_id."
  }

  assert {
    condition     = module.cloud-ids.ids_private_ip_range_name == "xxxx-ids-private-address" && var.subnetwork_name == "prod-tenant-1-subnet" && var.create_service_networking_connection == false
    error_message = "Stage 2 defaults must use prod-tenant-1-subnet and keep Service Networking connection opt-in."
  }
}

run "plan_opt_in_psa_connection" {
  command = plan

  variables {
    create_service_networking_connection = true
    subnetwork_list                      = ["prod-tenant-1-subnet", "prod-tenant-2-subnet"]
  }

  assert {
    condition     = var.create_service_networking_connection == true && toset(var.subnetwork_list) == toset(["prod-tenant-1-subnet", "prod-tenant-2-subnet"])
    error_message = "Opt-in PSA connection and subnetwork_list must pass through."
  }
}
