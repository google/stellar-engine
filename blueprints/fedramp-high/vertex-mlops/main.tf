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

  # Cloud Storage roles are granted on the buckets this blueprint creates
  # instead of on the project, so they do not reach any other bucket.
  bucket_iam_bindings_additive = {
    storage-creator-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/storage.objectCreator"
    }
    storage-creator-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/storage.objectCreator"
    }
    storage-iam-notebook = {
      member = module.service-account-notebook.iam_email
      role   = google_project_iam_custom_role.storage_role.id
    }
    storage-viewer-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/storage.objectViewer"
    }
    storage-viewer-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/storage.objectViewer"
    }
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

  iam_bindings_additive = local.bucket_iam_bindings_additive
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

  iam_bindings_additive = local.bucket_iam_bindings_additive
}

module "bq-dataset" {
  count          = var.dataset_name == null ? 0 : 1
  source         = "../../../modules/bigquery-dataset"
  project_id     = module.project.project_id
  id             = var.dataset_name
  location       = var.region
  encryption_key = var.service_encryption_keys.bq
  # roles/bigquery.dataEditor is granted on this dataset instead of on the
  # project, so it does not reach any other dataset.
  iam_bindings_additive = {
    data-editor-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/bigquery.dataEditor"
    }
    data-editor-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/bigquery.dataEditor"
    }
  }
}

module "project" {
  source          = "../../../modules/project"
  name            = var.project_config.project_id
  parent          = var.project_config.parent
  billing_account = var.project_config.billing_account_id
  iam_bindings_additive = {
    # we manage aiplatform.user additively since it is also granted to
    # the vertex-shtune service agent by the project module
    # it stays on the project since pipelines, jobs, models and endpoints are
    # created at run time, so there is no resource to bind it to
    aiplatform-user-mlops = {
      member = module.service-account-mlops.iam_email
      role   = "roles/aiplatform.user"
    }
    aiplatform-user-notebook = {
      member = module.service-account-notebook.iam_email
      role   = "roles/aiplatform.user"
    }
  }
  # The roles below stay on the project. Each comment states why the role
  # cannot be bound to a resource that this blueprint creates.
  iam = {
    # Artifact Registry repositories are created by the workload, not here.
    "roles/artifactregistry.reader" = [module.service-account-mlops.iam_email]
    # BigQuery jobs run in the project, so job creation is project-scoped.
    "roles/bigquery.jobUser" = [
      module.service-account-mlops.iam_email,
      module.service-account-notebook.iam_email
    ]
    # Read sessions and dataset creation are project-scoped permissions.
    "roles/bigquery.user" = [
      module.service-account-mlops.iam_email,
      module.service-account-notebook.iam_email
    ]
    # Cloud Build builds have no resource-level IAM policy.
    "roles/cloudbuild.builds.editor" = [
      module.service-account-mlops.iam_email,
    ]
    # Cloud Functions are created by the workload, not here.
    "roles/cloudfunctions.invoker" = [module.service-account-mlops.iam_email]
    # Dataflow jobs and workers are authorized on the project only.
    "roles/dataflow.developer" = [module.service-account-mlops.iam_email]
    "roles/dataflow.worker"    = [module.service-account-mlops.iam_email]
    # Metric writes are authorized on the project only.
    "roles/monitoring.metricWriter" = [module.service-account-mlops.iam_email]
    # Cloud Run services are created by the workload, not here.
    "roles/run.invoker" = [module.service-account-mlops.iam_email]
    # Service usage is authorized on the consumer project only.
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
    # roles/compute.networkUser for the Notebooks service agent is granted on
    # the subnet the Workbench instances use instead of on the host project.
    service_agent_subnet_iam = {
      "${var.region}/${var.network_config.subnetwork_name}" = ["notebooks"]
    }
  }
}

module "service-account-mlops" {
  source     = "../../../modules/iam-service-account"
  name       = "${local.prefix}sa-mlops"
  project_id = module.project.project_id
}

# roles/iam.serviceAccountUser is granted on the two service accounts instead
# of on the project, so no principal can act as any other service account.
# Each service account acts as itself to run the workloads it submits, and the
# Cloud Build service agent acts as the MLOps service account to run builds.
# The bindings are declared here and not through the service account modules,
# so that no module reads its own outputs.
resource "google_service_account_iam_member" "service_account_user" {
  for_each = {
    service-account-user-cloudbuild = {
      member             = module.project.service_agents.cloudbuild.iam_email
      service_account_id = module.service-account-mlops.id
    }
    service-account-user-mlops = {
      member             = module.service-account-mlops.iam_email
      service_account_id = module.service-account-mlops.id
    }
    service-account-user-notebook = {
      member             = module.service-account-notebook.iam_email
      service_account_id = module.service-account-notebook.id
    }
  }
  service_account_id = each.value.service_account_id
  role               = "roles/iam.serviceAccountUser"
  member             = each.value.member
}

# The roles below stay on the project, since notebook executions, schedules
# and Vertex AI resources are created at run time and there is no resource to
# bind a role to. roles/aiplatform.user repeats the additive binding in the
# project module. It stays here because destroying this copy would remove the
# shared binding until the next apply restores it.
resource "google_project_iam_member" "service_permissions" {
  for_each = toset([
    "roles/notebooks.runner",
    "roles/aiplatform.user",
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