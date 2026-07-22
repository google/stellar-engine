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

resource "google_project_service" "cloudscheduler_api" {
  project            = var.main_project_id
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

# Grant Pub/Sub service account permissions on the KMS key for CMEK of the Pub/Sub topic
resource "google_kms_crypto_key_iam_binding" "pubsub" {
  count = var.kms_key_name != null ? 1 : 0
  # This grants permission to the Pub/Sub service account to use the KMS key
  # for the *existing* Pub/Sub topic.
  crypto_key_id = var.kms_key_name # Full self-link of the existing KMS key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  ]
  # Depend on google_project_service_identity if we were creating it in this blueprint
  # but here, we just need to ensure the API is enabled.
  depends_on = [google_project_service.cloudscheduler_api] # Ensure API is enabled before IAM
}

module "pubsub_job" {
  source      = "../../../modules/cloud-scheduler"
  name        = var.name
  description = var.description
  project_id  = var.main_project_id
  schedule    = var.schedule

  retry_config = {
    retry_count = var.retry_count
    # Optional retry configurations are now part of 'var.retry_config' if passed via module
    max_backoff_duration = var.max_backoff_duration
    max_doublings        = var.max_doublings
    max_retry_duration   = var.max_retry_duration
    min_backoff_duration = var.min_backoff_duration
  }

  trigger_type = "pubsub"
  pubsub_target = {
    data     = base64encode(var.data)
    topic_id = var.topic_id # This is now the self-link of the EXISTING Pub/Sub topic
  }
  depends_on = [
    google_project_service.cloudscheduler_api,
    google_kms_crypto_key_iam_binding.pubsub, # Ensure Pub/Sub SA has KMS permission if new topic is CMEK'd
  ]
}

