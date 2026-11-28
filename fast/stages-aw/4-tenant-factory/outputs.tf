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

# tfdoc:file:description Stage outputs for provisioned tenant resources.

output "tenant_folders" {
  description = "Map of environment/tenant keys to tenant folder IDs."
  value       = module.project-factory.folder_ids
}

output "tenant_project_numbers" {
  description = "Map of project keys to created tenant project numbers."
  value = {
    for k, v in module.tenant-projects : k => v.number
  }
}

output "tenant_projects" {
  description = "Map of project keys to created tenant project IDs."
  value = {
    for k, v in module.tenant-projects : k => v.project_id
  }
}

output "tenant_service_accounts" {
  description = "Map of tenant automation and workload service accounts."
  value = merge(
    module.project-factory.service_accounts,
    {
      for k, v in module.tenant-service-accounts : k => {
        email     = v.email
        iam_email = v.iam_email
        id        = v.id
      }
    }
  )
}

output "tenant_state_buckets" {
  description = "Map of tenant automation state bucket keys to names."
  value       = module.project-factory.storage_buckets
}
