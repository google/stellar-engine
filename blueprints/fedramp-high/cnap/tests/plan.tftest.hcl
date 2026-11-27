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

mock_provider "google" {
  mock_data "google_project" {
    defaults = {
      number     = "123456789012"
      project_id = "xxxx-main-0"
    }
  }
  mock_data "google_compute_zones" {
    defaults = {
      names = ["us-east4-a", "us-east4-b", "us-east4-c"]
    }
  }
  mock_data "google_compute_network" {
    defaults = {
      id        = "projects/xxxx-prod-net-host/global/networks/prod-spoke-0"
      self_link = "https://www.googleapis.com/compute/v1/projects/xxxx-prod-net-host/global/networks/prod-spoke-0"
    }
  }
  mock_data "google_compute_subnetwork" {
    defaults = {
      id            = "projects/xxxx-prod-net-host/regions/us-east4/subnetworks/prod-tenant-1-subnet"
      self_link     = "https://www.googleapis.com/compute/v1/projects/xxxx-prod-net-host/regions/us-east4/subnetworks/prod-tenant-1-subnet"
      ip_cidr_range = "10.40.2.0/24"
    }
  }
  mock_resource "google_service_account" {
    defaults = {
      email  = "cnap-app-compute-sa@xxxx-main-0.iam.gserviceaccount.com"
      member = "serviceAccount:cnap-app-compute-sa@xxxx-main-0.iam.gserviceaccount.com"
    }
  }
}

mock_provider "google-beta" {
  mock_resource "google_project_service_identity" {
    defaults = {
      email  = "service-123456789012@serverless-robot-prod.iam.gserviceaccount.com"
      member = "serviceAccount:service-123456789012@serverless-robot-prod.iam.gserviceaccount.com"
    }
  }
}
mock_provider "tls" {}

variables {
  access_policy_number = 123456789012
  default_backend      = "easy"
  domain               = "xxxx.example.com"
  main_project_id      = "xxxx-main-0"
  network_name         = "prod-spoke-0"
  network_project_id   = "xxxx-prod-net-host"
  prefix               = "xxxx"
  region               = "us-east4"
}

run "plan_additive_access_levels_and_main_project_alb" {
  command = apply

  override_data {
    target = data.google_project.landing_project
    values = {
      number     = "987654321098"
      project_id = "xxxx-prod-net-host"
    }
  }

  assert {
    condition     = google_access_context_manager_access_level.us.parent == "accessPolicies/123456789012" && toset(google_access_context_manager_access_level.lenient_device.basic[0].conditions[0].required_access_levels) == toset([google_access_context_manager_access_level.us.name]) && length(google_access_context_manager_access_level.expire) == 0
    error_message = "Access levels must be additive per-level resources without an expired 2025 level by default."
  }

  assert {
    condition     = google_org_policy_policy.allow_external_lb.parent == "projects/123456789012" && google_compute_address.cnap_ext_ip.project == "xxxx-main-0" && google_compute_firewall.allow_app.project == "xxxx-prod-net-host"
    error_message = "External LB Org Policy and IP must target main_project_id while firewall targets the VPC host project."
  }

  assert {
    condition     = data.google_compute_subnetwork.default.project == "xxxx-prod-net-host" && data.google_compute_subnetwork.proxy.name == "proxy-us-east4" && data.google_compute_subnetwork.proxy.project == "xxxx-prod-net-host"
    error_message = "Subnetwork lookups must default to network_project_id and resolve proxy-<region>."
  }

  assert {
    condition     = length(google_compute_shared_vpc_host_project.host) == 0 && !contains(tls_self_signed_cert.default.dns_names, " easy-vm.xxxx.example.com") && length(tls_self_signed_cert.default.dns_names) == 4
    error_message = "Shared VPC host registration must default to false and SANs must omit duplicate leading-space entries."
  }

  assert {
    condition     = google_project_service.services["cloudkms.googleapis.com"].service == "cloudkms.googleapis.com" && google_cloud_run_v2_service.cloud_run_apps["easy"].template[0].encryption_key == module.kms.keys.default.id
    error_message = "Cloud KMS API must be enabled and Cloud Run services must use CMEK."
  }
}

run "plan_opt_in_shared_vpc_custom_proxy_and_expiry_level" {
  command = plan

  variables {
    access_expiry_timestamp = "2027-01-01T00:00:00Z"
    enable_shared_vpc_host  = true
    net_project             = "custom-vpc-host"
    proxy_subnetwork_name   = "custom-proxy"
  }

  assert {
    condition     = length(google_compute_shared_vpc_host_project.host) == 1 && length(google_access_context_manager_access_level.expire) == 1 && data.google_compute_network.network.project == "custom-vpc-host" && data.google_compute_subnetwork.proxy.name == "custom-proxy"
    error_message = "Opt-in Shared VPC host, access expiry level, net_project override, and custom proxy subnetwork must apply when set."
  }
}
