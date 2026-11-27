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
  target = data.google_storage_project_service_account.gcs_sa
  values = {
    email_address = "service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
    member        = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

override_resource {
  target = google_project_service_identity.container_engine_robot
  values = {
    email  = "service-123456789012@container-engine-robot.iam.gserviceaccount.com"
    member = "serviceAccount:service-123456789012@container-engine-robot.iam.gserviceaccount.com"
  }
}

override_resource {
  target = google_service_account.gatekeeper_sa
  values = {
    name   = "projects/test-gke-hardened-project/serviceAccounts/gatekeeper-metrics-sa@test-gke-hardened-project.iam.gserviceaccount.com"
    email  = "gatekeeper-metrics-sa@test-gke-hardened-project.iam.gserviceaccount.com"
    member = "serviceAccount:gatekeeper-metrics-sa@test-gke-hardened-project.iam.gserviceaccount.com"
  }
}

override_resource {
  target = google_service_account.gke
  values = {
    name   = "projects/test-gke-hardened-project/serviceAccounts/gke-test-gke-hardened-project@test-gke-hardened-project.iam.gserviceaccount.com"
    email  = "gke-test-gke-hardened-project@test-gke-hardened-project.iam.gserviceaccount.com"
    member = "serviceAccount:gke-test-gke-hardened-project@test-gke-hardened-project.iam.gserviceaccount.com"
  }
}

variables {
  main_project_id                     = "test-gke-hardened-project"
  region                              = "us-central1"
  gatekeeper_sa                       = "gatekeeper-metrics-sa"
  gke_cluster_enable_private_endpoint = true
  gke_cluster_master_global_access    = false
  gke_cluster_name                    = "test-gke-cluster"
  gke_initial_node_per_zone           = 1
  gke_nodepool_name                   = "test-nodepool"
  gke_vpc_master_ipv4_cidr_block      = "192.168.0.0/28"
  kms_keyring_name = {
    location = "us-central1"
    name     = "test-gke-keyring"
  }
  local_admin_external_ip                  = ["203.0.113.10/32"]
  master_authorized_ranges_ip_ranges       = "10.0.0.0/8"
  nat_gateway_name                         = "test-nat-gw"
  nat_router_name                          = "test-nat-router"
  network_name                             = "test-gke-vpc"
  node_config_tags                         = ["gke-node"]
  node_disk_size_gb                        = 20
  nodepool_node_count                      = { initial = 1 }
  source_dir                               = "policies"
  source_repo                              = "https://example.com/example-org/gke-policies.git"
  subnetwork_ip_cidr_range_1               = "10.0.4.0/22"
  subnetwork_name                          = "gke-subnet"
  subnetwork_secondary_ip_range_pods_1     = "10.4.0.0/14"
  subnetwork_secondary_ip_range_services_1 = "10.0.32.0/20"
}

run "plan_defaults_and_dynamic_bastion" {
  command = plan

  assert {
    condition     = contains(keys(var.kms_key_names), "default")
    error_message = "Expected default kms_key_names to include key 'default'."
  }

  assert {
    condition     = google_service_account.gke.account_id == "gke-test-gke-hardened-project"
    error_message = "Expected bounded GKE service account ID."
  }

  assert {
    condition     = google_project_service.required_apis["container.googleapis.com"].service == "container.googleapis.com"
    error_message = "Expected container.googleapis.com to be enabled."
  }

  assert {
    condition     = google_project_service.required_apis["anthosconfigmanagement.googleapis.com"].service == "anthosconfigmanagement.googleapis.com"
    error_message = "Expected anthosconfigmanagement.googleapis.com to be enabled."
  }

  assert {
    condition     = google_project_service.required_apis["storage.googleapis.com"].service == "storage.googleapis.com"
    error_message = "Expected storage.googleapis.com to be enabled."
  }

  assert {
    condition     = google_compute_router_nat.nat.project == "test-gke-hardened-project"
    error_message = "Expected NAT gateway to set project explicitly."
  }
}

run "apply_bastion_zone_and_cos_stable" {
  command = apply

  assert {
    condition     = module.compute-vm.instance.zone == "us-central1-a"
    error_message = "Expected bastion VM zone to derive dynamically from var.region."
  }

  assert {
    condition     = module.compute-vm.instance.boot_disk[0].initialize_params[0].image == "projects/cos-cloud/global/images/family/cos-stable"
    error_message = "Expected bastion VM to use cos-stable image family."
  }

  assert {
    condition     = google_project_service_identity.container_engine_robot.member == "serviceAccount:service-123456789012@container-engine-robot.iam.gserviceaccount.com"
    error_message = "Expected container-engine-robot service identity member to resolve."
  }

  assert {
    condition     = data.google_storage_project_service_account.gcs_sa.member == "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
    error_message = "Expected Cloud Storage service agent to resolve via data.google_storage_project_service_account."
  }
}

run "apply_explicit_bastion_zone_override" {
  command = apply

  variables {
    region          = "us-east1"
    bastion_vm_zone = "us-east1-b"
    kms_keyring_name = {
      location = "us-east1"
      name     = "test-gke-keyring"
    }
  }

  assert {
    condition     = module.compute-vm.instance.zone == "us-east1-b"
    error_message = "Expected explicit bastion_vm_zone override to apply."
  }
}

run "reject_kms_key_names_without_default" {
  command = plan

  variables {
    kms_key_names = {
      "key-gke" = {
        rotation_period = "7776000s"
      }
    }
  }

  expect_failures = [
    var.kms_key_names,
  ]
}

run "reject_bastion_zone_outside_region" {
  command = plan

  variables {
    bastion_vm_zone = "us-east4-a"
  }

  expect_failures = [
    var.bastion_vm_zone,
  ]
}
