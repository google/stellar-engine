# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
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
  target = data.google_compute_network.vpc
  values = {
    name      = "my-shared-vpc"
    self_link = "https://www.googleapis.com/compute/v1/projects/my-network-project/global/networks/my-shared-vpc"
  }
}

override_data {
  target = data.google_compute_subnetwork.subnet
  values = {
    name      = "syslog-us-east4"
    self_link = "https://www.googleapis.com/compute/v1/projects/my-network-project/regions/us-east4/subnetworks/syslog-us-east4"
  }
}

variables {
  project_id         = "my-syslog-project"
  network_project_id = "my-network-project"
  region             = "us-east4"
  network_name       = "my-shared-vpc"
  subnetwork_name    = "syslog-us-east4"
  kms_key_id = join("", [
    "projects/my-kms-project/locations/us-east4/",
    "keyRings/syslog-kr/cryptoKeys/gce-disk-key",
  ])
  golden_image = join("", [
    "projects/my-image-project/global/images/",
    "family/hardened-fluent-bit",
  ])
  allowed_source_ranges = [
    "192.0.2.0/24",
    "198.51.100.0/24",
  ]
  tls_secret_ids = {
    client_ca_cert = "syslog-client-ca-cert"
    server_cert    = "syslog-server-cert"
    server_key     = "syslog-server-key"
  }
  min_replicas   = 2
  max_replicas   = 6
  ilb_ip_address = "192.0.2.10"
}

run "plan_hardened_syslog_collector" {
  command = plan

  assert {
    condition = (
      length(google_project_service.apis) == 4 &&
      length(time_sleep.service_agent_propagation) == 1 &&
      time_sleep.service_agent_propagation[0].create_duration == "60s"
    )
    error_message = "Expected 4 project APIs and 60s propagation wait."
  }

  assert {
    condition = (
      module.syslog-sa.email
      == "syslog-collector-sa@my-syslog-project.iam.gserviceaccount.com"
    )
    error_message = "Expected dedicated syslog collector service account."
  }

  assert {
    condition = (
      length(google_secret_manager_regional_secret_iam_member.tls_secret) == 3
    )
    error_message = "Expected per-secret Regional Secret Manager bindings."
  }

  assert {
    condition = alltrue([
      for k, b in google_secret_manager_regional_secret_iam_member.tls_secret :
      b.role == "roles/secretmanager.secretAccessor" &&
      b.location == "us-east4" &&
      b.project == "my-syslog-project" &&
      b.member == join("", [
        "serviceAccount:syslog-collector-sa@",
        "my-syslog-project.iam.gserviceaccount.com",
      ])
    ])
    error_message = "Expected secret-scoped secretAccessor in us-east4."
  }

  assert {
    condition = (
      google_kms_crypto_key_iam_member.compute_cmek[0].member == join("", [
        "serviceAccount:service-123456789012@",
        "compute-system.iam.gserviceaccount.com",
      ])
    )
    error_message = "Expected Compute Engine service agent CMEK binding."
  }

  assert {
    condition = (
      length(google_compute_subnetwork_iam_member.shared_vpc_network_user) == 0
    )
    error_message = "Expected Shared VPC subnet IAM disabled by default."
  }

  assert {
    condition = (
      module.syslog-ilb.forwarding_rules[""].load_balancing_scheme
      == "INTERNAL" &&
      module.syslog-ilb.forwarding_rules[""].ip_protocol == "TCP" &&
      module.syslog-ilb.forwarding_rules[""].ip_address == "192.0.2.10" &&
      contains(
        tolist(module.syslog-ilb.forwarding_rules[""].ports),
        "6514",
      )
    )
    error_message = "Expected internal NLB exposing TCP port 6514."
  }

  assert {
    condition = (
      module.syslog-firewall.rules[
        "syslog-collector-allow-syslog"
      ].project == "my-network-project" &&
      module.syslog-firewall.rules[
        "syslog-collector-allow-syslog"
      ].log_config[0].metadata == "INCLUDE_ALL_METADATA" &&
      contains(
        tolist(
          module.syslog-firewall.rules[
            "syslog-collector-allow-syslog"
          ].target_service_accounts
        ),
        "syslog-collector-sa@my-syslog-project.iam.gserviceaccount.com",
      ) &&
      module.syslog-firewall.rules[
        "syslog-collector-allow-syslog"
      ].target_tags == null &&
      module.syslog-firewall.rules[
        "syslog-collector-allow-hc"
      ].log_config[0].metadata == "INCLUDE_ALL_METADATA" &&
      contains(
        tolist(
          module.syslog-firewall.rules[
            "syslog-collector-allow-hc"
          ].source_ranges
        ),
        "35.191.0.0/16",
      ) &&
      contains(
        tolist(
          module.syslog-firewall.rules[
            "syslog-collector-allow-hc"
          ].source_ranges
        ),
        "130.211.0.0/22",
      ) &&
      contains(
        tolist(
          module.syslog-firewall.rules[
            "syslog-collector-allow-hc"
          ].target_service_accounts
        ),
        "syslog-collector-sa@my-syslog-project.iam.gserviceaccount.com",
      )
    )
    error_message = "Expected SA-targeted logged ingress firewall rules."
  }
}

