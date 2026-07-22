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

variable "deletion_protection" {
  description = "Deletion proteciton."
  type        = bool
  default     = true
}

variable "description" {
  description = "Description of the workflow."
  type        = string
  default     = null
}

variable "env_vars" {
  description = "Environment variables made available to your workflow execution."
  type        = map(string)
  default     = null
}

variable "file" {
  description = "File path to the instructions for the workflow."
  type        = string
}

variable "iam" {
  description = "Keyring IAM bindings in {ROLE => [MEMBERS]} format."
  type        = map(list(string))
  default     = {}
  nullable    = false
}

variable "logging_level" {
  description = "Logging level of workflow executions."
  type        = string
  default     = "LOG_ERRORS_ONLY"
}

variable "name" {
  description = "Name of the workflow."
  type        = string
}

variable "project" {
  description = "The Google Project ID."
  type        = string
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
}

variable "service_account" {
  description = "Service account for Workflows."
  type        = string
}

# In ../../../modules/workflows/variables.tf

variable "kms_key_self_link" {
  description = "The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for Workflow encryption (CMEK)."
  type        = string
}
