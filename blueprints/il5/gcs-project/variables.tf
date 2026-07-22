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
# tflint-ignore: terraform_unused_declarations
variable "autoclass" {
  description = "Enable autoclass to automatically transition objects to appropriate storage classes based on their access pattern. If set to true, storage_class must be set to STANDARD. When set to true, All objects added to the bucket begin in Standard storage, even if a different storage class is specified in the request."
  type        = bool
  default     = true
}

variable "bucket-name" {
  description = "Bucket name suffix."
  type        = string
}

variable "core_project_id" {
  description = "Core Project ID."
  type        = string
}

variable "kms_key_name" {
  description = "The full self-link (projects/../locations/../cryptoKeys/..) of the existing KMS key to use for encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type        = string
}

variable "main_project_id" {
  description = "Project ID."
  type        = string
}

variable "prefix" {
  description = "Optional prefix used to generate the bucket name."
  type        = string
  default     = "string"
  validation {
    condition     = var.prefix != ""
    error_message = "Prefix cannot be empty, please use null instead."
  }
}

variable "public_access_prevention" {
  description = "This provides the ability to toggle Public Access Prevention for the GCS Storage bucket. By setting this variable to enforced, the CIS Compliance Benchmark 5.1 control is satisfied."
  type        = string
  default     = "enforced"
  validation {
    condition     = contains(["enforced", "inherited"], var.public_access_prevention)
    error_message = "public_access_prevention must be either 'enforced' or 'inherited'."
  }
}

variable "region" {
  description = "Bucket region."
  type        = string
  default     = "us-east4"
}

variable "retention_policy" {
  description = "Retention policy."
  type = object({
    is_locked        = bool
    retention_period = number
  })

  default = {
    is_locked        = false # Change to true if storing logs here for CIS Compliance Benchmark 2.3
    retention_period = 7776000
  }
}

variable "storage_class" {
  description = "Bucket storage class."
  type        = string
  default     = "STANDARD"
  validation {
    condition     = contains(["STANDARD", "MULTI_REGIONAL", "REGIONAL", "NEARLINE", "COLDLINE", "ARCHIVE"], var.storage_class)
    error_message = "Storage class must be one of STANDARD, MULTI_REGIONAL, REGIONAL, NEARLINE, COLDLINE, ARCHIVE."
  }
}

variable "uniform_bucket_level_access" {
  description = "This provides the ability to toggle Uniform Bucket Level Access for the GCS Storage bucket. By setting this variable to true, the CIS Compliance Benchmark 5.2 control is satisfied."
  type        = bool
  default     = true
}
