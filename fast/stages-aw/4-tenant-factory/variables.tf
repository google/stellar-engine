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

# tfdoc:file:description Stage variables and plan-time guardrails.

variable "automation" {
  description = "Optional Stage 0 outputs bucket, KMS keys, and project ID."
  type = object({
    kms_keys = optional(object({
      gcs = optional(string)
    }), {})
    outputs_bucket = optional(string)
    project_id     = optional(string)
  })
  default  = {}
  nullable = false
}

variable "billing_account" {
  description = "Optional billing account used when billing mode is managed."
  type = object({
    id = optional(string)
  })
  default = null
  validation {
    condition = (
      try(var.billing_account.id, null) == null ||
      try(trimspace(var.billing_account.id), "") != ""
    )
    error_message = "billing_account.id must be non-empty when set."
  }
}

variable "billing_linkage_mode" {
  description = "Billing attachment mode: managed or external_gate."
  type        = string
  default     = "managed"
  nullable    = false
  validation {
    condition = contains(
      ["managed", "external_gate"],
      var.billing_linkage_mode
    )
    error_message = "billing_linkage_mode must be managed or external_gate."
  }
  validation {
    condition = (
      var.billing_linkage_mode != "managed" ||
      try(trimspace(var.billing_account.id), "") != ""
    )
    error_message = "billing_account.id is required in managed billing mode."
  }
}

variable "environment_folders" {
  description = "Map of environment keys to folders/<id> parent folder IDs."
  type        = map(string)
  default     = {}
  nullable    = false
  validation {
    condition = alltrue([
      for k, v in var.environment_folders :
      can(regex("^[a-z][a-z0-9-]*$", k)) &&
      can(regex("^folders/[0-9]+$", v))
    ])
    error_message = "Keys must be slugs and values must match folders/<id>."
  }
}

variable "factories_config" {
  description = "Paths to YAML tenant manifests and optional templates."
  type = object({
    project_templates_path = optional(string)
    tenants_data_path      = optional(string, "data/tenants")
  })
  default  = {}
  nullable = false
}

variable "folder_ids" {
  # tfdoc:variable:source 1-resman
  description = "Optional Stage 1 folder IDs mapping with envs fallback."
  type = object({
    envs = optional(map(string), {})
  })
  default  = {}
  nullable = false
  validation {
    condition = alltrue([
      for k, v in coalesce(try(var.folder_ids.envs, null), {}) :
      v == null || (
        can(regex("^[a-z][a-z0-9-]*$", lower(k))) &&
        can(regex("^folders/[0-9]+$", v))
      )
    ])
    error_message = "folder_ids.envs entries must match folders/<id>."
  }
}

variable "force_destroy" {
  description = "Allow DELETE on archived projects and state bucket destroy."
  type        = bool
  default     = false
  nullable    = false
}

