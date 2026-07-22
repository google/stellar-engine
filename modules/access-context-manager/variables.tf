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

variable "access_levels" {
  description = "List of access levels to create. Each access level is a map containing 'name', 'description', and 'conditions'."
  type = list(object({
    name        = string
    description = string
    conditions = list(object({
      ip_subnetworks = list(string)
      members        = list(string)
      negate         = bool
      device_policy = object({
        require_screen_lock = bool
      })
      regions = list(string)
    }))
  }))
}
variable "access_policy_title" {
  description = "The title for the Access Context Manager policy."
  type        = string
}

variable "domain" {
  description = "Domain for ACM."
  type        = string
}

variable "organization_id" {
  description = "The organization ID."
  type        = string
}

variable "project_id" {
  description = "The project ID where the Access Context Manager resources will be created."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "service_perimeters" {
  description = "List of service perimeters to create. Each service perimeter is a map containing 'name', 'description', 'status', and 'resources'."
  type = list(object({
    name        = string
    description = string
    status = object({
      restricted_services = list(string)
      resources           = list(string)
    })
  }))
}
