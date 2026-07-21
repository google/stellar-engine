/**
 * Copyright 2023 Google LLC
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

variable "email" {
  description = "Email address of the user."
  type        = string
  # Example default = "admin.user-anme@example.google.com"
}

variable "group_email" {
  description = "An email address that represents a Google group. For example, admins@example.com."
  type        = string
  # Example default = "admins@example.com"
}

variable "kms_key_names" {
  description = "Key names and base attributes. Set attributes to null if not needed."
  type = map(object({
    destroy_scheduled_duration    = optional(string)
    rotation_period               = optional(string, "7776000s") # CIS Compliance Benchmark 1.10
    labels                        = optional(map(string))
    purpose                       = optional(string, "ENCRYPT_DECRYPT")
    skip_initial_version_creation = optional(bool, false)
    version_template = optional(object({
      algorithm        = string
      protection_level = optional(string, "HSM")
    }))

    iam = optional(map(list(string)), {})
    iam_bindings = optional(map(object({
      members = list(string)
      role    = string
      condition = optional(object({
        expression  = string
        title       = string
        description = optional(string)
      }))
    })), {})
    iam_bindings_additive = optional(map(object({
      member = string
      role   = string
      condition = optional(object({
        expression  = string
        title       = string
        description = optional(string)
      }))
    })), {})
  }))
  default = {
    "update-the-keys-name" = {
      rotation_period            = "7776000s"
      destroy_scheduled_duration = "2592000s"
      labels = {
        "team" = "update-the-team-label-here"
      }
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
      iam = {
        "roles/cloudkms.cryptoKeyEncrypterDecrypter" = ["user:update-the-email-address-here", "group:update-group-email-address-here"]
      }
      lifecycle = {
        prevent_destroy = true
      }
    }

  }
  nullable = false
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type = object({
    location = string
    name     = string
  })
}

variable "main_project_id" {
  description = "Project ID."
  type        = string
  # Example default = project-id-123
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}
