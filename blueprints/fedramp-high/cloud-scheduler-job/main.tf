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

data "google_project" "project" {
  project_id = var.main_project_id
}

resource "google_project_service" "cloudscheduler_api" {
  project            = var.main_project_id
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}


resource "google_kms_crypto_key_iam_binding" "pubsub" {
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  ]
}

module "pubsub_job" {
  source      = "../../../modules/cloud-scheduler"
  name        = var.name
  description = var.description
  project_id  = var.main_project_id
  schedule    = var.schedule

  retry_config = {
    retry_count = var.retry_count
  }

  trigger_type = "pubsub"
  pubsub_target = {
    data     = base64encode(var.data)
    topic_id = var.topic_id
    new_topic = {
      create       = true
      name         = var.new_topic_name
      kms_key_name = var.kms_key_name
    }
  }
  depends_on = [google_project_service.cloudscheduler_api]
}
