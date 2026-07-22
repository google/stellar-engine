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
# tfdoc:file:description Networking Hub and Spokes configuration using Network Connectivity Center.

# main hub
resource "google_network_connectivity_hub" "main" {
  name            = "main-hub"
  project         = module.vdss-host-project.project_id
  description     = "Main NCC Hub for Landings and Spokes"
  preset_topology = "STAR"
  export_psc      = true
}

# Hub groups with auto-accept for cross-project spokes
resource "google_network_connectivity_group" "groups" {
  for_each = toset(["center", "edge"])
  hub      = google_network_connectivity_hub.main.id
  name     = each.key
  project  = module.vdss-host-project.project_id
  auto_accept {
    auto_accept_projects = ["*"] # Allow all projects in the organization
  }
}

# center spokes
resource "google_network_connectivity_spoke" "landing" {
  name     = "landing-vpc-spoke"
  hub      = google_network_connectivity_hub.main.id
  location = "global"
  project  = module.vdss-host-project.project_id
  group    = google_network_connectivity_group.groups["center"].id
  linked_vpc_network {
    uri = module.vdss-vpc.self_link
  }
  depends_on = [google_network_connectivity_hub.main]
}

resource "google_network_connectivity_spoke" "sharedsvcs" {
  name     = "shared-services-spoke"
  hub      = google_network_connectivity_hub.main.id
  location = "global"
  project  = module.vdss-host-project.project_id
  group    = google_network_connectivity_group.groups["center"].id
  linked_vpc_network {
    uri                   = module.shared-services-vpc.self_link
    exclude_export_ranges = ["10.84.8.0/23"]
  }
  depends_on = [google_network_connectivity_hub.main]
}

#Tenant Transit Spoke
resource "google_network_connectivity_spoke" "tenant_spoke" {
  name     = "tenant-transit-vpc-spoke"
  hub      = google_network_connectivity_hub.main.id
  location = "global"
  project  = module.vdss-host-project.project_id
  group    = google_network_connectivity_group.groups["center"].id

  linked_vpc_network {
    uri = module.tenant-transit-vpc.self_link
  }
}

# edge spokes
resource "google_network_connectivity_spoke" "csp_spoke" {
  name     = "csp-vpc-spoke"
  hub      = google_network_connectivity_hub.main.id
  location = "global"
  project  = module.vdss-host-project.project_id
  group    = google_network_connectivity_group.groups["edge"].id
  linked_vpc_network {
    uri                   = module.csp-landing-vpc.self_link
    exclude_export_ranges = ["10.84.7.0/24"]
  }
}

resource "google_network_connectivity_spoke" "bcap_spoke" {
  name     = "bcap-vpc-spoke"
  hub      = google_network_connectivity_hub.main.id
  location = "global"
  project  = module.vdss-host-project.project_id
  group    = google_network_connectivity_group.groups["edge"].id
  linked_vpc_network {
    uri                   = module.bcap-spoke-vpc.self_link
    exclude_export_ranges = ["10.84.5.0/24"]
  }
}

resource "google_network_connectivity_spoke" "interconnect_spoke" {
  name     = "interconnect-vpc-spoke"
  hub      = google_network_connectivity_hub.main.id
  location = "global"
  project  = module.vdss-host-project.project_id
  group    = google_network_connectivity_group.groups["edge"].id
  linked_vpc_network {
    uri                   = module.interconnect-spoke-vpc.self_link
    exclude_export_ranges = ["10.84.6.0/24"]
  }
}
