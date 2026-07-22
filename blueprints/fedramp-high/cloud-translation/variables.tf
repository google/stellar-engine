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

variable "output_folder" {
  description = "Name of the folder that will be created in the output bucket to store the translated text."
  type        = string
  default     = "output"
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
}

variable "src_lang" {
  description = "The source language of the text."
  type        = string
  default     = "es"
}

variable "target_lang" {
  description = "The target language to translate into."
  type        = string
  default     = "en"
}