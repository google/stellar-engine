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
  pubsub_data = (
    var.data == null ? null : (
      var.data_is_base64 ? var.data : base64encode(var.data)
    )
  )
  topic_project_id = regex("^projects/([^/]+)/topics/", var.topic_id)[0]
}

data "google_project" "topic" {
  project_id = local.topic_project_id
}

resource "google_project_service" "cloudscheduler_api" {
  project            = var.main_project_id
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service_identity" "cloudscheduler" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "cloudscheduler.googleapis.com"
  depends_on = [google_project_service.cloudscheduler_api]
}

# Grant the Cloud Scheduler service agent permission to publish to the target Pub/Sub topic.
resource "google_pubsub_topic_iam_member" "scheduler_publisher" {
  project    = local.topic_project_id
  topic      = var.topic_id
  role       = "roles/pubsub.publisher"
  member     = google_project_service_identity.cloudscheduler.member
  depends_on = [google_project_service_identity.cloudscheduler]
}

# Grant the topic project's Pub/Sub service agent permissions on the CMEK key.
resource "google_kms_crypto_key_iam_member" "pubsub" {
  count = var.kms_key_name != null ? 1 : 0
  # This grants permission to the Pub/Sub service account to use the KMS key
  # for the *existing* Pub/Sub topic.
  crypto_key_id = var.kms_key_name # Full self-link of the existing KMS key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.topic.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  # Depend on google_project_service_identity if we were creating it in this blueprint
  # but here, we just need to ensure the API is enabled.
  depends_on = [google_project_service.cloudscheduler_api] # Ensure API is enabled before IAM
}

moved {
  from = module.pubsub_job
  to   = module.pubsub-job
}

module "pubsub-job" {
  source      = "../../../modules/cloud-scheduler"
  name        = var.name
  description = var.description
  project_id  = var.main_project_id
  schedule    = var.schedule

  retry_config = (
    var.retry_count == null &&
    var.max_backoff_duration == null &&
    var.max_doublings == null &&
    var.max_retry_duration == null &&
    var.min_backoff_duration == null
    ) ? null : {
    retry_count = var.retry_count
    # Optional retry configurations are now part of 'var.retry_config' if passed via module
    max_backoff_duration = var.max_backoff_duration
    max_doublings        = var.max_doublings
    max_retry_duration   = var.max_retry_duration
    min_backoff_duration = var.min_backoff_duration
  }

  trigger_type = "pubsub"
  pubsub_target = {
    data     = local.pubsub_data
    topic_id = var.topic_id # This is now the self-link of the EXISTING Pub/Sub topic
  }
  depends_on = [
    google_project_service.cloudscheduler_api,
    google_kms_crypto_key_iam_member.pubsub, # Ensure Pub/Sub SA has KMS permission if new topic is CMEK'd
    google_pubsub_topic_iam_member.scheduler_publisher,
  ]
}

