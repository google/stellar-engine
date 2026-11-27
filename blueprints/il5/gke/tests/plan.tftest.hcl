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
mock_provider "time" {}

override_data {
  target = data.google_project.main
  values = {
    number     = "123456789012"
    project_id = "my-gke-main-0"
  }
}

override_data {
  target = data.google_compute_network.existing_network
  values = {
    self_link = "projects/my-net-host-0/global/networks/prod-spoke-0"
  }
}

override_data {
  target = data.google_compute_subnetwork.existing_subnetwork
  values = {
    self_link     = "projects/my-net-host-0/regions/us-east4/subnetworks/prod-tenant-1-subnet"
    ip_cidr_range = "10.0.0.0/24"
  }
}

override_data {
  target = data.google_kms_key_ring.existing_kms_keyring
  values = {
    id = "projects/my-core-0/locations/us-east4/keyRings/my-kr"
  }
}

override_data {
  target = data.google_kms_crypto_key.existing_kms_key
  values = {
    id = "projects/my-core-0/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
  }
}

variables {
  bastion_vm_zone                                   = "us-east4-a"
  core_project_id                                   = "my-core-0"
  existing_kms_key_name                             = "default"
  existing_kms_keyring_name                         = "my-kr"
  existing_network_name                             = "prod-spoke-0"
  existing_subnetwork_name                          = "prod-tenant-1-subnet"
  existing_subnetwork_secondary_range_pods_name     = "pods"
  existing_subnetwork_secondary_range_services_name = "services"
  gcp_region                                        = "us-east4"
  landing_project_id                                = "my-net-host-0"
  main_project_id                                   = "my-gke-main-0"
}

run "defaults_plan" {
  command = plan

  assert {
    condition     = module.cluster.cluster.private_cluster_config[0].enable_private_endpoint == true
    error_message = "Expected GKE cluster private endpoint to be enabled by default."
  }

  assert {
    condition     = module.cluster.cluster.remove_default_node_pool == true
    error_message = "Expected default node pool removal to be enabled by default."
  }

  assert {
    condition     = module.cluster.cluster.enable_shielded_nodes == true
    error_message = "Expected shielded nodes to be enabled by default."
  }

  assert {
    condition     = output.gke_cluster_name != ""
    error_message = "Expected non-empty gke_cluster_name output."
  }

  assert {
    condition     = output.nodepool_name != ""
    error_message = "Expected non-empty nodepool_name output."
  }
}

run "keep_default_node_pool" {
  command = plan

  variables {
    remove_default_node_pool = false
  }

  assert {
    condition     = module.cluster.cluster.remove_default_node_pool == false
    error_message = "Expected remove_default_node_pool override to be reflected on the cluster."
  }
}
