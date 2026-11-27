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
  target = data.google_project.current
  values = {
    number = "123456789012"
  }
}

override_data {
  target = data.google_compute_network.network
  values = {
    id        = "projects/test-net/global/networks/test-vpc"
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
  network_name               = "test-vpc"
  subnetwork_name            = "test-subnet"
  kms_keyring_name           = "test-kr"
  kms_key_name               = "test-key"
  compute_service_account_id = "shielded-vm-sa"
  allowed_firewall_ports     = ["22", "443"]
  source_ranges_allowed      = ["10.0.1.0/24"]
}

run "plan_default_sev_machine_type_and_cmek" {
  command = plan

  assert {
    condition     = var.instance_type == "n2d-standard-2"
    error_message = "Expected default instance_type to support Confidential Compute SEV."
  }

  assert {
    condition     = google_service_account.compute.account_id == "shielded-vm-sa"
    error_message = "Expected dedicated compute service account ID."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.compute.crypto_key_id == "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
    error_message = "Expected CMEK IAM binding on the target KMS CryptoKey."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.compute.member == "serviceAccount:service-123456789012@compute-system.iam.gserviceaccount.com"
    error_message = "Expected Compute Engine service agent CMEK binding."
  }

  assert {
    condition     = google_compute_firewall.default.network == "projects/test-net/global/networks/test-vpc"
    error_message = "Expected firewall rule to attach to the Shared VPC network."
  }

  assert {
    condition     = google_compute_firewall.default.source_ranges == toset(["10.0.1.0/24"])
    error_message = "Expected firewall rule to restrict ingress to source_ranges_allowed."
  }

  assert {
    condition     = google_compute_firewall.default.log_config[0].metadata == "INCLUDE_ALL_METADATA"
    error_message = "Expected full firewall flow metadata logging."
  }
}

run "plan_custom_sev_machine_type" {
  command = plan

  variables {
    instance_type = "c2d-standard-2"
  }

  assert {
    condition     = var.instance_type == "c2d-standard-2"
    error_message = "Expected custom SEV machine_type override to plan cleanly."
  }
}

run "apply_shielded_and_confidential_vm" {
  command = apply

  assert {
    condition     = module.shielded-vm.instance.machine_type == "n2d-standard-2"
    error_message = "Expected VM machine_type to default to n2d-standard-2."
  }

  assert {
    condition     = module.shielded-vm.instance.confidential_instance_config[0].enable_confidential_compute == true
    error_message = "Expected Confidential Compute SEV to be enabled."
  }

  assert {
    condition     = module.shielded-vm.instance.shielded_instance_config[0].enable_secure_boot == true
    error_message = "Expected Secure Boot to be enabled."
  }

  assert {
    condition     = module.shielded-vm.instance.shielded_instance_config[0].enable_vtpm == true
    error_message = "Expected vTPM to be enabled."
  }

  assert {
    condition     = module.shielded-vm.instance.shielded_instance_config[0].enable_integrity_monitoring == true
    error_message = "Expected Integrity Monitoring to be enabled."
  }

  assert {
    condition     = module.shielded-vm.instance.boot_disk[0].kms_key_self_link == "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
    error_message = "Expected CMEK boot disk encryption."
  }
}
