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

variable "endpoint_name" {
  description = "Name for endpoint."
  type        = string
}

variable "iap_user_email" {
  description = "User or group email for IAP access."
  type        = string
}

variable "oauth_client_id" {
  description = "OAuth Client ID for IAP."
  type        = string
}

variable "oauth_client_secret" {
  description = "OAuth Client Secret for IAP."
  type        = string
}

variable "organization_id" {
  description = "GCP Organization ID."
  type        = string
}

variable "policy_title" {
  description = "Title for the Access Context Manager Policy."
  type        = string
  default     = "BeyondCorp Policy"
}

variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "Region."
  type        = string
}
