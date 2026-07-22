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

variable "auth_domain" {
  description = "The domain to authenticate users with when using App Engine's User API."
  type        = string
  default     = null
}

variable "database_type" {
  description = "The type of the Cloud Firestore or Cloud Datastore database associated with this application."
  type        = string
  default     = null
}

variable "feature_settings" {
  description = "A block of optional settings to configure specific App Engine features."
  type = object({
    split_health_checks = optional(bool, true)
  })

  nullable = true
  default  = {}
}

variable "iap" {
  description = "Settings for enabling Cloud Identity Aware Proxy."
  type = object({
    oauth2_client_id     = optional(string, "")
    oauth2_client_secret = optional(string, "")
  })

  nullable = true
  default  = {}
}

variable "location_id" {
  description = "Region to create your App Engine resource."
  type        = string
}

variable "project" {
  description = "Project to create your App Engine resource."
  type        = string
}

variable "serving_status" {
  description = "The serving status of the app."
  type        = string
  default     = null
}
