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
variable "entitlements" {
  description = "PAM entitlements configuration."
  type = map(object({
    location                        = optional(string, "global")
    max_request_duration_hours      = optional(number, 1)
    parent_type                     = optional(string, "organization") # organization, folder, project
    parent_id                       = string
    grant_service_agent_permissions = optional(bool, true)
    requesters                      = list(string)
    approvers                       = optional(list(string), [])
    notification_recipients = optional(object({
      approval     = optional(list(string), [])
      pending      = optional(list(string), [])
      availability = optional(list(string), [])
    }), {})
    role_bindings = list(object({
      role                 = string
      condition_expression = optional(string)
    }))
    auto_approve_entitlement       = optional(bool, false)
    require_approver_justification = optional(bool, true)
    requester_justification        = optional(bool, true)
  }))
  default = {}
}

variable "main_project_id" {
  description = "Project ID where PAM API will be enabled and service identity created."
  type        = string
}

variable "organization_id" {
  description = "Organization ID used for the PAM service agent."
  type        = string
}
