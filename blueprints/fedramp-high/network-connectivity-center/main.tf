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

locals {
  spoke_projects = distinct(
    concat(
      [for spoke_name, spoke_self_link in var.spokes : regex("projects/([^/]+)/", spoke_self_link)[0]],
      [var.main_project_id]
    )
  )
}

# Enable the API service
resource "google_project_service" "ncc" {
  project = var.main_project_id
  for_each = toset([
    "networkconnectivity.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_network_connectivity_hub" "hub" {
  name            = var.name
  project         = var.main_project_id
  preset_topology = var.topology
  export_psc      = var.psc_prop
  depends_on      = [google_project_service.ncc]
}

resource "google_network_connectivity_group" "default" {
  count = var.topology == "MESH" ? 1 : 0
  hub   = google_network_connectivity_hub.hub.id
  name  = "default"
  auto_accept {
    auto_accept_projects = local.spoke_projects
  }
}

resource "google_network_connectivity_group" "center" {
  count = var.topology == "STAR" ? 1 : 0
  hub   = google_network_connectivity_hub.hub.id
  name  = "center"
  auto_accept {
    auto_accept_projects = [var.main_project_id]
  }
}

resource "google_network_connectivity_group" "edge" {
  count = var.topology == "STAR" ? 1 : 0
  hub   = google_network_connectivity_hub.hub.id
  name  = "edge"
  auto_accept {
    auto_accept_projects = local.spoke_projects
  }
}

resource "google_network_connectivity_spoke" "spokes" {
  for_each = var.spokes
  name     = each.key
  location = "global"
  hub      = google_network_connectivity_hub.hub.id

  # Grab the project id from the vpc self-link
  project = regex("projects/([^/]+)/", each.value)[0]

  # Determine which group each spoke should be added to
  group = (var.topology == "MESH" ? google_network_connectivity_group.default[0].id :
    (regex("projects/([^/]+)/", each.value)[0] == var.main_project_id ? google_network_connectivity_group.center[0].id :
  google_network_connectivity_group.edge[0].id))

  linked_vpc_network {
    uri = each.value
  }
}