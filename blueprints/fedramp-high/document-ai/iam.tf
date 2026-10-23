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

resource "google_service_account" "workflow_sa" {
  project      = var.main_project_id
  account_id   = "docai-workflow-sa"
  display_name = "Workflows Service Account."
}

resource "google_project_iam_member" "workflow_sa_roles" {
  for_each = toset([
    "roles/workflows.invoker",
    "roles/logging.logWriter",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/documentai.apiUser",
  ])
  project = var.main_project_id
  role    = each.value
  member  = google_service_account.workflow_sa.member
}

resource "google_kms_crypto_key_iam_member" "service_agents_kms" {
  for_each = toset([
    "serviceAccount:service-${data.google_project.project.number}@gcp-sa-prod-dai-core.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.project.number}@gcp-sa-workflows.iam.gserviceaccount.com",
  ])
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
  depends_on    = [google_project_service.documentai]
}