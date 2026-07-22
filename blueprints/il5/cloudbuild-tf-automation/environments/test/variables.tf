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

variable "project_id" {
  description = "The ID of the project where the Cloud Build service account will be created and operate."
  type        = string
}

variable "bucket_name" {
  description = "The name of the GCS bucket used for Terraform remote state."
  type        = string
}

variable "locations" {
  description = "Optional locations for GCS, BigQuery, and logging buckets created here."
  type = object({
    bq      = optional(string, "US")
    gcs     = optional(string, "US")
    logging = optional(string, "global")
    pubsub  = optional(list(string), [])
    kms     = optional(string, "US")
  })
  nullable = false
  default  = {}
}

variable "prefix" {
  description = "Prefix used for resources that need unique names. Use 7 characters or less."
  type        = string
  validation {
    condition     = try(length(var.prefix), 0) <= 7
    error_message = "Use a maximum of 7 characters for prefix."
  }
}

variable "state_bucket" {
  description = "The bucket created in the blueprint to hold project state."
  type        = string
}