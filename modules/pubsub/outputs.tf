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
output "name" {
  description = "The name of the created Pub/Sub topic."
  value       = google_pubsub_topic.default.name
}

output "id" {
  description = "The full ID (self-link) of the created Pub/Sub topic."
  value       = google_pubsub_topic.default.id # This typically provides the full resource path/self-link
}

output "topic_id_static" {
  description = "The statically constructed topic ID/self-link based on project_id and name."
  value       = local.topic_id_static
}

output "schema" {
  description = "Schema resource."
  value       = try(google_pubsub_schema.default[0], null)
}

output "schema_id" {
  description = "Schema resource id."
  value       = try(google_pubsub_schema.default[0].id, null)
}

output "subscription_id" {
  description = "Subscription ids."
  value = {
    for k, v in google_pubsub_subscription.default : k => v.id
  }
}

output "subscriptions" {
  description = "Subscription resources."
  value       = google_pubsub_subscription.default
}

output "topic" {
  description = "Topic resource."
  value       = google_pubsub_topic.default
}

