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

  assert {
    condition     = length(google_project_iam_member.bastion_observability) == 2
    error_message = "Expected logging and monitoring writer IAM bindings by default."
  }

  assert {
    condition     = google_project_iam_member.bastion_observability["roles/logging.logWriter"].role == "roles/logging.logWriter"
    error_message = "Expected roles/logging.logWriter grant on the bastion service account."
  }

  assert {
    condition     = google_project_iam_member.bastion_observability["roles/monitoring.metricWriter"].role == "roles/monitoring.metricWriter"
    error_message = "Expected roles/monitoring.metricWriter grant on the bastion service account."
  }

  assert {
    condition     = length(module.additional-bastion-vm) == 0
    error_message = "Expected no additional bastions by default."
  }
}

run "apply_hardened_bastion_vm_attributes" {
  command = apply

  assert {
    condition     = module.bastion-vm.instance.metadata["serial-port-enable"] == "false"
    error_message = "Expected serial port access to be disabled per CIS 4.5."
  }

  assert {
    condition     = module.bastion-vm.instance.metadata["enable-oslogin"] == "TRUE"
    error_message = "Expected OS Login metadata to remain enabled."
  }

  assert {
    condition     = module.bastion-vm.instance.metadata["block-project-ssh-keys"] == "true"
    error_message = "Expected project SSH keys to remain blocked."
  }

  assert {
    condition     = module.bastion-vm.instance.confidential_instance_config[0].enable_confidential_compute == true
    error_message = "Expected Confidential Compute SEV to remain enabled."
  }

  assert {
    condition     = module.bastion-vm.instance.shielded_instance_config[0].enable_secure_boot == true
    error_message = "Expected Shielded VM secure boot to remain enabled."
  }

  assert {
    condition     = module.bastion-vm.instance.shielded_instance_config[0].enable_vtpm == true
    error_message = "Expected Shielded VM vTPM to remain enabled."
  }

  assert {
    condition     = module.bastion-vm.instance.shielded_instance_config[0].enable_integrity_monitoring == true
    error_message = "Expected Shielded VM integrity monitoring to remain enabled."
  }

  assert {
    condition     = module.bastion-vm.instance.boot_disk[0].kms_key_self_link == "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
    error_message = "Expected CMEK boot disk encryption on primary bastion."
  }
}

run "apply_bcap_static_ip_and_additional_bastions" {
  command = apply

  variables {
    access_mode           = "bcap"
    allowed_source_ranges = ["10.200.0.0/24"]
    static_internal_ip    = "10.10.0.10"
    additional_bastions = {
      ops = {
        instance_name              = "ops-bastion-vm"
        compute_service_account_id = "ops-bastion-sa"
        static_internal_ip         = "10.10.0.20"
        allowed_firewall_ports     = ["22", "443"]
        allowed_source_ranges      = ["10.200.1.0/24"]
      }
    }
  }

  assert {
    condition     = module.bastion-vm.instance.network_interface[0].network_ip == "10.10.0.10"
    error_message = "Expected primary bastion VM to use configured static_internal_ip."
  }

  assert {
    condition     = output.internal_ip == "10.10.0.10"
    error_message = "Expected primary internal_ip output to match static_internal_ip."
  }

  assert {
    condition     = google_compute_firewall.default.source_ranges == toset(["10.200.0.0/24"])
    error_message = "Expected primary firewall rule to use explicit BCAP source ranges."
  }

  assert {
    condition     = google_service_account.additional["ops"].account_id == "ops-bastion-sa"
    error_message = "Expected dedicated service account for additional bastion."
  }

  assert {
    condition     = google_compute_firewall.additional["ops"].name == "allow-bastion-ops"
    error_message = "Expected deterministic SA-targeted firewall rule name for additional bastion."
  }

  assert {
    condition     = google_compute_firewall.additional["ops"].source_ranges == toset(["10.200.1.0/24"])
    error_message = "Expected additional bastion firewall to use its dedicated BCAP source ranges."
  }

  assert {
    condition     = google_compute_firewall.additional["ops"].log_config[0].metadata == "INCLUDE_ALL_METADATA"
    error_message = "Expected full firewall logging metadata on additional bastion firewall."
  }

  assert {
    condition     = module.additional-bastion-vm["ops"].instance.network_interface[0].network_ip == "10.10.0.20"
    error_message = "Expected additional bastion VM to use its configured static_internal_ip."
  }

  assert {
    condition     = output.additional_bastions["ops"].internal_ip == "10.10.0.20"
    error_message = "Expected additional_bastions output internal_ip to match static_internal_ip."
  }

  assert {
    condition     = module.additional-bastion-vm["ops"].instance.metadata["serial-port-enable"] == "false"
    error_message = "Expected serial port access to be disabled on additional bastion."
  }

  assert {
    condition     = module.additional-bastion-vm["ops"].instance.metadata["enable-oslogin"] == "TRUE"
    error_message = "Expected OS Login to remain enabled on additional bastion."
  }

  assert {
    condition     = module.additional-bastion-vm["ops"].instance.metadata["block-project-ssh-keys"] == "true"
    error_message = "Expected project SSH keys to remain blocked on additional bastion."
  }

  assert {
    condition     = module.additional-bastion-vm["ops"].instance.confidential_instance_config[0].enable_confidential_compute == true
    error_message = "Expected Confidential Compute SEV on additional bastion."
  }

  assert {
    condition     = module.additional-bastion-vm["ops"].instance.shielded_instance_config[0].enable_secure_boot == true
    error_message = "Expected Shielded VM secure boot on additional bastion."
  }

  assert {
    condition     = module.additional-bastion-vm["ops"].instance.boot_disk[0].kms_key_self_link == "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
    error_message = "Expected CMEK boot disk encryption on additional bastion."
  }

  assert {
    condition     = length(google_project_iam_member.additional_observability) == 2
    error_message = "Expected observability IAM bindings for the additional bastion service account."
  }
}

