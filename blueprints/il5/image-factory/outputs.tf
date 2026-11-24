# Copyright 2026 Google LLC
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

output "artifact_registry_repository_id" {
  description = "Resource ID of the CMEK Artifact Registry mirror."
  value       = module.builder-registry.id
}

output "builder_service_account_email" {
  description = "Email of the dedicated Cloud Build service account."
  value       = module.builder-sa.email
}

output "cloudbuild_config_object" {
  description = "Cloud Storage URI of the rendered Cloud Build YAML."
  value = format(
    "gs://%s/%s",
    module.staging-bucket.name,
    var.cloudbuild_config_object_name,
  )
  depends_on = [module.staging-bucket]
}

output "staging_bucket_name" {
  description = "Name of the CMEK Cloud Storage staging bucket."
  value       = module.staging-bucket.name
}

output "trigger_id" {
  description = "ID of the optional Cloud Build trigger, or null."
  value       = try(google_cloudbuild_trigger.default[0].trigger_id, null)
}

output "worker_pool_id" {
  description = "Resource ID of the private Cloud Build worker pool."
  value       = google_cloudbuild_worker_pool.default.id
}
