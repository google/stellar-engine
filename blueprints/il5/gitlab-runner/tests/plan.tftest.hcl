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
  target = data.google_project.current
  values = {
    number = "123456789012"
  }
}

override_data {
  target = data.google_compute_network.network
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/my-net-host-0/global/networks/my-vpc-0"
  }
}

override_data {
  target = data.google_compute_subnetwork.subnetwork
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/my-net-host-0/regions/us-east4/subnetworks/my-subnet-0"
  }
}

variables {
  project_id         = "my-runner-project-0"
  network_project_id = "my-net-host-0"
  region             = "us-east4"
  zone               = "us-east4-a"
  network_name       = "my-vpc-0"
  subnetwork_name    = "my-subnet-0"
  kms_key_id = join("", [
    "projects/my-kms-project-0/locations/us-east4/",
    "keyRings/my-keyring/cryptoKeys/runner-key",
  ])
  golden_image = join("", [
    "projects/my-images-project-0/global/images/",
    "family/gitlab-runner-golden",
  ])
  gitlab_url             = "https://gitlab.example.com"
  runner_token_secret_id = "gitlab-runner-auth-token"
}

run "plan_hardened_default_runner" {
  command = apply

  assert {
    condition = (
      length(google_project_service.apis) == 4 &&
      time_sleep.service_agent_propagation.create_duration == "60s"
    )
    error_message = "Expected 4 project APIs and 60s propagation wait."
  }

  assert {
    condition = (
      module.runner-sa.email
      == "gitlab-runner-sa@my-runner-project-0.iam.gserviceaccount.com"
    )
    error_message = "Expected dedicated runner service account email."
  }

  assert {
    condition = (
      module.runner-vm.instance.service_account[0].email
      == module.runner-sa.email
    )
    error_message = "Expected runner VM to attach dedicated SA."
  }

  assert {
    condition = (
      module.runner-vm.instance.confidential_instance_config[
        0
      ].enable_confidential_compute == true
    )
    error_message = "Expected AMD SEV Confidential Compute enabled."
  }

  assert {
    condition = (
      module.runner-vm.instance.shielded_instance_config[
        0
      ].enable_secure_boot == true &&
      module.runner-vm.instance.shielded_instance_config[
        0
      ].enable_vtpm == true &&
      module.runner-vm.instance.shielded_instance_config[
        0
      ].enable_integrity_monitoring == true
    )
    error_message = "Expected Shielded VM controls enabled."
  }

  assert {
    condition = (
      module.runner-vm.instance.boot_disk[0].kms_key_self_link
      == var.kms_key_id
    )
    error_message = "Expected CMEK encryption on runner boot disk."
  }

  assert {
    condition = (
      module.runner-vm.instance.boot_disk[0].initialize_params[0].image
      == var.golden_image
    )
    error_message = "Expected pre-baked golden image on boot disk."
  }

  assert {
    condition = (
      module.runner-vm.instance.metadata["enable-oslogin"] == "TRUE" &&
      module.runner-vm.instance.metadata[
        "block-project-ssh-keys"
      ] == "TRUE" &&
      module.runner-vm.instance.metadata[
        "serial-port-enable"
      ] == "false" &&
      strcontains(
        module.runner-vm.instance.metadata["shutdown-script"],
        "gitlab-runner unregister --config /etc/gitlab-runner/config.toml",
      )
    )
    error_message = "Expected OS Login, key block, serial off, and shutdown."
  }

  assert {
    condition = (
      length(
        module.runner-vm.instance.network_interface[0].access_config
      ) == 0
    )
    error_message = "Expected private runner VM without public IP."
  }

  assert {
    condition = (
      length(google_kms_crypto_key_iam_member.compute_cmek) == 1 &&
      google_kms_crypto_key_iam_member.compute_cmek[0].member == join("", [
        "serviceAccount:service-123456789012@",
        "compute-system.iam.gserviceaccount.com",
      ])
    )
    error_message = "Expected Compute Engine service agent CMEK binding."
  }

  assert {
    condition = (
      length(google_secret_manager_regional_secret_iam_member.runner_token)
      == 1 &&
      google_secret_manager_regional_secret_iam_member.runner_token[
        0
      ].location == "us-east4" &&
      google_secret_manager_regional_secret_iam_member.runner_token[
        0
      ].secret_id == "gitlab-runner-auth-token" &&
      google_secret_manager_regional_secret_iam_member.runner_token[
        0
      ].role == "roles/secretmanager.secretAccessor"
    )
    error_message = "Expected secret-scoped regional secretAccessor grant."
  }

  assert {
    condition     = length(module.iap-ssh-firewall) == 0
    error_message = "Expected IAP SSH firewall disabled by default."
  }

  assert {
    condition     = length(module.cloud-nat) == 0
    error_message = "Expected Cloud NAT disabled by default."
  }

  assert {
    condition = (
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "CLOUDSDK_CORE_DISABLE_PROMPTS=1",
      ) &&
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "https://secretmanager.$${REGION}.rep.googleapis.com/",
      ) &&
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER=",
      ) &&
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "systemctl enable --now docker",
      ) &&
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "CI_SERVER_TOKEN",
      ) &&
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "--location=",
      ) &&
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "--non-interactive",
      ) &&
      strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "unset CI_SERVER_TOKEN",
      ) &&
      !strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "curl",
      ) &&
      !strcontains(
        module.runner-vm.instance.metadata["startup-script"],
        "--token",
      )
    )
    error_message = "Startup script failed regional SM or token assertions."
  }
}

