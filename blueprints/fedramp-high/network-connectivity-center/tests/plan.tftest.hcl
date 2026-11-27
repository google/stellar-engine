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

mock_provider "google" {}

variables {
  gcp_region      = "us-east4"
  main_project_id = "xxxx-hub-project"
  ncc_hub_name    = "xxxx-ncc-hub"
  spokes = {
    prod-spoke-0 = "projects/xxxx-prod-net-host/global/networks/prod-spoke-0"
    prod-spoke-1 = "projects/xxxx-prod-net-host-2/global/networks/prod-spoke-1"
  }
}

run "mesh_topology_sets_auto_accept_projects" {
  command = plan

  variables {
    topology = "MESH"
  }

  assert {
    condition     = length(google_network_connectivity_group.default) == 1 && length(google_network_connectivity_group.center) == 0 && length(google_network_connectivity_group.edge) == 0
    error_message = "MESH topology must create only the default group."
  }

  assert {
    condition     = toset(google_network_connectivity_group.default[0].auto_accept[0].auto_accept_projects) == toset(["xxxx-prod-net-host", "xxxx-prod-net-host-2", "xxxx-hub-project"])
    error_message = "default group auto_accept_projects must include all spoke projects and main_project_id."
  }
}

run "star_topology_sets_center_and_edge_auto_accept_projects" {
  command = plan

  variables {
    topology = "STAR"
  }

  assert {
    condition     = length(google_network_connectivity_group.default) == 0 && length(google_network_connectivity_group.center) == 1 && length(google_network_connectivity_group.edge) == 1
    error_message = "STAR topology must create center and edge groups without default."
  }

  assert {
    condition     = toset(google_network_connectivity_group.center[0].auto_accept[0].auto_accept_projects) == toset(["xxxx-prod-net-host", "xxxx-prod-net-host-2", "xxxx-hub-project"]) && toset(google_network_connectivity_group.edge[0].auto_accept[0].auto_accept_projects) == toset(["xxxx-prod-net-host", "xxxx-prod-net-host-2", "xxxx-hub-project"])
    error_message = "STAR center and edge groups must auto-accept spokes from spoke projects and main_project_id."
  }
}
