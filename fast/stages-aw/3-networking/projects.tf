/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

# tfdoc:file:description Host projects.

# VDSS Host Project
module "vdss-host-project" {
  source          = "../../../modules/project"
  billing_account = var.billing_account.id
  name            = local.project_map["vdss-host-project"]
  parent          = var.folder_ids.networking
  services = [
    "compute.googleapis.com",
    "certificatemanager.googleapis.com",
    "dns.googleapis.com",
    "iap.googleapis.com",
    "networkmanagement.googleapis.com",
    "stackdriver.googleapis.com",
    "networkservices.googleapis.com",
    "cloudkms.googleapis.com",
    "storage.googleapis.com",
    "redis.googleapis.com",
    "servicenetworking.googleapis.com",
    "networkconnectivity.googleapis.com",
    "secretmanager.googleapis.com",
    "servicedirectory.googleapis.com"
  ]
  shared_vpc_host_config = {
    enabled = true
  }
  iam = {
    "roles/dns.admin" = compact([
      try(local.service_accounts.project-factory-prod, null),
      try(local.service_accounts.shared-services, null),
    ])
    "roles/networkconnectivity.serviceAgent" = [
      "serviceAccount:service-${module.vdss-host-project.number}@gcp-sa-networkconnectivity.iam.gserviceaccount.com"
    ]
  }
  iam_bindings_additive = try(local.service_accounts.shared-services, null) == null ? {} : {
    shared-services-compute-network = {
      role   = "roles/compute.networkAdmin"
      member = local.service_accounts.shared-services
    }
    shared-services-compute-security = {
      role   = "roles/compute.securityAdmin"
      member = local.service_accounts.shared-services
    }
    shared-services-compute-instance = {
      role   = "roles/compute.instanceAdmin.v1"
      member = local.service_accounts.shared-services
    }
    shared-services-sa-admin = {
      role   = "roles/iam.serviceAccountAdmin"
      member = local.service_accounts.shared-services
    }
    shared-services-sa-user = {
      role   = "roles/iam.serviceAccountUser"
      member = local.service_accounts.shared-services
    }
  }
}

resource "google_compute_project_metadata" "metadata-vdss-host-project" {
  project = module.vdss-host-project.project_id
  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
    enable-oslogin         = true # CIS Compliance Benchmark 4.4
  }
}

# resource "google_cloud_quotas_quota_preference" "network_quota" {
#   parent   = "projects/${module.vdss-host-project.number}"
#   name     = "networks-increase-v2"
#   service  = "compute.googleapis.com"
#   quota_id = "NETWORKS-per-project"
#   quota_config {
#     preferred_value = var.network_quota_preferred_value
#   }
#   justification = "Required for multiple VPC networks in VDSS project."
#   contact_email = var.alert_email
# }

# Environment-level host projects (Shared VPC Hosts)
module "env-spoke-projects" {
  source          = "../../../modules/project"
  billing_account = var.billing_account.id
  for_each        = var.tenant_environments
  name            = local.project_map["${each.key}-net-host"]
  parent          = var.folder_ids.networking
  services = concat([
    "container.googleapis.com",
    "compute.googleapis.com",
    "dns.googleapis.com",
    "iap.googleapis.com",
    "networkmanagement.googleapis.com",
    "servicenetworking.googleapis.com",
    "stackdriver.googleapis.com",
    "vpcaccess.googleapis.com",
    "networkconnectivity.googleapis.com"
    ]
  )
  shared_vpc_host_config = {
    enabled = true
  }
  metric_scopes = [module.vdss-host-project.project_id]
  iam = {
    "roles/dns.admin" = compact([
      try(local.service_accounts.gke-dev, null),
      try(local.service_accounts.project-factory-dev, null),
      try(local.service_accounts.project-factory-prod, null),
    ])
  }
  iam_bindings_additive = {
    vdss_ncc_sa = {
      role   = "roles/networkconnectivity.serviceAgent"
      member = "serviceAccount:service-${module.vdss-host-project.number}@gcp-sa-networkconnectivity.iam.gserviceaccount.com"
    }
  }
}
