# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

variable "deletion_protection" {
  description = "Deletion protection."
  type        = bool
  default     = true
}

variable "file" {
  description = "File path of the yaml instructions for the workflow."
  type        = string
  default     = "code/example.yaml"
}

variable "main_project_id" {
  description = "The Google Project ID."
  type        = string
}

variable "name" {
  description = "Name of the Document AI processor."
  type        = string
}

variable "processor_kms_key_name" {
  description = "Cloud KMS CryptoKey resource ID in the us multi-region for Document AI processor encryption."
  type        = string
  validation {
    condition = can(regex(
      "^projects/[^/]+/locations/us/keyRings/[^/]+/cryptoKeys/[A-Za-z0-9_-]+$",
      var.processor_kms_key_name
    ))
    error_message = "processor_kms_key_name must be a Cloud KMS CryptoKey in locations/us (projects/../locations/us/keyRings/../cryptoKeys/..)."
  }
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
}

variable "regional_kms_key_name" {
  description = "Cloud KMS CryptoKey resource ID in var.region for Cloud Storage bucket and Workflows encryption."
  type        = string
  validation {
    condition = (
      can(regex(
        "^projects/[^/]+/locations/[^/]+/keyRings/[^/]+/cryptoKeys/[A-Za-z0-9_-]+$",
        var.regional_kms_key_name
      )) &&
      try(split("/", var.regional_kms_key_name)[3], "") == var.region
    )
    error_message = "regional_kms_key_name must be a Cloud KMS CryptoKey in var.region (projects/../locations/<region>/keyRings/../cryptoKeys/..)."
  }
}

variable "type" {
  description = "Type of Document AI model."
  type        = string
  default     = "OCR_PROCESSOR"
}
