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

data "google_project" "current" {}

locals {
  # Determine the KMS key region: use kms_key_location if provided, otherwise default to the workflow's region
  kms_key_region = var.kms_key_location == null ? var.region : var.kms_key_location
  # Construct the full KMS key self-link using the component variables and determined region
  kms_key_self_link_calculated = "projects/${var.core_project_id}/locations/${local.kms_key_region}/keyRings/${var.kms_keyring_name}/cryptoKeys/${var.kms_key_name}"
}

# Enable the API
resource "google_project_service" "workflows_api" {
  project            = var.main_project_id
  service            = "workflows.googleapis.com"
  disable_on_destroy = false
}

# The Google-managed service identity for Workflows.
# This is usually needed for the Workflows service to interact with other GCP services,
# including KMS for CMEK.
resource "google_project_service_identity" "workflows_si" {
  provider = google-beta
  project  = var.main_project_id
  service  = "workflows.googleapis.com"

  depends_on = [google_project_service.workflows_api]
}

# Custom Service Account for the Workflow execution.
resource "google_service_account" "workflow_sa" {
  account_id   = var.workflow_service_account_id
  display_name = "Workflows Service Account."
  project      = var.main_project_id

  depends_on = [google_project_service.workflows_api]
}

# Grant the Workflows Service Agent permissions on the KMS key for CMEK
# This is crucial for resolving the cyclical dependency.
# The Workflows Service Agent needs this role to use the CMEK key.
resource "google_kms_crypto_key_iam_member" "workflows_agent_kms_access" {
  crypto_key_id = local.kms_key_self_link_calculated # Using the calculated local
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  # The Workflows service agent is typically in the format:
  # service-${project_number}@gcp-sa-workflows.iam.gserviceaccount.com
  member = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-workflows.iam.gserviceaccount.com"

  depends_on = [
    google_project_service.workflows_api,
    google_project_service_identity.workflows_si,
  ]
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
  kms_key_self_link   = local.kms_key_self_link_calculated

  iam = {
    # It's good practice to grant these roles to the custom SA.
    # roles/workflows.invoker is for invoking the workflow
    "roles/workflows.invoker" = [google_service_account.workflow_sa.member],
    # roles/logging.logWriter is for writing logs to Cloud Logging
    "roles/logging.logWriter" = [google_service_account.workflow_sa.member],
    # roles/serviceusage.serviceUsageConsumer if the SA needs to enable APIs (less common for a workflow SA)
    "roles/serviceusage.serviceUsageConsumer" = [google_service_account.workflow_sa.member],
  }
  depends_on = [
    google_project_service.workflows_api,
    google_project_service_identity.workflows_si,
    google_service_account.workflow_sa,
    google_kms_crypto_key_iam_member.workflows_agent_kms_access,
  ]
}