variable "kms_keys" {
  description = "Map of CMEK aliases to Cloud KMS crypto key resource IDs."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "prefix" {
  description = "Lowercase prefix up to 10 characters for tenant resources."
  type        = string
  nullable    = false
  validation {
    condition     = length(var.prefix) > 0 && length(var.prefix) <= 10
    error_message = "prefix must be between 1 and 10 characters."
  }
  validation {
    condition = can(
      regex("^[a-z]([a-z0-9-]*[a-z0-9])?$", var.prefix)
    )
    error_message = "prefix must use lowercase letters, digits, and hyphens."
  }
}

variable "read_stage_outputs_from_gcs" {
  description = "Read curated Stage 1 JSON outputs from automation bucket."
  type        = bool
  default     = false
  nullable    = false
  validation {
    condition = (
      !var.read_stage_outputs_from_gcs ||
      try(trimspace(var.automation.outputs_bucket), "") != ""
    )
    error_message = "automation.outputs_bucket is required for GCS reads."
  }
}

variable "shared_vpc_host_projects" {
  description = "Map of environment keys to Shared VPC host project IDs."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "storage_location" {
  description = "Default GCS location for per-tenant automation buckets."
  type        = string
  default     = "us-east4"
  nullable    = false
}

variable "tenants" {
  description = "Optional HCL tenant definitions merged with YAML manifests."
  type = map(object({
    automation = optional(object({
      bucket_kms_key  = optional(string)
      bucket_location = optional(string)
      create_bucket   = optional(bool, true)
      project_id      = optional(string)
      service_accounts = optional(map(object({
        description  = optional(string)
        display_name = optional(string)
      })), {})
    }))
    contacts         = optional(map(list(string)), {})
    descriptive_name = optional(string)
    environment      = string
    iam              = optional(map(list(string)), {})
    labels           = optional(map(string), {})
    lifecycle_state  = optional(string, "active")
    projects = map(object({
      contacts         = optional(map(list(string)), {})
      descriptive_name = optional(string)
      iam              = optional(map(list(string)), {})
      iam_bindings_additive = optional(map(object({
        member = string
        role   = string
        condition = optional(object({
          description = optional(string)
          expression  = string
          title       = string
        }))
      })), {})
      iam_by_principals = optional(map(list(string)), {})
      kms_services      = optional(map(list(string)), {})
      labels            = optional(map(string), {})
      lien_reason       = optional(string)
      metric_scopes     = optional(list(string), [])
      name              = optional(string)
      project_template  = optional(string)
      service_accounts = optional(map(object({
        description    = optional(string)
        display_name   = optional(string)
        iam_self_roles = optional(list(string), [])
      })), {})
      services                     = optional(list(string), [])
      shared_vpc_host_project      = optional(string)
      shared_vpc_network_users     = optional(list(string), [])
      shared_vpc_service_agent_iam = optional(map(list(string)), {})
      shared_vpc_service_grants    = optional(list(string), [])
      shared_vpc_subnets           = optional(list(string), [])
      tag_bindings                 = optional(map(string), {})
      vpc_sc_perimeter = optional(object({
        is_dry_run     = optional(bool, false)
        perimeter_name = string
      }))
    }))
    tag_bindings = optional(map(string), {})
    tenant_id    = optional(string)
  }))
  default  = {}
  nullable = false
  validation {
    condition = (
      var.read_stage_outputs_from_gcs ||
      alltrue([
        for k, v in var.tenants : contains(
          distinct(concat(
            keys(var.environment_folders),
            [
              for ek, ev in coalesce(try(var.folder_ids.envs, null), {}) :
              lower(ek) if ev != null
            ]
          )),
          v.environment
        )
      ])
    )
    error_message = "Tenant environment must exist in environment_folders."
  }
  validation {
    condition = alltrue([
      for k, v in var.tenants :
      can(regex(
        "^[a-z]([a-z0-9-]{0,18}[a-z0-9])?$",
        coalesce(v.tenant_id, trimprefix(k, "${v.environment}/"))
      ))
    ])
    error_message = "Tenant slug must be 1 to 20 lowercase slug characters."
  }
  validation {
    condition = alltrue([
      for k, v in var.tenants :
      contains(["active", "archived"], v.lifecycle_state)
    ])
    error_message = "Tenant lifecycle_state must be active or archived."
  }
  validation {
    condition = alltrue([
      for k, v in var.tenants : length(v.projects) > 0
    ])
    error_message = "Every tenant must define at least one project."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for role in distinct(concat(
          keys(tv.iam),
          flatten([
            for pk, pv in tv.projects : concat(
              keys(pv.iam),
              keys(pv.shared_vpc_service_agent_iam),
              flatten(values(pv.iam_by_principals)),
              [for bk, bv in pv.iam_bindings_additive : bv.role],
              flatten([
                for sk, sv in pv.service_accounts : sv.iam_self_roles
              ])
            )
          ])
          )) : !contains([
          "roles/compute.xpnAdmin",
          "roles/editor",
          "roles/iam.organizationRoleAdmin",
          "roles/iam.securityAdmin",
          "roles/iam.serviceAccountKeyAdmin",
          "roles/orgpolicy.policyAdmin",
          "roles/owner",
          "roles/resourcemanager.folderAdmin",
          "roles/resourcemanager.folderIamAdmin",
          "roles/resourcemanager.lienModifier",
          "roles/resourcemanager.organizationAdmin",
          "roles/resourcemanager.projectIamAdmin",
        ], role)
      ]
    ]))
    error_message = "Tenant IAM cannot grant forbidden high-privilege roles."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects : concat(
          [
            for role in keys(pv.shared_vpc_service_agent_iam) :
            contains([
              "roles/composer.sharedVpcAgent",
              "roles/compute.networkUser",
              "roles/container.hostServiceAgentUser",
              "roles/vpcaccess.user",
            ], role)
          ],
          [
            for member in flatten(values(pv.shared_vpc_service_agent_iam)) :
            can(regex("^\\$service_agents:[a-z0-9-]+$", member))
          ]
        )
      ]
    ]))
    error_message = "shared_vpc_service_agent_iam requires allowlisted roles."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects : [
          for grant in pv.shared_vpc_service_grants :
          can(regex(
            "^\\$service_agents:[a-z0-9-]+\\.googleapis\\.com$",
            grant
          ))
        ]
      ]
    ]))
    error_message = "shared_vpc_service_grants requires service agent APIs."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects : [
          for subnet in pv.shared_vpc_subnets :
          can(regex("^[a-z]+-[a-z]+[0-9]+/[a-z][a-z0-9-]*$", subnet))
        ]
      ]
    ]))
    error_message = "shared_vpc_subnets entries must use <region>/<subnet>."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects :
        pv.vpc_sc_perimeter == null ||
        can(regex(
          "^accessPolicies/[0-9]+/servicePerimeters/[A-Za-z0-9_]+$",
          pv.vpc_sc_perimeter.perimeter_name
        ))
      ]
    ]))
    error_message = "vpc_sc_perimeter.perimeter_name is invalid."
  }
  validation {
    condition = alltrue([
      for tk, tv in var.tenants :
      tv.automation == null || (
        try(coalesce(
          tv.automation.project_id,
          try(var.automation.project_id, null)
        ), null) != null &&
        alltrue([
          for sk in keys(tv.automation.service_accounts) :
          contains(["ro", "rw"], sk)
        ])
      )
    ])
    error_message = "automation requires project_id and only rw or ro SA keys."
  }
}
