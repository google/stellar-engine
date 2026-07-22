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
output "notebook" {
  description = "Vertex AI notebook ids."
  value = merge(
    { for k, v in resource.google_notebooks_runtime.runtime : k => v.id },
    { for k, v in resource.google_workbench_instance.playground : k => v.id }
  )
}

output "project_id" {
  description = "Project ID."
  value       = module.project.project_id
}
