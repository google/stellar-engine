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

mock_provider "google-beta" {}

variables {
  project_id = "my-project"
  name       = "cluster-1"
  location   = "us-east4"
  vpc_config = {
    network    = "projects/my-project/global/networks/vpc-0"
    subnetwork = "projects/my-project/regions/us-east4/subnetworks/subnet-0"
    secondary_range_names = {
      pods     = "pods"
      services = "services"
    }
  }
}

run "private_endpoint_defaults_enabled_with_ip_access" {
  command = plan

  variables {
    access_config = {
      ip_access = {
        authorized_ranges = {
          internal-vms = "10.0.0.0/8"
        }
      }
    }
  }

  assert {
    condition     = google_container_cluster.cluster.private_cluster_config[0].enable_private_nodes == true
    error_message = "Private nodes must default to true."
  }

  assert {
    condition     = google_container_cluster.cluster.private_cluster_config[0].enable_private_endpoint == true
    error_message = "disable_public_endpoint must default to true when ip_access is configured."
  }

  assert {
    condition     = google_container_cluster.cluster.enable_shielded_nodes == true
    error_message = "Shielded nodes must default to true."
  }

  assert {
    condition     = google_container_cluster.cluster.fleet[0].project == "my-project"
    error_message = "Fleet registration must default to the cluster project."
  }
}

run "public_endpoint_allowed_when_explicitly_enabled" {
  command = plan

  variables {
    access_config = {
      ip_access = {
        disable_public_endpoint = false
        authorized_ranges = {
          internal-vms = "10.0.0.0/8"
        }
      }
    }
  }

  assert {
    condition     = google_container_cluster.cluster.private_cluster_config[0].enable_private_endpoint == false
    error_message = "Explicit disable_public_endpoint = false must allow the public control plane endpoint."
  }
}

run "fleet_project_override" {
  command = plan

  variables {
    fleet_project = "my-fleet-project"
  }

  assert {
    condition     = google_container_cluster.cluster.fleet[0].project == "my-fleet-project"
    error_message = "Custom fleet_project must override the default fleet project."
  }
}
