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

override_data {
  target = data.google_project.current
  values = {
    number = "123456789012"
  }
}

override_data {
  target = data.google_compute_network.network
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/test-net/global/networks/test-vpc"
  }
}

override_data {
  target = data.google_compute_subnetwork.subnetwork
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/test-net/regions/us-east4/subnetworks/test-subnet"
  }
}

override_data {
  target = data.google_kms_key_ring.default
  values = {
    id = "projects/test-core/locations/us-east4/keyRings/test-kr"
  }
}

override_data {
  target = data.google_kms_crypto_key.default
  values = {
    id = "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
  }
}

variables {
  main_project_id            = "test-workload"
  core_project_id            = "test-core"
  network_project_id         = "test-net"
  region                     = "us-east4"
  zone                       = "us-east4-a"
  network_name               = "test-vpc"
  subnetwork_name            = "test-subnet"
  kms_keyring_name           = "test-kr"
  kms_key_name               = "test-key"
  compute_service_account_id = "bastion-sa"
  instance_name              = "bastion-vm"
  disk_name                  = "bastion-disk"
  allowed_firewall_ports     = ["22"]
  allowed_source_ranges      = ["35.235.240.0/20"]
}

run "plan_hardened_bastion" {
  command = plan

  assert {
    condition     = google_service_account.compute.account_id == "bastion-sa"
    error_message = "Expected dedicated bastion compute service account."
  }

  assert {
    condition     = google_compute_firewall.default.project == "test-net"
    error_message = "Expected firewall rule in network_project_id."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.crypto_key.member == "serviceAccount:service-123456789012@compute-system.iam.gserviceaccount.com"
    error_message = "Expected Compute Engine service agent CMEK binding."
  }
}
