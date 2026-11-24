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

variables {
  project_id   = "my-image-factory-0"
  region       = "us-east4"
  builder_zone = "us-east4-a"
  prefix       = "acme-il5"
  base_image   = "projects/rhel-cloud/global/images/rhel-9-20250514"
  kms_key_id = join("", [
    "projects/my-kms-0/locations/us-east4/",
    "keyRings/kr/cryptoKeys/img",
  ])
  peered_network          = "projects/123456789012/global/networks/vpc-hub"
  peered_network_ip_range = "10.250.0.0/24"
  builder_subnetwork = join("", [
    "projects/my-net-host-0/regions/us-east4/",
    "subnetworks/img",
  ])
  builder_image_digest = join("", [
    "us-east4-docker.pkg.dev/my-image-factory-0/",
    "image-factory-builders/cloud-sdk@sha256:",
    "0123456789abcdef0123456789abcdef",
    "0123456789abcdef0123456789abcdef",
  ])
}

run "plan_private_image_factory" {
  command = plan

  assert {
    condition = (
      length(google_project_service.apis) == 6
      && contains(
        keys(google_project_service.apis),
        "containerscanning.googleapis.com",
      )
    )
    error_message = "Expected all 6 required project APIs to be enabled."
  }

  assert {
    condition = (
      google_project_service_identity.artifact_registry_sa.service
      == "artifactregistry.googleapis.com"
      && google_project_service_identity.cloudbuild_sa.service
      == "cloudbuild.googleapis.com"
      && length(data.google_storage_project_service_account.gcs_sa) == 1
      && time_sleep.service_agent_propagation.create_duration == "60s"
    )
    error_message = "Expected service identities, GCS SA read, and 60s wait."
  }

  assert {
    condition = (
      google_service_account_iam_member.cloudbuild_token_creator.role
      == "roles/iam.serviceAccountTokenCreator"
    )
    error_message = "Expected standalone Cloud Build token creator binding."
  }

  assert {
    condition = (
      google_cloudbuild_worker_pool.default.worker_config[0].no_external_ip
      == true
    )
    error_message = "Expected private worker pool with no_external_ip."
  }

  assert {
    condition = (
      google_cloudbuild_worker_pool.default.network_config[0].peered_network
      == var.peered_network
    )
    error_message = "Expected worker pool peered to var.peered_network."
  }

  assert {
    condition = (
      module.builder-sa.email
      == "acme-il5-image-builder@my-image-factory-0.iam.gserviceaccount.com"
    )
    error_message = "Expected dedicated builder service account email."
  }

  assert {
    condition = !strcontains(
      module.builder-sa.email,
      "-compute@developer.gserviceaccount.com",
    )
    error_message = "Builder SA must never use the default Compute SA."
  }

  assert {
    condition = (
      contains(local.builder_project_roles, "roles/compute.storageAdmin")
      && !contains(local.builder_project_roles, "roles/compute.imageUser")
    )
    error_message = "Builder SA must hold roles/compute.storageAdmin."
  }

  assert {
    condition = (
      local.staging_bucket_builder_role == "roles/storage.objectViewer"
    )
    error_message = "Builder SA must hold roles/storage.objectViewer."
  }

  assert {
    condition = (
      module.staging-bucket.bucket.encryption[0].default_kms_key_name
      == var.kms_key_id
    )
    error_message = "Expected CMEK encryption on the staging bucket."
  }

  assert {
    condition = (
      module.staging-bucket.bucket.uniform_bucket_level_access == true
    )
    error_message = "Expected UBLA on the staging bucket."
  }

  assert {
    condition = (
      module.staging-bucket.bucket.public_access_prevention == "enforced"
    )
    error_message = "Expected enforced PAP on the staging bucket."
  }

  assert {
    condition = (
      module.builder-registry.repository.kms_key_name == var.kms_key_id
    )
    error_message = "Expected CMEK encryption on Artifact Registry."
  }

  assert {
    condition     = module.builder-registry.repository.format == "DOCKER"
    error_message = "Expected DOCKER format on Artifact Registry."
  }

  assert {
    condition = (
      length(google_compute_subnetwork_iam_member.builder_network_user) == 1
    )
    error_message = "Expected Shared VPC subnetwork networkUser binding."
  }

  assert {
    condition     = length(module.builder-ssh-firewall) == 0
    error_message = "Expected SSH firewall disabled by default."
  }

  assert {
    condition     = length(google_cloudbuild_trigger.default) == 0
    error_message = "Expected no trigger when trigger_config is null."
  }

  assert {
    condition = strcontains(
      local.cloudbuild_config,
      "--confidential-compute-type=SEV",
    )
    error_message = "Rendered config must enable SEV Confidential Compute."
  }

  assert {
    condition     = strcontains(local.cloudbuild_config, "SEV_CAPABLE")
    error_message = "Rendered config must include SEV_CAPABLE."
  }

  assert {
    condition = (
      strcontains(local.cloudbuild_config, "UEFI_COMPATIBLE")
      && strcontains(local.cloudbuild_config, "GVNIC")
    )
    error_message = "Rendered config must include UEFI_COMPATIBLE and GVNIC."
  }

  assert {
    condition = strcontains(
      local.cloudbuild_config,
      "run_dir=\"/opt/google-startup-scripts\"",
    )
    error_message = "Rendered config must configure Guest Agent run_dir."
  }

  assert {
    condition = (
      strcontains(local.cloudbuild_config, "0750")
      && strcontains(
        local.cloudbuild_config,
        "/etc/default/instance_configs.cfg.template",
      )
      && !strcontains(
        local.cloudbuild_config,
        "/etc/google/instance_configs.cfg",
      )
    )
    error_message = "Rendered config must create mode 0750 run_dir."
  }

  assert {
    condition = (
      strcontains(local.cloudbuild_config, "--no-service-account")
      && strcontains(local.cloudbuild_config, "--internal-ip")
      && strcontains(local.cloudbuild_config, "--ssh-key-expire-after=1h")
    )
    error_message = "Rendered config must use private SSH without VM SA."
  }

  assert {
    condition     = strcontains(local.cloudbuild_config, "trap cleanup EXIT")
    error_message = "Rendered config must delete builder VM on exit."
  }

  assert {
    condition = (
      strcontains(
        local.cloudbuild_config,
        "--command='sudo bash /tmp/harden-rhel9.sh;",
      )
      && strcontains(
        local.cloudbuild_config,
        "status=$$?; rm -f /tmp/harden-rhel9.sh; exit $$status'",
      )
    )
    error_message = "Rendered config must single-quote remote SSH status."
  }

  assert {
    condition     = !strcontains(lower(local.cloudbuild_config), "gcr.io")
    error_message = "Rendered config must not reference gcr.io."
  }

  assert {
    condition = (
      !strcontains(local.cloudbuild_config, "tunnel-through-iap")
      && !strcontains(local.cloudbuild_config, "199.36.153.8/30")
    )
    error_message = "Rendered config must not use IAP SSH or VPC-SC bypass."
  }

  assert {
    condition = (
      strcontains(local.cloudbuild_config, "$$${attempt}")
      && !strcontains(local.cloudbuild_config, "$$$${attempt}")
    )
    error_message = "Rendered config must escape shell variables properly."
  }
}

