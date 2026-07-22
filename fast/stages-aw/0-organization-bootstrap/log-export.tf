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

locals {
  primary_gcs_region = element(local.locations.gcs, 0)
}

module "org-logging-bucket" {
  source        = "../../../modules/logging-bucket"
  for_each      = toset(local.locations.logging)
  name          = "${element(split(".", var.organization.domain), 0)}-org-log-bucket-${each.key}"
  parent_type   = "project"
  parent        = module.centralized-logging-project.project_id
  location      = each.value
  retention     = 30
  description   = "Organization-level audit logs - captures org-level IAM, billing, org policies, and administrative activities"
  log_analytics = { enable = true }
  kms_key_name  = coalesce(var.logging_kms_key, module.logging-kms[each.key].keys["log-sink"].id)
  depends_on = [
    module.organization-logging,
    module.logging-kms
  ]
}

module "folder-logging-bucket" {
  source        = "../../../modules/logging-bucket"
  for_each      = toset(local.locations.logging)
  name          = "${lower(replace(google_assured_workloads_workload.organization[0].display_name, " ", "-"))}-log-bucket-${each.key}"
  parent_type   = "project"
  parent        = module.centralized-logging-project.project_id
  location      = each.value
  retention     = 30
  description   = "Folder-level audit logs."
  log_analytics = { enable = true }
  kms_key_name  = coalesce(var.logging_kms_key, module.logging-kms[each.key].keys["log-sink"].id)
  depends_on = [
    module.organization-logging,
    module.logging-kms
  ]
}

resource "google_logging_organization_sink" "org_logging_sink" {
  for_each    = toset(local.locations.logging)
  name        = "org-logging-sink-${each.key}"
  org_id      = var.organization.id
  destination = "logging.googleapis.com/${module.org-logging-bucket[each.key].id}"
  depends_on = [
    module.org-logging-bucket
  ]
}

resource "google_logging_folder_sink" "folder_logging_sink" {
  for_each    = toset(local.locations.logging)
  name        = "${lower(replace(google_assured_workloads_workload.organization[0].display_name, " ", "-"))}-sink-${each.key}"
  folder      = "folders/${local.consumer_folder_id}"
  destination = "logging.googleapis.com/${module.folder-logging-bucket[each.key].id}"
  depends_on = [
    module.folder-logging-bucket
  ]
}

resource "google_project_iam_member" "org_log_writer_permission" {
  for_each = toset(local.locations.logging)
  project  = module.centralized-logging-project.project_id
  role     = "roles/logging.bucketWriter"
  member   = google_logging_organization_sink.org_logging_sink[each.key].writer_identity
  depends_on = [
    module.org-logging-bucket,
    google_logging_organization_sink.org_logging_sink
  ]
}

resource "google_project_iam_member" "folder_log_writer_permission" {
  for_each = toset(local.locations.logging)
  project  = module.centralized-logging-project.project_id
  role     = "roles/logging.bucketWriter"
  member   = google_logging_folder_sink.folder_logging_sink[each.key].writer_identity
  depends_on = [
    module.folder-logging-bucket,
    google_logging_folder_sink.folder_logging_sink
  ]
}

module "lz-logs-state-gcs" {
  source         = "../../../modules/gcs"
  project_id     = module.centralized-logging-project.project_id
  name           = "${element(split(".", var.top_level_folder.name), 0)}-org-iac"
  location       = local.primary_gcs_region
  storage_class  = local.gcs_storage_class[local.primary_gcs_region]
  versioning     = true
  depends_on     = [module.centralized-logging-project, module.gcs-kms]
  encryption_key = module.gcs-kms[local.primary_gcs_region].keys.gcs.id
}

module "lz-logs-bootstrap-gcs" {
  source         = "../../../modules/gcs"
  project_id     = module.centralized-logging-project.project_id
  name           = "${element(split(".", var.top_level_folder.name), 0)}-org-iac-bootstrap"
  location       = local.primary_gcs_region
  storage_class  = local.gcs_storage_class[local.primary_gcs_region]
  versioning     = true
  depends_on     = [module.centralized-logging-project, module.gcs-kms]
  encryption_key = module.gcs-kms[local.primary_gcs_region].keys.gcs.id
}

module "centralized-logging-project" {
  source          = "../../../modules/project"
  billing_account = var.billing_account.id
  name            = local.project_map["centralized-logging-project"]
  parent          = var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED" ? "folders/${local.consumer_folder_id}" : module.no-compliance-folder[0].folder.id
  org_policies = {
    "compute.skipDefaultNetworkCreation" = {
      rules = [{ enforce = true }]
    }
    "iam.automaticIamGrantsForDefaultServiceAccounts" = {
      rules = [{ enforce = true }]
    }
    "iam.disableServiceAccountKeyCreation" = {
      rules = [{ enforce = true }]
    }
  }
  services = concat(
    [
      "cloudkms.googleapis.com",
      "logging.googleapis.com",
      "storage.googleapis.com"
    ]
  )
  depends_on = [
    module.organization,
    google_assured_workloads_workload.organization
  ]
}

resource "google_project_service_identity" "logging" {
  provider = google-beta
  project  = module.centralized-logging-project.project_id
  service  = "logging.googleapis.com"
}

# tflint-ignore: terraform_unused_declarations
data "google_logging_project_cmek_settings" "settings" {
  project    = module.centralized-logging-project.project_id
  depends_on = [google_project_service_identity.logging]
}