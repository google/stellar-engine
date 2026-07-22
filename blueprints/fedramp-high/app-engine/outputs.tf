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

output "app_id" {
  value       = module.app-engine.app_id
  description = "Identifier of the app."
}

output "code_bucket" {
  value       = module.app-engine.code_bucket
  description = "GCS bucket where the app code is stored."
}

output "default_bucket" {
  value       = module.app-engine.default_bucket
  description = "GCS bucket where the app content is stored."
}

output "default_hostname" {
  value       = module.app-engine.default_hostname
  description = "Default hostname for the app."
}

output "gcr_domain" {
  value       = module.app-engine.gcr_domain
  description = "GCR domain used for storing managed Docker images."
}

output "id" {
  description = "An identifier for the resource."
  value       = module.app-engine.id
}

output "name" {
  value       = module.app-engine.name
  description = "Unique name of the app."
}
