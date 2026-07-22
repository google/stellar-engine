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

variable "composer_env_name" {
  description = "Name of the Composer environment."
  type        = string
}

variable "composer_version" {
  description = "Cloud composer version."
  type        = string
  default     = "composer-3-airflow-2"
}

variable "main_project_id" {
  description = "Main project ID."
  type        = string
}

variable "network_name" {
  description = "Full path to VPC."
  type        = string
}

variable "network_project_id" {
  description = "The ID of the landing zone project where the VPC is."
  type        = string
}

variable "region" {
  description = "Google Cloud Region."
  type        = string
  default     = "us-east4"
}

variable "sa_account_id" {
  description = "Service account id."
  default     = "composer-env-account"
  type        = string
}

variable "sa_display_name" {
  description = "Service account display name."
  default     = "Service Account for Composer Environment"
  type        = string
}

variable "service_agent_version" {
  description = "Composer Service Agent version. This must correspond to Composer version."
  type        = string
  default     = "roles/composer.ServiceAgentV2Ext"
}

variable "subnetwork_name" {
  description = "The name of the existing subnetwork to use within the specified VPC network and region."
  type        = string
}