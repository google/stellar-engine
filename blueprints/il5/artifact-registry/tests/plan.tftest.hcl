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

override_data {
  target = data.google_project.project
  values = {
    id         = "projects/test-ar-project"
    number     = "123456789012"
    project_id = "test-ar-project"
  }
}

override_data {
  target = data.google_kms_key_ring.default
  values = {
    id = "projects/test-core-project/locations/us-east4/keyRings/test-kr"
  }
}

override_data {
  target = data.google_kms_crypto_key.default
  values = {
    id = "projects/test-core-project/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
  }
}

override_data {
  target = data.google_compute_network.network
  values = {
    id = "projects/test-net-project/global/networks/prod-spoke-0"
  }
}

override_data {
  target = data.google_compute_subnetwork.subnetwork
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/test-net-project/regions/us-east4/subnetworks/prod-tenant-1-subnet"
  }
}

override_data {
  target = data.google_compute_image.centos
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/images/centos-stream-9-v20260101"
  }
}

variables {
  main_project_id    = "test-ar-project"
  core_project_id    = "test-core-project"
  network_project_id = "test-net-project"
  region             = "us-east4"
  kms_keyring_name   = "test-kr"
  kms_key_name       = "test-key"
  vpc_network_name   = "prod-spoke-0"
  subnetwork_name    = "prod-tenant-1-subnet"
  developer_registries = {
    "app-a" = {
      readers = ["group:readers@example.com"]
      writers = ["group:writers@example.com"]
    }
  }
}

run "plan_required_vpc_network_name" {
  command = plan

  assert {
    condition     = var.vpc_network_name == "prod-spoke-0"
    error_message = "Expected vpc_network_name to be set explicitly."
  }

  assert {
    condition     = google_artifact_registry_repository.docker_hub.kms_key_name == "projects/test-core-project/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
    error_message = "Expected Docker Hub remote repository to use CMEK."
  }

  assert {
    condition     = google_artifact_registry_repository.docker_repos_developer["app-a"].kms_key_name == "projects/test-core-project/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
    error_message = "Expected developer repository to use CMEK."
  }
}

run "reject_empty_vpc_network_name" {
  command = plan

  variables {
    vpc_network_name = ""
  }

  expect_failures = [
    var.vpc_network_name,
  ]
}