run "plan_disable_observability_iam" {
  command = plan

  variables {
    enable_observability_iam = false
  }

  assert {
    condition     = length(google_project_iam_member.bastion_observability) == 0
    error_message = "Expected observability IAM bindings to be omitted when disabled."
  }
}

run "reject_open_source_range" {
  command = plan

  variables {
    allowed_source_ranges = ["0.0.0.0/0"]
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_invalid_access_mode" {
  command = plan

  variables {
    access_mode = "public"
  }

  expect_failures = [
    var.access_mode,
  ]
}

run "reject_bcap_with_iap_source_range" {
  command = plan

  variables {
    access_mode           = "bcap"
    allowed_source_ranges = ["35.235.240.0/20"]
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_empty_source_ranges" {
  command = plan

  variables {
    access_mode           = "bcap"
    allowed_source_ranges = []
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_additional_bastion_open_source_range" {
  command = plan

  variables {
    additional_bastions = {
      bad = {
        compute_service_account_id = "bad-bastion-sa"
        allowed_source_ranges      = ["0.0.0.0/0"]
      }
    }
  }

  expect_failures = [
    var.additional_bastions,
  ]
}

run "reject_bcap_with_iap_superset_range" {
  command = plan

  variables {
    access_mode           = "bcap"
    allowed_source_ranges = ["35.235.0.0/16"]
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_bcap_with_iap_subset_range" {
  command = plan

  variables {
    access_mode           = "bcap"
    allowed_source_ranges = ["35.235.240.0/21"]
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_half_internet_source_range" {
  command = plan

  variables {
    allowed_source_ranges = ["0.0.0.0/1"]
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_additional_bastion_bcap_iap_overlap" {
  command = plan

  variables {
    additional_bastions = {
      badbcap = {
        access_mode                = "bcap"
        compute_service_account_id = "badbcap-bastion-sa"
        allowed_source_ranges      = ["35.235.240.1/32"]
      }
    }
  }

  expect_failures = [
    var.additional_bastions,
  ]
}

run "reject_zone_outside_region" {
  command = plan

  variables {
    zone = "us-central1-a"
  }

  expect_failures = [
    var.zone,
  ]
}

run "reject_additional_bastion_zone_outside_region" {
  command = plan

  variables {
    additional_bastions = {
      badzone = {
        compute_service_account_id = "badzone-bastion-sa"
        zone                       = "us-west1-a"
      }
    }
  }

  expect_failures = [
    var.additional_bastions,
  ]
}

run "reject_colliding_firewall_name" {
  command = plan

  variables {
    additional_bastions = {
      dup = {
        compute_service_account_id = "dup-bastion-sa"
        firewall_name              = "allow-web"
      }
    }
  }

  expect_failures = [
    var.additional_bastions,
  ]
}

run "reject_duplicate_static_ip_same_subnet" {
  command = plan

  variables {
    static_internal_ip = "10.10.0.10"
    additional_bastions = {
      dup = {
        compute_service_account_id = "dup-ip-bastion-sa"
        static_internal_ip         = "10.10.0.10"
      }
    }
  }

  expect_failures = [
    var.additional_bastions,
  ]
}