run "plan_shared_vpc_subnet_iam_enabled" {
  command = plan

  variables {
    grant_shared_vpc_subnet_iam = true
  }

  assert {
    condition = (
      length(google_compute_subnetwork_iam_member.shared_vpc_network_user)
      == 2 &&
      google_compute_subnetwork_iam_member.shared_vpc_network_user[
        "cloudservices"
      ].member
      == "serviceAccount:123456789012@cloudservices.gserviceaccount.com" &&
      google_compute_subnetwork_iam_member.shared_vpc_network_user[
        "syslog_sa"
        ].member == join("", [
          "serviceAccount:syslog-collector-sa@",
          "my-syslog-project.iam.gserviceaccount.com",
      ])
    )
    error_message = "Expected Shared VPC networkUser for SA and cloudservices."
  }
}

run "apply_mock_hardened_syslog_collector" {
  command = apply

  assert {
    condition = (
      module.syslog-template.template.machine_type == "n2d-standard-2"
    )
    error_message = "Expected default SEV-compatible n2d-standard-2."
  }

  assert {
    condition = (
      module.syslog-template.template.confidential_instance_config[
        0
      ].enable_confidential_compute == true
    )
    error_message = "Expected Confidential Compute (SEV) on template."
  }

  assert {
    condition = (
      module.syslog-template.template.shielded_instance_config[
        0
      ].enable_secure_boot == true &&
      module.syslog-template.template.shielded_instance_config[
        0
      ].enable_vtpm == true &&
      module.syslog-template.template.shielded_instance_config[
        0
      ].enable_integrity_monitoring == true
    )
    error_message = "Expected Shielded VM controls enabled on template."
  }

  assert {
    condition = (
      module.syslog-template.template.disk[0].disk_encryption_key[
        0
      ].kms_key_self_link == var.kms_key_id
    )
    error_message = "Expected CMEK encryption on collector boot disk."
  }

  assert {
    condition = (
      length(
        module.syslog-template.template.network_interface[0].access_config
      ) == 0
    )
    error_message = "Expected private-only collector instances."
  }

  assert {
    condition = (
      module.syslog-template.template.metadata["enable-oslogin"] == "TRUE" &&
      module.syslog-template.template.metadata[
        "block-project-ssh-keys"
      ] == "TRUE" &&
      module.syslog-template.template.metadata[
        "serial-port-enable"
      ] == "false"
    )
    error_message = "Expected OS Login, key block, and serial port disabled."
  }

  assert {
    condition = (
      !strcontains(
        jsonencode(module.syslog-template.template.metadata),
        "PRIVATE KEY",
      ) &&
      !strcontains(
        jsonencode(module.syslog-template.template.metadata),
        "BEGIN CERTIFICATE",
      ) &&
      !strcontains(
        module.syslog-template.template.metadata_startup_script,
        "PRIVATE KEY",
      ) &&
      !strcontains(
        module.syslog-template.template.metadata_startup_script,
        "BEGIN CERTIFICATE",
      )
    )
    error_message = "No private keys or certs in GCE metadata."
  }

  assert {
    condition = (
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "/run/fluent-bit-tls",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "/opt/fluent-bit/etc/parsers.conf",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "chmod 0600",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "Format octet_counting",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "tls.verify_client_cert On",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "tls.min_version TLSv1.2",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "--dry-run -c",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "10-startup-order.conf",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "After=google-startup-scripts.service",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "systemctl daemon-reload",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "systemctl reset-failed fluent-bit.service",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "--location=",
      ) &&
      strcontains(
        module.syslog-template.template.metadata_startup_script,
        "CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER",
      ) &&
      !strcontains(
        module.syslog-template.template.metadata_startup_script,
        "nft delete",
      ) &&
      !strcontains(
        module.syslog-template.template.metadata_startup_script,
        "curl ",
      )
    )
    error_message = "Startup script failed security or mTLS assertions."
  }

  assert {
    condition = (
      module.syslog-mig.autoscaler.autoscaling_policy[0].min_replicas >= 2 &&
      module.syslog-mig.autoscaler.autoscaling_policy[0].max_replicas == 6
    )
    error_message = "Expected regional autoscaler with min_replicas >= 2."
  }

  assert {
    condition = (
      module.syslog-mig.group_manager.update_policy[0].type == "PROACTIVE" &&
      module.syslog-mig.group_manager.update_policy[
        0
      ].minimal_action == "REPLACE" &&
      module.syslog-mig.group_manager.update_policy[
        0
      ].max_unavailable_fixed == 0 &&
      module.syslog-mig.group_manager.update_policy[0].max_surge_fixed >= 3
    )
    error_message = "Expected PROACTIVE zero-downtime MIG update policy."
  }

  assert {
    condition = (
      length(module.syslog-mig.group_manager.auto_healing_policies) == 1 &&
      module.syslog-mig.group_manager.auto_healing_policies[
        0
      ].initial_delay_sec == 180 &&
      module.syslog-mig.group_manager.instance_lifecycle_policy[
        0
      ].default_action_on_failure == "REPAIR" &&
      module.syslog-mig.group_manager.instance_lifecycle_policy[
        0
      ].force_update_on_repair == "YES" &&
      module.syslog-mig.group_manager.instance_lifecycle_policy[
        0
      ].on_failed_health_check == "DEFAULT_ACTION"
    )
    error_message = "Expected active MIG autohealing and REPAIR policy."
  }

  assert {
    condition = (
      module.syslog-ilb.health_check.http_health_check[0].port == 2020 &&
      module.syslog-ilb.health_check.http_health_check[
        0
      ].request_path == "/api/v1/health" &&
      module.syslog-ilb.health_check.log_config[0].enable == true
    )
    error_message = "Expected logged HTTP /api/v1/health probe on 2020."
  }

  assert {
    condition = (
      output.ilb_ip_address == "192.0.2.10" &&
      output.service_account_email
      == "syslog-collector-sa@my-syslog-project.iam.gserviceaccount.com" &&
      output.instance_group_manager_id != ""
    )
    error_message = "Expected non-secret blueprint outputs."
  }
}

