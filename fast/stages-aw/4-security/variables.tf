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
variable "alert_email" {
  description = "Email to receive log alerts."
  type        = string
}

variable "assured_workloads" {
  description = "Configuration for Assured Workloads."
  type = object({
    regime   = optional(string)
    location = optional(string)
    folder   = optional(string)
  })
  nullable = false
  default  = {}
}

variable "automation" {
  # tfdoc:variable:source 1-assured-workload
  description = "Automation resources created by the bootstrap stage."
  type = object({
    outputs_bucket = string
  })
}

variable "billing_account" {
  # tfdoc:variable:source 1-assured-workload
  description = "Billing account id. If billing account is not part of the same org set `is_org_level` to false."
  type = object({
    id           = string
    is_org_level = optional(bool, true)
  })
  validation {
    condition     = var.billing_account.is_org_level != null
    error_message = "Invalid `null` value for `billing_account.is_org_level`."
  }
}

variable "essential_contacts" {
  description = "Email used for essential contacts, unset if null."
  type        = string
  default     = null
}

variable "factories_config" {
  description = "Paths to folders that enable factory functionality."
  type = object({
    vpc_sc = optional(object({
      access_levels       = optional(string, "data/vpc-sc/access-levels")
      egress_policies     = optional(string, "data/vpc-sc/egress-policies")
      ingress_policies    = optional(string, "data/vpc-sc/ingress-policies")
      restricted_services = optional(string, "data/vpc-sc/restricted-services.yaml")
    }), {})
  })
  nullable = false
  default  = {}
}

variable "folder_ids" {
  # tfdoc:variable:source 2-resman
  description = "Folder name => id mappings, the 'security' folder name must exist."
  type = object({
    security = string
  })
}

variable "kms_keys" {
  description = "KMS keys to create, keyed by name."
  type = map(object({
    rotation_period = optional(string, "7776000s") # CIS Compliance Benchmark 1.10
    labels          = optional(map(string))
    locations = optional(list(string), [
      "us",
      "us-central2",
      "us-east5-locations",
      "us-central1-b",
      "us-central2-d",
      "us-west1-c",
      "us-east4-a",
      "us-west1",
      "us-central2-b",
      "us-south1-locations",
      "us-south1-b",
      "us-west2-c",
      "us-west1-b",
      "us-central2-locations",
      "us-east4-d",
      "us-east4-locations",
      "us-east5-c",
      "us-central2-a",
      "us-west1-locations",
      "us-west4",
      "us-west3-b",
      "us-west1-a",
      "us-west4-a",
      "us-west2",
      "us-east4-c",
      "us-west2-b",
      "us-south1-a",
      "us-east5-a",
      "nam4",
      "us-east4-a",
      "us-west2-locations",
      "us-central1-f",
      "us-south1",
      "us-west4-c",
      "us-west2-a",
      "us-west3",
      "us-west4-b",
      "us-central1",
      "us-west3-c",
      "us-central1-c",
      "us-south1-c",
      "us-east4-locations",
      "us-east4",
      "us-east4-b",
      "us-central1-a",
      "us-central2-c",
      "us-east5-b",
      "us-central1-locations",
      "us-west4-locations",
      "us-east5",
      "us-west3-locations",
      "us-west3-a",
      "us-east4",
      "us-east4-b",
      "us-east4-c",
    ])
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
  default  = {}
  nullable = false
}

variable "logging" {
  # tfdoc:variable:source 1-assured-workload
  description = "Log writer identities for organization / folders."
  type = object({
    project_number    = string
    writer_identities = map(string)
  })
  default = null
}

variable "organization" {
  # tfdoc:variable:source 1-assured-workload
  description = "Organization details."
  type = object({
    domain      = string
    id          = number
    customer_id = string
  })
}

variable "outputs_location" {
  description = "Path where providers, tfvars files, and lists for the following stages are written. Leave empty to disable."
  type        = string
  default     = null
}

variable "prefix" {
  # tfdoc:variable:source 1-assured-workload
  description = "Prefix used for resources that need unique names. Use 9 characters or less."
  type        = string
  validation {
    condition     = try(length(var.prefix), 0) <= 10
    error_message = "Use a maximum of 9 characters for prefix."
  }
}

variable "regime_mapping" {
  description = "Mapping of compliance regime names to short codes."
  type        = map(string)
}

variable "service_accounts" {
  # tfdoc:variable:source 2-resman
  description = "Automation service accounts that can assign the encrypt/decrypt roles on keys."
  type = object({
    data-platform-dev    = string
    data-platform-prod   = string
    project-factory-dev  = string
    project-factory-prod = string
  })
}

variable "vpc_sc" {
  description = "VPC SC configuration."
  type = object({
    access_levels    = optional(map(any), {})
    egress_policies  = optional(map(any), {})
    ingress_policies = optional(map(any), {})
    perimeter_default = optional(object({
      access_levels    = optional(list(string), [])
      dry_run          = optional(bool, false)
      egress_policies  = optional(list(string), [])
      ingress_policies = optional(list(string), [])
      resources        = optional(list(string), [])
    }))
    resource_discovery = optional(object({
      enabled          = optional(bool, true)
      ignore_folders   = optional(list(string), [])
      ignore_projects  = optional(list(string), [])
      include_projects = optional(list(string), [])
    }), {})
  })
  default  = {}
  nullable = false
}