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

resource "google_cloud_scheduler_job" "job" {
  project     = var.project_id
  name        = var.name
  description = var.description
  schedule    = var.schedule

  dynamic "pubsub_target" {
    for_each = var.trigger_type == "pubsub" ? [1] : []
    content {
      topic_name = var.pubsub_target.topic_id
      data       = var.pubsub_target.data
      attributes = var.pubsub_target.attributes
    }
  }

  dynamic "http_target" {
    for_each = var.trigger_type == "http" ? [1] : []
    content {
      http_method = var.http_target.http_method
      uri         = var.http_target.uri
      body        = var.http_target.body
      headers     = var.http_target.headers
    }
  }

  dynamic "retry_config" {
    for_each = var.retry_config != null ? [1] : []
    content {
      retry_count          = var.retry_config.retry_count
      max_retry_duration   = var.retry_config.max_retry_duration
      min_backoff_duration = var.retry_config.min_backoff_duration
      max_backoff_duration = var.retry_config.max_backoff_duration
      max_doublings        = var.retry_config.max_doublings
    }
  }
}

resource "google_pubsub_topic" "topic" {
  count        = var.pubsub_target.new_topic != null ? 1 : 0
  project      = var.project_id
  name         = var.pubsub_target.new_topic.name
  kms_key_name = var.pubsub_target.new_topic.kms_key_name
}
