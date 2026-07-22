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
  vpc    = "projects/${var.network_config.network_project_id}/global/networks/${var.network_config.network_name}"
  subnet = "projects/${var.network_config.network_project_id}/regions/${var.region}/subnetworks/${var.network_config.subnetwork_name}"

  prefix = var.prefix == null ? "" : "${var.prefix}-"

  shared_vpc_project = var.network_config.network_project_id

  shared_vpc_bindings = {
    "roles/compute.networkUser" = [
      "robot-df", "notebooks"
    ]
  }

  shared_vpc_role_members = {
    robot-df  = module.project.service_agents.dataflow.iam_email
    notebooks = module.project.service_agents.notebooks.iam_email
  }

  # reassemble in a format suitable for for_each
  shared_vpc_bindings_map = {
    for binding in flatten([
      for role, members in local.shared_vpc_bindings : [
        for member in members : { role = role, member = member }
      ]
    ]) : "${binding.role}-${binding.member}" => binding
  }
}

module "gcs-bucket" {
  count          = var.bucket_name == null ? 0 : 1
  source         = "../../../modules/gcs"
  project_id     = module.project.project_id
  name           = var.bucket_name
  prefix         = var.prefix
  location       = var.region
  storage_class  = "REGIONAL"
  versioning     = false
  encryption_key = var.service_encryption_keys.storage
  force_destroy  = !var.deletion_protection
}

# Default bucket for Cloud Build to prevent error: "'us' violates constraint ‘gcp.resourceLocations’"
# https://stackoverflow.com/questions/53206667/cloud-build-fails-with-resource-location-constraint
module "gcs-bucket-cloudbuild" {
  source         = "../../../modules/gcs"
  project_id     = module.project.project_id
  name           = "${module.project.project_id}_cloudbuild"
  location       = var.region
  storage_class  = "REGIONAL"
  versioning     = false
  encryption_key = var.service_encryption_keys.storage
  force_destroy  = !var.deletion_protection
}

module "bq-dataset" {
  count          = var.dataset_name == null ? 0 : 1
  source         = "../../../modules/bigquery-dataset"
  project_id     = module.project.project_id
  id             = var.dataset_name
  location       = var.region
  encryption_key = var.service_encryption_keys.bq
}

module "project" {
  source          = "../../../modules/project"
  name            = var.project_config.project_id
  parent          = var.project_config.parent
  billing_account = var.project_config.billing_account_id
  iam_bindings_additive = {
    # we manage aiplatform.user additively since it is also granted to
    # the vertex-shtune service agent by the project module
    aiplatform-user-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/aiplatform.user"
    }
    aiplatform-user-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/aiplatform.user"
    }
    storage-viewer-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/storage.objectViewer"
    }
    storage-viewer-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/storage.objectViewer"
    }
    storage-creator-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/storage.objectCreator"
    }
    storage-creator-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/storage.objectCreator"
    }
    service-account-user-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/iam.serviceAccountUser"
    }
    service-account-user-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/iam.serviceAccountUser"
    }
    service-account-user-cloudbuild = {
      member = module.project.service_agents.cloudbuild.iam_email,
      role   = "roles/iam.serviceAccountUser"
    }
  }
  iam = {
    "roles/artifactregistry.reader" = [module.service-account-mlops.iam_email]
    "roles/bigquery.dataEditor" = [
      module.service-account-mlops.iam_email,
      module.service-account-notebook.iam_email
    ]
    "roles/bigquery.jobUser" = [
      module.service-account-mlops.iam_email,
      module.service-account-notebook.iam_email
    ]
    "roles/bigquery.user" = [
      module.service-account-mlops.iam_email,
      module.service-account-notebook.iam_email
    ]
    "roles/cloudbuild.builds.editor" = [
      module.service-account-mlops.iam_email,
    ]
    "roles/cloudfunctions.invoker"  = [module.service-account-mlops.iam_email]
    "roles/dataflow.developer"      = [module.service-account-mlops.iam_email]
    "roles/dataflow.worker"         = [module.service-account-mlops.iam_email]
    "roles/monitoring.metricWriter" = [module.service-account-mlops.iam_email]
    "roles/run.invoker"             = [module.service-account-mlops.iam_email]
    "roles/serviceusage.serviceUsageConsumer" = [
      module.service-account-mlops.iam_email,
    ]
  }
  labels = var.labels

  service_encryption_key_ids = {
    "aiplatform.googleapis.com" = compact([var.service_encryption_keys.aiplatform])
    "bigquery.googleapis.com"   = compact([var.service_encryption_keys.bq])
    "compute.googleapis.com"    = compact([var.service_encryption_keys.notebooks])
    //"cloudbuild.googleapis.com"    = compact([var.service_encryption_keys.storage])
    "notebooks.googleapis.com" = compact([var.service_encryption_keys.notebooks])
    //"secretmanager.googleapis.com" = compact([var.service_encryption_keys.secretmanager])
    "storage.googleapis.com" = compact([var.service_encryption_keys.storage])
  }

  services = [
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "bigquerystorage.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "datacatalog.googleapis.com",
    "dataflow.googleapis.com",
    "iam.googleapis.com",
    "ml.googleapis.com",
    "monitoring.googleapis.com",
    "notebooks.googleapis.com",
    //"secretmanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "serviceusage.googleapis.com",
    "stackdriver.googleapis.com",
    "storage.googleapis.com",
    "storage-component.googleapis.com"
  ]
  shared_vpc_service_config = local.shared_vpc_project == null ? null : {
    attach       = true
    host_project = local.shared_vpc_project
  }
}

module "service-account-mlops" {
  source     = "../../../modules/iam-service-account"
  name       = "${local.prefix}sa-mlops"
  project_id = module.project.project_id
}

resource "google_project_iam_member" "shared_vpc" {
  project = var.network_config.network_project_id
  role    = "roles/compute.networkUser"
  member  = module.project.service_agents.notebooks.iam_email
}

resource "google_project_iam_member" "service_permissions" {
  for_each = toset([
    "roles/notebooks.runner",
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/iam.serviceAccountUser",
    "projects/${module.project.project_id}/roles/storage_iam",
  ])
  project = module.project.project_id
  role    = each.key
  member  = module.service-account-notebook.iam_email
}

resource "google_project_iam_custom_role" "storage_role" {
  role_id = "storage_iam"
  project = module.project.project_id
  title   = "Storage IAM Policy Role"
  permissions = [
    "storage.buckets.getIamPolicy",
    "storage.buckets.setIamPolicy",
  ]
}