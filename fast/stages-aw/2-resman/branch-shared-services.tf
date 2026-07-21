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

# tfdoc:file:description Shared services stage resources.

# automation service account

module "branch-shared-services-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = var.automation.project_id
  name         = "resman-shdsvc-0"
  display_name = "Terraform resman shared-services service account."
  prefix       = var.prefix
  iam = {
    "roles/iam.serviceAccountTokenCreator" = compact([
      try(module.branch-shared-services-sa-cicd[0].iam_email, null),
      try(module.branch-shared-services-r-sa-cicd[0].iam_email, null)
    ])
  }
  iam_project_roles = {
    (var.automation.project_id)      = ["roles/serviceusage.serviceUsageConsumer"]
    (var.shared_services_project_id) = ["roles/owner"]
  }
  iam_storage_roles = {
    (var.automation.outputs_bucket) = ["roles/storage.objectAdmin"]
  }
  iam_folder_roles = {
    (var.common_services_folder) = ["roles/compute.xpnAdmin"]
  }
}

# automation read-only service account

module "branch-shared-services-r-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = var.automation.project_id
  name         = "resman-shdsvc-0r"
  display_name = "Terraform resman shared-services service account (read-only)."
  prefix       = var.prefix
  iam          = {}
  iam_project_roles = {
    (var.automation.project_id) = ["roles/serviceusage.serviceUsageConsumer"]
  }
  iam_storage_roles = {
    (var.automation.outputs_bucket) = [var.custom_roles["storage_viewer"]]
  }
}

# automation bucket

module "branch-shared-services-gcs" {
  source        = "../../../modules/gcs"
  project_id    = var.automation.project_id
  name          = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-resman-shdsvc")
  prefix        = var.prefix
  location      = local.primary_location_gcs
  storage_class = local.gcs_storage_class
  versioning    = true
  iam = {
    "roles/storage.objectAdmin"  = [module.branch-shared-services-sa.iam_email]
    "roles/storage.objectViewer" = [module.branch-shared-services-r-sa.iam_email]
  }

  encryption_key = "projects/${var.automation.project_id}/locations/${local.primary_location_kms}/keyRings/gcs-${local.primary_location_kms}/cryptoKeys/gcs"
}