run "plan_optional_iap_ssh_cloud_nat_snapshots_and_central_kms" {
  command = apply

  variables {
    enable_iap_ssh             = true
    enable_cloud_nat           = true
    enable_boot_disk_snapshots = true
    manage_kms_iam             = false
    machine_type               = "n2d-custom-4-16384"
  }

  assert {
    condition = (
      length(module.iap-ssh-firewall) == 1 &&
      length(module.iap-ssh-firewall[0].default_rules.admin) == 0 &&
      length(module.iap-ssh-firewall[0].default_rules.http) == 0 &&
      length(module.iap-ssh-firewall[0].default_rules.https) == 0 &&
      length(module.iap-ssh-firewall[0].default_rules.ssh) == 0 &&
      module.iap-ssh-firewall[0].rules[
        "gitlab-runner-0-allow-iap-ssh"
      ].project == "my-net-host-0" &&
      module.iap-ssh-firewall[0].rules[
        "gitlab-runner-0-allow-iap-ssh"
      ].source_ranges == toset(["35.235.240.0/20"]) &&
      module.iap-ssh-firewall[0].rules[
        "gitlab-runner-0-allow-iap-ssh"
      ].target_service_accounts == toset([module.runner-sa.email]) &&
      module.iap-ssh-firewall[0].rules[
        "gitlab-runner-0-allow-iap-ssh"
      ].log_config[0].metadata == "INCLUDE_ALL_METADATA"
    )
    error_message = "Expected SA-targeted logged IAP SSH rule."
  }

  assert {
    condition = (
      length(module.cloud-nat) == 1 &&
      module.cloud-nat[0].router.project == "my-net-host-0" &&
      module.cloud-nat[0].router_name == "gitlab-runner-0-router" &&
      module.cloud-nat[0].region == "us-east4"
    )
    error_message = "Expected Cloud NAT with explicit router_name."
  }

  assert {
    condition = (
      length(google_kms_crypto_key_iam_member.compute_cmek) == 0 &&
      length(google_kms_crypto_key_iam_member.secretmanager_cmek) == 0
    )
    error_message = "Expected KMS IAM skipped when manage_kms_iam is false."
  }
}

