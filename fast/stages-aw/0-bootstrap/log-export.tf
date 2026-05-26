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

# tfdoc:file:description Audit log project and sink.

locals {
  log_sink_destinations = merge(
    # use the same dataset for all sinks with `bigquery` as  destination
    {
      for k, v in var.log_sinks :
      k => module.log-export-dataset[0] if v.type == "bigquery"
    },
    # use the same gcs bucket for all sinks with `storage` as destination
    {
      for k, v in var.log_sinks :
      k => module.log-export-gcs[0] if v.type == "storage"
    },
    # use separate pubsub topics and logging buckets for sinks with
    # destination `pubsub` and `logging`
    module.log-export-pubsub,
    module.log-export-logbucket
  )
  log_types = toset([for k, v in var.log_sinks : v.type])
}

module "log-export-project" {
  source                  = "../../../modules/project"
  name                    = "audit-logs-0"
  default_service_account = "deprivilege"
  lien_reason             = "Protected by default as a core project."
  parent = coalesce(
    var.project_parent_ids.logging, module.branch-common-services-folder.folder.name
  )
  prefix          = local.prefix
  billing_account = var.billing_account.id
  contacts = (
    var.bootstrap_user != null || var.essential_contacts == null
    ? {}
    : { (var.essential_contacts) = ["ALL"] }
  )
  iam = {
    "roles/owner"  = [module.automation-tf-bootstrap-sa.iam_email]
    "roles/viewer" = [module.automation-tf-bootstrap-r-sa.iam_email]
  }
  services = [
    # "cloudresourcemanager.googleapis.com",
    # "iam.googleapis.com",
    # "serviceusage.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "stackdriver.googleapis.com",
    "cloudkms.googleapis.com",
    "pubsub.googleapis.com",
    "compute.googleapis.com"
  ]
}

resource "google_compute_project_metadata" "metadata-log-export" {
  project = module.log-export-project.project_id
  metadata = {
    block-project-ssh-keys = "TRUE" # CIS Compliance Benchmark 4.3
    enable-oslogin         = "TRUE" # CIS Compliance Benchmark 4.4
  }
}

# one log export per type, with conditionals to skip those not needed

module "log-export-dataset" {
  source         = "../../../modules/bigquery-dataset"
  count          = contains(local.log_types, "bigquery") ? 1 : 0
  project_id     = module.log-export-project.project_id
  id             = "logs"
  friendly_name  = "Audit logs export."
  location       = local.locations.bq
  encryption_key = try(var.logging_kms_key, module.logging-kms.keys["log-sink"])

}

module "log-export-gcs" {
  source         = "../../../modules/gcs"
  count          = contains(local.log_types, "storage") ? 1 : 0
  project_id     = module.log-export-project.project_id
  name           = "logs"
  prefix         = local.prefix
  location       = local.locations.gcs
  storage_class  = local.gcs_storage_class
  force_destroy  = true
  encryption_key = try(var.logging_kms_key, module.logging-kms.keys["log-sink"])
}

module "log-export-logbucket" {
  source        = "../../../modules/logging-bucket"
  for_each      = toset([for k, v in var.log_sinks : k if v.type == "logging"])
  parent_type   = "project"
  parent        = module.log-export-project.project_id
  id            = each.key
  location      = local.locations.logging
  log_analytics = { enable = true }
  kms_key_name  = try(var.logging_kms_key, module.logging-kms.keys["log-sink"])
  # org-level logging settings ready before we create any logging buckets
  depends_on = [module.organization-logging]
}

module "log-export-pubsub" {
  source     = "../../../modules/pubsub"
  for_each   = toset([for k, v in var.log_sinks : k if v.type == "pubsub"])
  project_id = module.log-export-project.project_id
  name       = each.key
  regions    = local.locations.pubsub
  kms_key    = try(var.logging_kms_key, module.logging-kms.keys["log-sink"])
}
