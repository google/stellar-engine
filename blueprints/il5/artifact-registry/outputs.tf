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

output "docker_registries" {
  description = "Docker registries created from the docker-registries.yaml file, with Docker Hub appended."
  value       = local.docker-registries
}

output "yum_repositories" {
  description = "Yum repositories created from the yum-repos.yaml file."
  value       = google_artifact_registry_repository.yum-repos
}
