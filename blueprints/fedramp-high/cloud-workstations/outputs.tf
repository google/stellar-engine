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

output "workstation_cluster" {
  description = "The cluster that was created to host the workstations."
  value       = module.workstations.id
}

output "workstation_config" {
  description = "The workstation config that is used to create workstation instances."
  value       = module.workstations.workstation_configs
}

output "workstation_key_sa" {
  description = "The service account that was created to use the KMS key."
  value       = google_service_account.workstation_config_key_user
}

output "workstations" {
  description = "The created workstation instances."
  value       = module.workstations.workstations
}