run "plan_managed_regional_cmek_secret_and_shell_executor" {
  command = apply

  variables {
    create_runner_token_secret = true
    runner_token_secret_wo = {
      value      = "test-placeholder-not-a-secret"
      wo_version = 1
    }
    executor = "shell"
  }

  assert {
    condition     = length(module.runner-token-secret) == 1
    error_message = "Expected modules/secret-manager to provision secret."
  }

  assert {
    condition = (
      length(google_secret_manager_regional_secret_iam_member.runner_token)
      == 0
    )
    error_message = "Expected standalone secret IAM skipped."
  }

  assert {
    condition = (
      module.runner-token-secret[0].secrets[
        "gitlab-runner-auth-token"
      ].location == "us-east4" &&
      module.runner-token-secret[0].secrets[
        "gitlab-runner-auth-token"
      ].customer_managed_encryption[0].kms_key_name == var.kms_key_id
    )
    error_message = "Expected regional CMEK secret via secret-manager."
  }

  assert {
    condition = (
      module.runner-token-secret[0].versions[
        "gitlab-runner-auth-token/runner"
      ].secret_data == null &&
      module.runner-token-secret[0].versions[
        "gitlab-runner-auth-token/runner"
      ].secret_data_wo_version == "1"
    )
    error_message = "Expected write-only secret version with null secret_data."
  }

  assert {
    condition = strcontains(
      module.runner-vm.instance.metadata["startup-script"],
      "EXECUTOR='shell'",
    )
    error_message = "Expected shell executor in startup script."
  }

  assert {
    condition = (
      length(google_kms_crypto_key_iam_member.secretmanager_cmek) == 1
    )
    error_message = "Expected Secret Manager SA CMEK binding."
  }
}

run "reject_instance_name_over_49_chars" {
  command = plan

  variables {
    instance_name = "gitlab-runner-012345678901234567890123456789012345"
  }

  expect_failures = [
    var.instance_name,
  ]
}

run "reject_non_tls_gitlab_url" {
  command = plan

  variables {
    gitlab_url = "http://gitlab.example.com"
  }

  expect_failures = [
    var.gitlab_url,
  ]
}

run "reject_invalid_executor" {
  command = plan

  variables {
    executor = "kubernetes"
  }

  expect_failures = [
    var.executor,
  ]
}

run "reject_invalid_kms_key_id" {
  command = plan

  variables {
    kms_key_id = "invalid-kms-key"
  }

  expect_failures = [
    var.kms_key_id,
  ]
}

run "reject_cross_region_kms_key_id" {
  command = plan

  variables {
    kms_key_id = join("", [
      "projects/my-kms-project-0/locations/us-central1/",
      "keyRings/my-keyring/cryptoKeys/runner-key",
    ])
  }

  expect_failures = [
    var.kms_key_id,
  ]
}

run "reject_global_kms_key_id" {
  command = plan

  variables {
    kms_key_id = join("", [
      "projects/my-kms-project-0/locations/global/",
      "keyRings/my-keyring/cryptoKeys/runner-key",
    ])
  }

  expect_failures = [
    var.kms_key_id,
  ]
}

run "reject_non_sev_machine_type" {
  command = plan

  variables {
    machine_type = "e2-standard-4"
  }

  expect_failures = [
    var.machine_type,
  ]
}

run "reject_c3d_custom_machine_type" {
  command = plan

  variables {
    machine_type = "c3d-custom-4-16384"
  }

  expect_failures = [
    var.machine_type,
  ]
}

run "reject_unsupported_boot_disk_type" {
  command = plan

  variables {
    boot_disk_type = "hyperdisk-balanced"
  }

  expect_failures = [
    var.boot_disk_type,
  ]
}

run "reject_legacy_gcr_docker_image" {
  command = plan

  variables {
    docker_image = "gcr.io/google.com/cloudsdktool/google-cloud-cli:slim"
  }

  expect_failures = [
    var.docker_image,
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
