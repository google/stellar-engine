/**
 * Copyright 2024 Google LLC
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

variable "artifact_registry_repo_id" {
  description = "Name/ID for the Artifact Registry YUM repository."
  type        = string
  default     = "acas-rpms"
}

variable "automation" {
  description = "Automation resources created by the bootstrap stage. Used to write ACAS outputs to the GCS outputs bucket for downstream consumption."
  type = object({
    outputs_bucket = string
  })
}

variable "base_image" {
  description = "The base image to use as the foundation for Golden Images. Specify as 'projects/PROJECT/global/images/IMAGE' or 'projects/PROJECT/global/images/family/FAMILY'."
  type        = string
  default     = "projects/rhel-cloud/global/images/family/rhel-8"
}

variable "build_sc_image" {
  description = "Whether to trigger the Cloud Build job for the SecurityCenter Golden Image."
  type        = bool
  default     = false
}

variable "build_scanner_image" {
  description = "Whether to trigger the Cloud Build job for the Nessus Scanner Golden Image."
  type        = bool
  default     = true
}

variable "hub_project_id" {
  description = "The GCP project ID that hosts the Shared VPC network."
  type        = string
}

variable "kms_deletion_policy" {
  description = "Deletion policy for the ACAS KMS key. Can be ABANDON, PREVENT_DESTROY, or DEFAULT."
  type        = string
  default     = "ABANDON"
}

variable "network" {
  description = "Self-link of the VPC network to use for the image builder VM."
  type        = string
}

variable "prefix" {
  description = "Prefix applied to resource names for org-level naming consistency. Set to null to disable prefixing."
  type        = string
  default     = null
  validation {
    condition     = var.prefix != ""
    error_message = "Prefix cannot be empty, use null instead."
  }
}

variable "region" {
  description = "GCP region for regional resources (e.g., Artifact Registry repository)."
  type        = string
  default     = "us-east4"
}

variable "shared_services_project_id" {
  description = "The GCP project ID where the image factory resources will be created."
  type        = string
}

variable "sc_image_family" {
  description = "Image family name for the SecurityCenter Golden Image."
  type        = string
  default     = "acas-sc-golden"
}

variable "sc_rpm_filename" {
  description = "Filename of the SecurityCenter RPM as uploaded to Artifact Registry (e.g., SecurityCenter-6.8.0-el8.x86_64.rpm)."
  type        = string
  default     = null
}

variable "scanner_image_family" {
  description = "Image family name for the Nessus Scanner Golden Image."
  type        = string
  default     = "acas-scanner-golden"
}

variable "scanner_rpm_filename" {
  description = "Filename of the Nessus Scanner RPM as uploaded to Artifact Registry (e.g., Nessus-10.12.0-el8.x86_64.rpm)."
  type        = string
  default     = null
}

variable "subnetwork" {
  description = "Self-link of the subnetwork to use for the image builder VM."
  type        = string
}

variable "zone" {
  description = "GCP zone where the image builder VM will run."
  type        = string
  default     = "us-east4-a"
}