run "plan_peered_network_project_id_and_ssh_firewall" {
  command = plan

  override_data {
    target = data.google_project.peered_network_host[0]
    values = {
      number = "987654321098"
    }
  }

  variables {
    peered_network = join("", [
      "projects/my-net-host-0/global/networks/vpc-hub",
    ])
    enable_ssh_firewall_rule          = true
    builder_confidential_compute_type = null
    builder_machine_type              = "e2-standard-2"
  }

  assert {
    condition = (
      google_cloudbuild_worker_pool.default.network_config[0].peered_network
      == "projects/987654321098/global/networks/vpc-hub"
    )
    error_message = "Expected peered_network normalized to project number."
  }

  assert {
    condition = (
      length(module.builder-ssh-firewall) == 1
      && module.builder-ssh-firewall[0].rules[
        "acme-il5-allow-builder-ssh"
      ].project == "my-net-host-0"
      && contains(
        tolist(
          module.builder-ssh-firewall[0].rules[
            "acme-il5-allow-builder-ssh"
          ].target_tags
        ),
        "image-builder",
      )
      && module.builder-ssh-firewall[0].rules[
        "acme-il5-allow-builder-ssh"
      ].log_config[0].metadata == "INCLUDE_ALL_METADATA"
    )
    error_message = "Expected tag-scoped logged TCP 22 firewall rule."
  }

  assert {
    condition = !strcontains(
      local.cloudbuild_config,
      "--confidential-compute-type=",
    )
    error_message = "Expected confidential flag omitted when set to null."
  }
}

