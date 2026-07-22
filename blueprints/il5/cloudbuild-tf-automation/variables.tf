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
variable "cloud_build_core_roles" {
  description = "A list of roles for the Cloud Build SA, needed to run the build process."
  type        = list(string)
  default = [
    "roles/cloudbuild.builds.builder",
    "roles/storage.admin"
  ]
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "locations" {
  description = "Optional locations for GCS, BigQuery, and logging buckets created here."
  type = object({
    gcs = optional(string, "US")
    kms = optional(string, "US")
  })
  nullable = false
  default  = {}
}

variable "main_project_id" {
  description = "Main project ID."
  type        = string
}

variable "prefix" {
  description = "Prefix used for resources that need unique names. Use 7 characters or less."
  type        = string
  validation {
    condition     = try(length(var.prefix), 0) <= 7
    error_message = "Use a maximum of 7 characters for prefix."
  }
}

variable "services" {
  description = "Cloud services to enable within the project."
  type        = set(string)
}

variable "terraform_apply_roles" {
  description = "A list of project-level admin roles for the service account to run Terraform apply."
  type        = list(string)
  default = [
    "roles/dns.admin",
    "roles/cloudkms.admin",
    "roles/compute.admin",
    "roles/compute.networkAdmin",
    "roles/container.admin",
    "roles/gkehub.admin",
    "roles/storage.admin"
  ]
}
