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

# Enable the API service
resource "google_project_service" "documentai" {
  project = var.main_project_id
  for_each = toset([
    "documentai.googleapis.com",
    "storage.googleapis.com",
    "workflows.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_document_ai_processor" "processor" {
  project      = var.main_project_id
  location     = "us"
  display_name = var.name
  type         = var.type
  kms_key_name = var.processor_kms_key_name

  depends_on = [
    google_project_service.documentai,
    google_kms_crypto_key_iam_member.documentai_cmek,
  ]
}

#Get the latest stable version of the selected processor
resource "google_document_ai_processor_default_version" "processor" {
  processor = google_document_ai_processor.processor.id
  version   = "${google_document_ai_processor.processor.id}/processorVersions/stable"

  lifecycle {
    ignore_changes = [
      version
    ]
  }
}

moved {
  from = module.input_bucket
  to   = module.input-bucket
}

module "input-bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "doc-ai-input"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  encryption_key              = var.regional_kms_key_name

  depends_on = [
    google_project_service.documentai,
    google_kms_crypto_key_iam_member.gcs_cmek,
  ]
}

moved {
  from = module.output_bucket
  to   = module.output-bucket
}

module "output-bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "doc-ai-output"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  encryption_key              = var.regional_kms_key_name

  depends_on = [
    google_project_service.documentai,
    google_kms_crypto_key_iam_member.gcs_cmek,
  ]
}

module "workflows" {
  source              = "../../../modules/workflows"
  project             = var.main_project_id
  name                = "doc-ai-workflow"
  region              = var.region
  deletion_protection = var.deletion_protection
  description         = "Document AI example workflow."
  file                = var.file
  service_account     = google_service_account.workflow_sa.email
  kms_key_self_link   = var.regional_kms_key_name
  env_vars = {
    project_id    = var.main_project_id
    input_bucket  = module.input-bucket.url
    output_bucket = module.output-bucket.url
    processor_id  = google_document_ai_processor.processor.id
    location      = var.region
  }
  iam = {
    "roles/workflows.invoker"                 = [google_service_account.workflow_sa.member],
    "roles/logging.logWriter"                 = [google_service_account.workflow_sa.member],
    "roles/serviceusage.serviceUsageConsumer" = [google_service_account.workflow_sa.member],
    "roles/documentai.apiUser"                = [google_service_account.workflow_sa.member],
    "roles/storage.objectViewer"              = [google_service_account.workflow_sa.member],
    "roles/storage.objectCreator"             = [google_service_account.workflow_sa.member],
  }
  depends_on = [
    google_project_service.documentai,
    google_service_account.workflow_sa,
    google_kms_crypto_key_iam_member.workflows_cmek,
  ]
}