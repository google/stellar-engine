/**
 * Copyright 2026 Google LLC
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
# tfdoc:file:description Networking stage resources.

locals {
  # FAST-specific IAM
  _network_folder_fast_iam = {
    # read-write (apply) automation service account
    "roles/logging.admin"                  = [module.branch-network-sa.iam_email]
    "roles/owner"                          = [module.branch-network-sa.iam_email]
    "roles/resourcemanager.folderAdmin"    = [module.branch-network-sa.iam_email]
    "roles/resourcemanager.projectCreator" = [module.branch-network-sa.iam_email]
    "roles/compute.xpnAdmin"               = [module.branch-network-sa.iam_email]
    # read-only (plan) automation service account
    "roles/viewer"                       = [module.branch-network-r-sa.iam_email]
    "roles/resourcemanager.folderViewer" = [module.branch-network-r-sa.iam_email]
  }
  # deep-merge FAST-specific IAM with user-provided bindings in var.folder_iam
  _network_folder_iam = merge(
    var.folder_iam.network,
    {
      for role, principals in local._network_folder_fast_iam :
      role => distinct(concat(principals, lookup(var.folder_iam.network, role, [])))
    }
  )
}

module "branch-network-folder" {
  source = "../../../modules/folder"
  parent = var.common_services_folder
  name   = "Networking"
  iam_by_principals = {
    (local.principals.gcp-vpc-network-admins) = [
      # owner and viewer roles are broad and might grant unwanted access
      # replace them with more selective custom roles for production deployments
      "roles/editor",
    ]
  }
  org_policies = yamldecode(file("./data/allow_ncc.yaml"))
  iam          = local._network_folder_iam
  tag_bindings = null
}

# automation service account

module "branch-network-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = var.automation.project_id
  name         = "prod-resman-net-0"
  display_name = "Terraform resman networking service account."
  prefix       = var.prefix
  iam = {
    "roles/iam.serviceAccountTokenCreator" = compact([
      try(module.branch-network-sa-cicd[0].iam_email, null),
      try(module.branch-network-r-sa-cicd[0].iam_email, null)
    ])
  }
  iam_project_roles = {
    (var.automation.project_id)      = ["roles/serviceusage.serviceUsageConsumer"],
    (var.shared_services_project_id) = ["roles/networkconnectivity.spokeAdmin"]
  }
  iam_storage_roles = {
    (var.automation.outputs_bucket) = ["roles/storage.objectAdmin"]
  }
}


resource "google_billing_account_iam_member" "networking_billing_admins" {
  billing_account_id = var.billing_account.id
  role               = "roles/billing.admin"
  member             = "serviceAccount:${module.branch-network-sa.email}"
}
# automation read-only service account

module "branch-network-r-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = var.automation.project_id
  name         = "prod-resman-net-0r"
  display_name = "Terraform resman networking service account (read-only)."
  prefix       = var.prefix
  iam = {
    "roles/iam.serviceAccountTokenCreator" = compact([
      try(module.branch-network-r-sa-cicd[0].iam_email, null)
    ])
  }
  iam_project_roles = {
    (var.automation.project_id) = ["roles/serviceusage.serviceUsageConsumer"]
  }
  iam_storage_roles = {
    (var.automation.outputs_bucket) = [var.custom_roles["storage_viewer"]]
  }
}

# automation bucket

module "branch-network-gcs" {
  source        = "../../../modules/gcs"
  project_id    = var.automation.project_id
  name          = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-prod-resman-net-0")
  prefix        = var.prefix
  location      = local.primary_location_gcs
  storage_class = local.gcs_storage_class
  versioning    = true
  iam = {
    "roles/storage.objectAdmin"  = [module.branch-network-sa.iam_email]
    "roles/storage.objectViewer" = [module.branch-network-r-sa.iam_email]
  }

  encryption_key = "projects/${var.automation.project_id}/locations/${local.primary_location_gcs}/keyRings/gcs-${local.primary_location_kms}/cryptoKeys/gcs"
}