run "reject_wildcard_ipv4_cidr" {
  command = plan

  variables {
    allowed_source_ranges = ["0.0.0.0/0"]
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_wildcard_ipv6_cidr" {
  command = plan

  variables {
    allowed_source_ranges = ["::/0"]
  }

  expect_failures = [
    var.allowed_source_ranges,
  ]
}

run "reject_single_replica_non_ha" {
  command = plan

  variables {
    min_replicas = 1
  }

  expect_failures = [
    var.min_replicas,
  ]
}

run "reject_privileged_syslog_port" {
  command = plan

  variables {
    syslog_port = 514
  }

  expect_failures = [
    var.syslog_port,
  ]
}

run "reject_invalid_syslog_port_zero" {
  command = plan

  variables {
    syslog_port = 0
  }

  expect_failures = [
    var.syslog_port,
  ]
}

run "reject_invalid_syslog_port_overflow" {
  command = plan

  variables {
    syslog_port = 70000
  }

  expect_failures = [
    var.syslog_port,
  ]
}

run "reject_privileged_health_check_port" {
  command = plan

  variables {
    health_check_port = 80
  }

  expect_failures = [
    var.health_check_port,
  ]
}

run "reject_invalid_health_check_port" {
  command = plan

  variables {
    health_check_port = 65536
  }

  expect_failures = [
    var.health_check_port,
  ]
}

run "reject_colliding_syslog_and_health_check_ports" {
  command = plan

  variables {
    health_check_port = 6514
  }

  expect_failures = [
    var.health_check_port,
  ]
}

run "reject_non_sev_machine_type" {
  command = plan

  variables {
    machine_type = "e2-medium"
  }

  expect_failures = [
    var.machine_type,
  ]
}

run "reject_inline_pem_in_tls_secret_ids" {
  command = plan

  variables {
    tls_secret_ids = {
      client_ca_cert = "syslog-client-ca-cert"
      server_cert    = "syslog-server-cert"
      server_key     = "-----BEGIN PRIVATE KEY-----"
    }
  }

  expect_failures = [
    var.tls_secret_ids,
  ]
}

run "reject_global_kms_key" {
  command = plan

  variables {
    kms_key_id = join("", [
      "projects/my-kms-project/locations/global/",
      "keyRings/syslog-kr/cryptoKeys/gce-disk-key",
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
      "projects/my-kms-project/locations/us-central1/",
      "keyRings/syslog-kr/cryptoKeys/gce-disk-key",
    ])
  }

  expect_failures = [
    var.kms_key_id,
  ]
}

run "reject_c2d_custom_machine_type" {
  command = plan

  variables {
    machine_type = "c2d-custom-4-16384"
  }

  expect_failures = [
    var.machine_type,
  ]
}

run "reject_invalid_syslog_framing_format" {
  command = plan

  variables {
    syslog_framing_format = "json"
  }

  expect_failures = [
    var.syslog_framing_format,
  ]
}
