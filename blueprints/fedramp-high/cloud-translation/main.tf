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
resource "google_project_service" "translate" {
  project = var.main_project_id
  for_each = toset([
    "translate.googleapis.com",
    "workflows.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

data "google_project" "project" {
  project_id = var.main_project_id
}

resource "google_kms_crypto_key_iam_member" "service_agents_kms" {
  for_each = var.kms_key_self_link != null ? toset([
    "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.project.number}@gcp-sa-workflows.iam.gserviceaccount.com",
  ]) : toset([])
  crypto_key_id = var.kms_key_self_link
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
  depends_on    = [google_project_service.translate]
}

moved {
  from = module.input_bucket
  to   = module.input-bucket
}

module "input-bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "translate-input"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  encryption_key              = var.kms_key_self_link
  iam = {
    "roles/storage.objectViewer" = [google_service_account.workflow_sa.member]
  }
  depends_on = [google_kms_crypto_key_iam_member.service_agents_kms]
}

moved {
  from = module.output_bucket
  to   = module.output-bucket
}

module "output-bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "translate-output"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  encryption_key              = var.kms_key_self_link
  iam = {
    "roles/storage.objectViewer"  = [google_service_account.workflow_sa.member]
    "roles/storage.objectCreator" = [google_service_account.workflow_sa.member]
  }
  depends_on = [google_kms_crypto_key_iam_member.service_agents_kms]
}

resource "google_service_account" "workflow_sa" {
  project      = var.main_project_id
  account_id   = "translate-workflow-sa"
  display_name = "Workflows Service Account."
}

resource "google_project_iam_member" "workflow_sa_roles" {
  for_each = toset([
    "roles/workflows.invoker",
    "roles/logging.logWriter",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/cloudtranslate.user",
  ])
  project = var.main_project_id
  role    = each.value
  member  = google_service_account.workflow_sa.member
}

module "workflows" {
  source              = "../../../modules/workflows"
  project             = var.main_project_id
  name                = "translate-workflow"
  region              = var.region
  deletion_protection = var.deletion_protection
  description         = "Translation LLM example workflow."
  file                = var.file
  kms_key_self_link   = var.kms_key_self_link
  service_account     = google_service_account.workflow_sa.email
  env_vars = {
    input_bucket  = "${module.input-bucket.url}/*.txt"
    output_bucket = "${module.output-bucket.url}/${var.output_folder}/"
    src_lang      = var.src_lang
    target_lang   = var.target_lang
    parent        = "projects/${var.main_project_id}/locations/us-central1"
  }
  depends_on = [
    google_project_service.translate,
    google_service_account.workflow_sa,
    google_project_iam_member.workflow_sa_roles,
    google_kms_crypto_key_iam_member.service_agents_kms,
  ]
}