run "plan_repository_trigger_enabled" {
  command = plan

  variables {
    trigger_config = {
      name              = "rhel9-stig-repo-trigger"
      approval_required = true
      filename          = "cloudbuild/cloudbuild-rhel9-stig.yaml"
      repository_event = {
        branch = "^main$"
        repository = join("", [
          "projects/my-image-factory-0/locations/us-east4/",
          "connections/internal-git/repositories/image-factory",
        ])
      }
    }
  }

  assert {
    condition     = length(google_cloudbuild_trigger.default) == 1
    error_message = "Expected one Cloud Build repository trigger."
  }

  assert {
    condition = (
      google_cloudbuild_trigger.default[0].service_account
      == module.builder-sa.id
    )
    error_message = "Expected trigger to use dedicated builder SA."
  }

  assert {
    condition = (
      google_cloudbuild_trigger.default[0].approval_config[0].approval_required
      == true
    )
    error_message = "Expected manual approval gate on trigger."
  }

  assert {
    condition = (
      google_cloudbuild_trigger.default[0].filename
      == "cloudbuild/cloudbuild-rhel9-stig.yaml"
    )
    error_message = "Expected trigger filename to match trigger_config."
  }
}

run "plan_pubsub_trigger_enabled" {
  command = plan

  variables {
    trigger_config = {
      name         = "rhel9-stig-scheduled-trigger"
      pubsub_topic = "projects/my-image-factory-0/topics/golden-image-rebuild"
    }
  }

  assert {
    condition     = length(google_cloudbuild_trigger.default) == 1
    error_message = "Expected one Cloud Build Pub/Sub trigger."
  }

  assert {
    condition = (
      google_cloudbuild_trigger.default[0].pubsub_config[0].topic
      == "projects/my-image-factory-0/topics/golden-image-rebuild"
    )
    error_message = "Expected trigger topic to match pubsub_topic."
  }

  assert {
    condition = (
      length(google_cloudbuild_trigger.default[0].build[0].step) == 2
    )
    error_message = "Expected inline Pub/Sub trigger to have 2 steps."
  }

  assert {
    condition = (
      google_cloudbuild_trigger.default[0].build[0].options[0].logging
      == "CLOUD_LOGGING_ONLY"
    )
    error_message = "Expected CLOUD_LOGGING_ONLY on Pub/Sub trigger."
  }
}

run "reject_ssh_firewall_without_full_cidr" {
  command = plan

  variables {
    enable_ssh_firewall_rule = true
    peered_network_ip_range  = "/24"
  }

  expect_failures = [
    var.enable_ssh_firewall_rule,
  ]
}

run "reject_sev_with_incompatible_machine_type" {
  command = plan

  variables {
    builder_confidential_compute_type = "SEV"
    builder_machine_type              = "e2-standard-2"
  }

  expect_failures = [
    var.builder_confidential_compute_type,
  ]
}

run "reject_gcr_io_builder_image" {
  command = plan

  variables {
    builder_image_digest = join("", [
      "gcr.io/google.com/cloudsdktool/cloud-sdk@sha256:",
      "0123456789abcdef0123456789abcdef",
      "0123456789abcdef0123456789abcdef",
    ])
  }

  expect_failures = [
    var.builder_image_digest,
  ]
}

run "reject_unpinned_builder_image_tag" {
  command = plan

  variables {
    builder_image_digest = join("", [
      "us-east4-docker.pkg.dev/my-image-factory-0/",
      "image-factory-builders/cloud-sdk:latest",
    ])
  }

  expect_failures = [
    var.builder_image_digest,
  ]
}

run "reject_guest_os_features_without_sev_capable" {
  command = plan

  variables {
    guest_os_features = ["UEFI_COMPATIBLE", "GVNIC"]
  }

  expect_failures = [
    var.guest_os_features,
  ]
}

run "reject_image_name_prefix_too_long" {
  command = plan

  variables {
    image_name_prefix = "rhel9-stig-golden-image-123"
  }

  expect_failures = [
    var.image_name_prefix,
  ]
}

run "reject_mismatched_builder_zone" {
  command = plan

  variables {
    builder_zone = "us-central1-a"
  }

  expect_failures = [
    var.builder_zone,
  ]
}

run "reject_global_kms_key" {
  command = plan

  variables {
    kms_key_id = join("", [
      "projects/my-kms-0/locations/global/",
      "keyRings/kr-0/cryptoKeys/img-key",
    ])
  }

  expect_failures = [
    var.kms_key_id,
  ]
}

run "reject_cross_region_kms_key" {
  command = plan

  variables {
    kms_key_id = join("", [
      "projects/my-kms-0/locations/us-central1/",
      "keyRings/kr-0/cryptoKeys/img-key",
    ])
  }

  expect_failures = [
    var.kms_key_id,
  ]
}

run "reject_combined_sa_id_over_30_chars" {
  command = plan

  variables {
    prefix          = "acme-il5-0"
    builder_sa_name = "image-factory-builder-long"
  }

  expect_failures = [
    var.builder_sa_name,
  ]
}

run "reject_invalid_peered_network_ip_range" {
  command = plan

  variables {
    peered_network_ip_range = "999.999.999.999/99"
  }

  expect_failures = [
    var.peered_network_ip_range,
  ]
}
