/**
 * Copyright 2024 Google LLC
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

variable "assured_workloads" {
  description = "Configuration for Assured Workloads."
  type = object({
    regime   = string
    location = string
  })
  nullable = false
  default = {
    regime   = "IL5"
    location = "US"
  }
}

variable "billing_account" {
  description = "Billing account id. If billing account is not part of the same org set `is_org_level` to `false`. To disable handling of billing IAM roles set `no_iam` to `true`."
  type = object({
    id           = string
    is_org_level = optional(bool, true)
    no_iam       = optional(bool, false)
  })
  nullable = false
}

variable "bootstrap_project" {
  description = "Bootstrap project ID."
  type        = string
}

variable "custom_roles" {
  description = "Map of role names => list of permissions to additionally create at the organization level."
  type        = map(list(string))
  nullable    = false
  default     = {}
}

variable "factories_config" {
  description = "Configuration for the resource factories or external data."
  type = object({
    checklist_data    = optional(string)
    checklist_org_iam = optional(string)
    custom_roles      = optional(string, "data/custom-roles")
    org_policy        = optional(string, "data/org-policies")
  })
  nullable = false
  default  = {}
}

variable "gcp_billing_admins_group" {
  description = "GCP Billing Admins group name."
  type        = string
  default     = "gcp-billing-admins"
}

variable "gcp_devops_group" {
  description = "GCP DevOps group name."
  type        = string
  default     = "gcp-devops"
}

variable "gcp_organization_admins_group" {
  description = "GCP Organization Admins group name."
  type        = string
  default     = "gcp-organization-admins"
}

variable "gcp_security_admins_group" {
  description = "GCP Security Admins group name."
  type        = string
  default     = "gcp-security-admins"
}

variable "gcp_support_group" {
  description = "GCP Support group name."
  type        = string
  default     = null
}

variable "gcp_vpc_network_admins_group" {
  description = "GCP VPC Network Admins group name."
  type        = string
  default     = "gcp-vpc-network-admins"
}

variable "groups" {
  # https://cloud.google.com/docs/enterprise/setup-checklist
  description = "Group names or IAM-format principals to grant organization-level permissions. If just the name is provided, the 'group:' principal and organization domain are interpolated."
  type = object({
    gcp-billing-admins      = optional(string)
    gcp-devops              = optional(string)
    gcp-vpc-network-admins  = optional(string)
    gcp-organization-admins = optional(string)
    gcp-security-admins     = optional(string)
    # aliased to gcp-devops as the checklist does not create it
    gcp-support = optional(string)
  })
  nullable = false
  default  = {}
}

variable "iam" {
  description = "Organization-level custom IAM settings in role => [principal] format."
  type        = map(list(string))
  nullable    = false
  default     = {}
}

variable "iam_bindings_additive" {
  description = "Organization-level custom additive IAM bindings. Keys are arbitrary."
  type = map(object({
    member = string
    role   = string
    condition = optional(object({
      expression  = string
      title       = string
      description = optional(string)
    }))
  }))
  nullable = false
  default  = {}
}

variable "iam_by_principals" {
  description = "Authoritative IAM binding in {PRINCIPAL => [ROLES]} format. Principals need to be statically defined to avoid cycle errors. Merged internally with the `iam` variable."
  type        = map(list(string))
  default     = {}
  nullable    = false
}

variable "locations" {
  description = "Optional locations for GCS, BigQuery, and logging buckets created here."
  type = object({
    bq      = optional(string, "US")
    gcs     = optional(list(string), ["US"])
    logging = optional(list(string), ["global"])
    pubsub  = optional(list(string), [])
    kms     = optional(list(string), ["US"])
  })
  nullable = false
  default  = {}
}

variable "logging_kms_key" {
  description = "value of the KMS key used for logging."
  type        = string
  default     = null
}

variable "org_policies_config" {
  description = "Organization policies customization."
  type = object({
    constraints = optional(object({
      allowed_policy_member_domains = optional(list(string), [])
      allowed_access_boundaries     = optional(list(string), [])
    }), {})
    import_defaults = optional(bool, false)
    tag_name        = optional(string, "org-policies")
    tag_values = optional(map(object({
      description = optional(string, "Managed by the Terraform organization module.")
      iam         = optional(map(list(string)), {})
      id          = optional(string)
    })), {})
  })
  default = {}
}

variable "organization" {
  description = "Organization details."
  type = object({
    id          = number
    domain      = optional(string)
    customer_id = optional(string)
  })
}

variable "top_level_folder" {
  description = "Top Level Folder Details."
  type = object({
    name = string
    id   = string
  })
}

variable "workforce_identity_providers" {
  description = "Workforce Identity Federation pools."
  type = map(object({
    attribute_condition = optional(string)
    issuer              = string
    display_name        = string
    description         = string
    disabled            = optional(bool, false)
    saml = optional(object({
      idp_metadata_xml = string
    }), null)
  }))
  default  = {}
  nullable = false
}
