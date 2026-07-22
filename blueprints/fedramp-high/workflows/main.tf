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

# Enable the API
resource "google_project_service" "workflows_api" {
  project            = var.main_project_id
  service            = "workflows.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service_identity" "workflows_si" {
  provider = google-beta
  project  = var.main_project_id
  service  = "workflows.googleapis.com"

  depends_on = [google_project_service.workflows_api]
}

resource "google_service_account" "workflow_sa" {
  account_id   = "workflows-sa"
  display_name = "Workflows Service Account."

  depends_on = [google_project_service.workflows_api]
}

module "workflows" {
  source              = "../../../modules/workflows"
  project             = var.main_project_id
  name                = var.name
  region              = var.region
  description         = var.description
  logging_level       = var.logging_level
  env_vars            = var.env_vars
  file                = var.file
  service_account     = google_service_account.workflow_sa.email
  deletion_protection = var.deletion_protection

  iam = {
    "roles/workflows.invoker"                 = [google_service_account.workflow_sa.member],
    "roles/logging.logWriter"                 = [google_service_account.workflow_sa.member],
    "roles/serviceusage.serviceUsageConsumer" = [google_service_account.workflow_sa.member],
  }
  depends_on = [
    google_project_service.workflows_api,
    google_project_service_identity.workflows_si,
    google_service_account.workflow_sa,
  ]
}