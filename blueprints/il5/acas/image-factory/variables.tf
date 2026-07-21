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

variable "kms_key_name" {
  description = "Name of the KMS crypto key for encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "Name of the KMS key ring used to encrypt images and Artifact Registry."
  type        = string
}

variable "kms_project_id" {
  description = "Project ID where the KMS keyring resides."
  type        = string
}

variable "network_name" {
  description = "VPC network to use for the image builder VM."
  type        = string
}

variable "network_project_id" {
  description = "Project ID that hosts the VPC network. Defaults to project_id. Set this when using a Shared VPC where the network lives in a different host project than the image factory."
  type        = string
  default     = null
}

variable "project_id" {
  description = "GCP project ID where the image factory resources will be created."
  type        = string
}

variable "region" {
  description = "GCP region for regional resources (e.g., Artifact Registry repository)."
  type        = string
  default     = "us-east4"
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

variable "subnetwork_name" {
  description = "VPC subnetwork to use for the image builder VM."
  type        = string
}

variable "zone" {
  description = "GCP zone where the image builder VM will run."
  type        = string
  default     = "us-east4-a"
}
