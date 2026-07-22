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
output "artifact_registry_id" {
  description = "Artifact Registry repository resource ID."
  value       = google_artifact_registry_repository.acas_rpms.id
}

output "artifact_registry_repo_id" {
  description = "Name/ID for the Artifact Registry YUM repository."
  value       = var.artifact_registry_repo_id
}

output "artifact_registry_repository" {
  description = "The full Artifact Registry repository URI."
  value       = "${var.region}-yum.pkg.dev/${var.shared_services_project_id}/${var.artifact_registry_repo_id}"
}

output "base_image" {
  description = "The base image to use as the foundation for Golden Images."
  value       = var.base_image
}

output "hub_project_id" {
  description = "Project ID that hosts the Shared VPC network."
  value       = var.hub_project_id
}

output "kms_key_id" {
  description = "ID for the dynamically created KMS key."
  value       = google_kms_crypto_key.acas.id
}

output "shared_services_project_id" {
  description = "GCP project ID where the image factory resources will be created."
  value       = var.shared_services_project_id
}

output "region" {
  description = "GCP region for regional resources (e.g., Artifact Registry repository)."
  value       = var.region
}

output "repository_id" {
  description = "ID for the created Artifact Registry repository."
  value       = google_artifact_registry_repository.acas_rpms.repository_id
}

output "sc_golden_image_family" {
  description = "Compute Image family for the SecurityCenter Golden Image."
  value       = "projects/${var.shared_services_project_id}/global/images/family/${var.sc_image_family}"
}

output "sc_image_family" {
  description = "Compute Image family for the SecurityCenter Golden Image."
  value       = var.sc_image_family
}

output "scanner_golden_image_family" {
  description = "Compute Image family for the Nessus Scanner Golden Image."
  value       = "projects/${var.shared_services_project_id}/global/images/family/${var.scanner_image_family}"
}

output "scanner_image_family" {
  description = "Compute Image family for the Nessus Scanner Golden Image."
  value       = var.scanner_image_family
}

output "subnetwork" {
  description = "VPC subnetwork to use for the image builder VM."
  value       = var.subnetwork
}

output "zone" {
  description = "GCP zone where the image builder VM will run."
  value       = var.zone
}