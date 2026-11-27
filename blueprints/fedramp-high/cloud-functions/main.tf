# Copyright 2025 Google LLC
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

locals {
  # Cloud Run functions names the Cloud Run service behind a function after
  # the function, in lowercase and with hyphens in place of underscores.
  function_service_name = lower(replace(var.function_name, "_", "-"))
}

data "google_project" "current" {
  project_id = var.main_project_id
}

module "service-account-runner" {
  source       = "../../../modules/iam-service-account"
  name         = "cf-runner-sa"
  project_id   = var.main_project_id
  display_name = "Cloud Functions Runner Service Account"
}

resource "google_project_service" "cloud_functions_apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "binaryauthorization.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
  ])

  project            = var.main_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service_identity" "cloudfunctions" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "cloudfunctions.googleapis.com"
  depends_on = [google_project_service.cloud_functions_apis]
}

resource "google_project_service_identity" "artifactregistry" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "artifactregistry.googleapis.com"
  depends_on = [google_project_service.cloud_functions_apis]
}

resource "google_project_service_identity" "run" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "run.googleapis.com"
  depends_on = [google_project_service.cloud_functions_apis]
}

data "google_storage_project_service_account" "gcs_sa" {
  project    = var.main_project_id
  depends_on = [google_project_service.cloud_functions_apis]
}

resource "time_sleep" "kms_iam_propagation" {
  create_duration = "60s"
  depends_on = [
    google_project_service.cloud_functions_apis,
    google_project_service_identity.artifactregistry,
    google_project_service_identity.cloudfunctions,
    google_project_service_identity.run,
    data.google_storage_project_service_account.gcs_sa,
  ]
}

# Cloud Build does not support IAM policies on builds, so the project is the
# narrowest resource that accepts this role. The role also carries
# project-wide Cloud Storage object and Artifact Registry write permissions.
resource "google_project_iam_member" "cloud_build" {
  project = var.main_project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = module.service-account-runner.iam_email
}

# The Cloud Run service behind the function exists only after the module
# deployment, so the binding waits for it.
resource "google_cloud_run_v2_service_iam_member" "cloud_invoker" {
  project    = var.main_project_id
  location   = var.region
  name       = local.function_service_name
  role       = "roles/run.invoker"
  member     = module.service-account-runner.iam_email
  depends_on = [module.cloud-function]
}

resource "google_kms_crypto_key_iam_member" "cloud_storage" {
  for_each = {
    artifactregistry = google_project_service_identity.artifactregistry.member
    cloudfunctions   = google_project_service_identity.cloudfunctions.member
    compute          = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
    run              = google_project_service_identity.run.member
    storage          = data.google_storage_project_service_account.gcs_sa.member
  }
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
  depends_on    = [time_sleep.kms_iam_propagation]
}

moved {
  from = google_project_iam_member.logging_logWriter
  to   = google_project_iam_member.logging_log_writer
}

# Cloud Logging authorizes log entry writes against the project that receives
# them, so the project is the narrowest resource that accepts this role.
resource "google_project_iam_member" "logging_log_writer" {
  project = var.main_project_id
  role    = "roles/logging.logWriter"
  member  = module.service-account-runner.iam_email
}

module "cloud-function" {
  source      = "../../../modules/cloud-function-v2"
  project_id  = var.main_project_id
  region      = var.region
  name        = var.function_name
  description = var.description
  bucket_name = module.bucket.name
  bundle_config = {
    path = var.bundle_config == null ? "${path.module}/src-code" : var.bundle_config.path
    folder_options = (
      var.bundle_config == null
      ? {
        archive_path = tostring(null)
        excludes     = tolist(null)
      }
      : var.bundle_config.folder_options
    )
  }
  docker_repository_id  = module.registry-docker.id
  environment_variables = var.environment_variables
  function_config = {
    binary_authorization_policy = "default"
    cpu                         = tostring(var.function_cpu)
    entry_point                 = var.function_entry_point
    instance_count              = var.function_instance_count
    memory_mb                   = var.function_memory_mb
    runtime                     = var.function_runtime
    timeout_seconds             = var.function_timeout_seconds
  }
  ingress_settings = "ALLOW_INTERNAL_AND_GCLB"
  kms_key          = var.kms_key_name
  labels           = var.labels
  secrets          = var.secrets
  service_account_config = {
    create = false
    email  = coalesce(var.service_account, module.service-account-runner.email)
  }
  depends_on = [
    google_project_service.cloud_functions_apis,
    google_kms_crypto_key_iam_member.cloud_storage,
    module.bucket,
    module.registry-docker,
  ]
}

module "bucket" {
  source         = "../../../modules/gcs"
  project_id     = var.main_project_id
  name           = var.bucket_name
  location       = var.region
  encryption_key = var.kms_key_name
  # The deployment stages the function source with the deploying identity and
  # the build service account, not with the runner, so the runner needs no
  # project-level Cloud Storage role in addition to this bucket-level grant.
  iam = {
    "roles/storage.objectUser" = [
      module.service-account-runner.iam_email,
      data.google_storage_project_service_account.gcs_sa.member,
      "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
    ]
  }
  depends_on = [
    google_project_service.cloud_functions_apis,
    google_kms_crypto_key_iam_member.cloud_storage,
  ]
}

module "registry-docker" {
  source         = "../../../modules/artifact-registry"
  project_id     = var.main_project_id
  location       = var.region
  name           = var.artifact_registry_name
  encryption_key = var.kms_key_name
  format = {
    docker = {
      standard = {
        immutable_tags = true
      }
    }
  }
  # The repository exists before the first push, so the runner does not need
  # the project-level roles/artifactregistry.createOnPushWriter role.
  iam_bindings_additive = {
    artifactregistry-writer-runner = {
      member = module.service-account-runner.iam_email
      role   = "roles/artifactregistry.writer"
    }
  }
  depends_on = [
    google_project_service.cloud_functions_apis,
    google_kms_crypto_key_iam_member.cloud_storage,
  ]
}
