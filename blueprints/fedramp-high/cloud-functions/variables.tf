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

variable "artifact_registry_name" {
  description = "Name of the Artifact Registry being deployed."
  type        = string
  default     = "cloud-func-reg"
}

variable "bucket_name" {
  description = "The name of the Cloud Storage bucket where the Cloud Function source code is stored."
  type        = string
}

variable "function_entry_point" {
  description = "The entry point for the Cloud Function."
  type        = string
  default     = "helloHttp"
}

variable "function_memory_mb" {
  description = "The amount of memory (in MB) allocated for the Cloud Function."
  type        = number
  default     = 256
}

variable "function_name" {
  description = "The name of the Cloud Function."
  type        = string
}

variable "function_runtime" {
  description = "The runtime to use for the Cloud Function (e.g., nodejs18, python39, etc.)."
  type        = string
  default     = "nodejs20"
}

variable "function_timeout_seconds" {
  description = "The maximum amount of time (in seconds) the Cloud Function is allowed to run."
  type        = number
  default     = 60
}

variable "kms_key_name" {
  description = "Path to the kms key."
  type        = string
}

variable "main_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region where the Cloud Function will be deployed."
  type        = string
}
