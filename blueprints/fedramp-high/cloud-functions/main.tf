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
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "logging.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "binaryauthorization.googleapis.com",
  ])

  project            = var.main_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_iam_member" "cloud_build" {
  project = var.main_project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = module.service-account-runner.iam_email
}

resource "google_project_iam_member" "cloud_invoker" {
  project = var.main_project_id
  role    = "roles/run.invoker"
  member  = module.service-account-runner.iam_email
}

resource "google_kms_crypto_key_iam_binding" "cloud_storage" {
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.current.number}@gcf-admin-robot.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.current.number}@gcp-sa-artifactregistry.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.current.number}@serverless-robot-prod.iam.gserviceaccount.com"
  ]
}

resource "google_project_iam_member" "artifactregistry_createOnPushWriter" {
  project = var.main_project_id
  role    = "roles/artifactregistry.createOnPushWriter"
  member  = module.service-account-runner.iam_email
}

resource "google_project_iam_member" "logging_logWriter" {
  project = var.main_project_id
  role    = "roles/logging.logWriter"
  member  = module.service-account-runner.iam_email
}

resource "google_project_iam_member" "storage_objectUser" {
  project = var.main_project_id
  role    = "roles/storage.objectUser"
  member  = module.service-account-runner.iam_email
}

resource "null_resource" "cloud_function_deploy" {
  depends_on = [module.bucket, module.registry-docker]
  triggers = {
    project_id       = var.main_project_id
    region           = var.region
    function_name    = var.function_name
    runtime          = var.function_runtime
    entry_point      = var.function_entry_point
    memory           = var.function_memory_mb
    timeout          = var.function_timeout_seconds
    source_code_hash = sha256(join("", [for f in fileset("./src-code", "**") : file("./src-code/${f}")]))
  }
  provisioner "local-exec" {
    command = <<EOT
      gcloud functions deploy "${var.function_name}" \
        --project="${var.main_project_id}" \
        --region="${var.region}" \
        --runtime="${var.function_runtime}" \
        --trigger-http \
        --source="./src-code" \
        --entry-point="${var.function_entry_point}" \
        --memory="${var.function_memory_mb}MB" \
        --timeout="${var.function_timeout_seconds}s" \
        --ingress-settings="internal-and-gclb" \
        --binary-authorization default \
        --docker-repository="${module.registry-docker.id}" \
        --kms-key="${var.kms_key_name}" \
        --service-account="${module.service-account-runner.email}"
    EOT
  }
}


module "bucket" {
  source         = "../../../modules/gcs"
  project_id     = var.main_project_id
  name           = var.bucket_name
  location       = var.region
  encryption_key = var.kms_key_name
  iam = {
    "roles/storage.objectUser" = [
      module.service-account-runner.iam_email,
      "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com",
      "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
    ]
  }
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
  depends_on = [google_kms_crypto_key_iam_binding.cloud_storage]
}
