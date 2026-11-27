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

# Validations reuse the role, regex, and preset locals in main.tf so this
# layer and the terraform_data.tenant_validation preconditions share one
# definition of every guardrail.

variable "allowed_custom_roles" {
  description = "Custom role IDs or $custom_roles refs tenant IAM may grant."
  type        = list(string)
  default     = []
  nullable    = false
  validation {
    condition = alltrue([
      for role in var.allowed_custom_roles : anytrue([
        for k in ["organization", "project", "reference"] :
        can(regex(local._role_id_regexes[k], role))
      ])
    ])
    error_message = "allowed_custom_roles must list custom role IDs or refs."
  }
}

variable "allowed_privileged_roles" {
  description = "Denylisted or service agent roles deliberately exempted."
  type        = list(string)
  default     = []
  nullable    = false
  validation {
    condition = alltrue([
      for role in var.allowed_privileged_roles :
      contains(local._forbidden_roles_lower, trimspace(lower(role))) ||
      strcontains(lower(role), "serviceagent")
    ])
    error_message = "Only denylisted or service agent roles can be exempted."
  }
}

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

variable "custom_roles" {
  # tfdoc:variable:source 0-bootstrap
  description = "Optional Stage 0 custom role IDs keyed by role name."
  type        = map(string)
  default     = {}
  nullable    = false
  validation {
    condition = alltrue([
      for k, v in var.custom_roles :
      can(regex(local._role_id_regexes.organization, v)) ||
      can(regex(local._role_id_regexes.project, v))
    ])
    error_message = "custom_roles values must be custom role IDs."
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
  description = "Allow DELETE and state bucket destroy for archived tenants."
  type        = bool
  default     = false
  nullable    = false
}

variable "host_project_ids" {
  # tfdoc:variable:source 2-networking
  description = "Optional Stage 2 host project IDs keyed by environment."
  type        = map(string)
  default     = {}
  nullable    = false
  validation {
    condition = alltrue([
      for k, v in var.host_project_ids :
      v == null || can(regex(local._gcp_id_regex, v))
    ])
    error_message = "host_project_ids values must be project IDs."
  }
}

variable "kms_keys" {
  description = "Map of CMEK aliases to Cloud KMS crypto key resource IDs."
  type        = map(string)
  default     = {}
  nullable    = false
  validation {
    condition = alltrue([
      for k, v in var.kms_keys : can(regex(local._kms_key_id_regex, v))
    ])
    error_message = "kms_keys values must be Cloud KMS crypto key IDs."
  }
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

variable "privileged_shared_vpc_service_grants" {
  description = "APIs allowed to use privileged Shared VPC service presets."
  type        = list(string)
  default     = []
  nullable    = false
  validation {
    condition = alltrue([
      for api in var.privileged_shared_vpc_service_grants :
      can(regex(local._api_regex, api))
    ])
    error_message = "Entries must be <api>.googleapis.com names."
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
  validation {
    condition = alltrue([
      for k, v in var.shared_vpc_host_projects :
      can(regex("^[a-z][a-z0-9-]*$", k)) &&
      can(regex(local._gcp_id_regex, v))
    ])
    error_message = "Keys must be environment slugs and values project IDs."
  }
}

variable "shared_vpc_subnet_allowlist" {
  description = "Optional <env>/<tenant> map of allocated Shared VPC subnets."
  type        = map(list(string))
  default     = null
  validation {
    condition = var.shared_vpc_subnet_allowlist == null ? true : alltrue(
      flatten([
        for k, v in var.shared_vpc_subnet_allowlist : concat(
          [can(regex(local._tenant_key_regex, k))],
          [for subnet in v : can(regex(local._subnet_regex, subnet))]
        )
      ])
    )
    error_message = "Use <env>/<tenant> keys and <region>/<subnet> values."
  }
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
        iam            = optional(map(list(string)), {})
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
        local._tenant_slug_regex,
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
        for scoped in [{
          project = concat(
            keys(tv.iam),
            flatten([
              for pk, pv in tv.projects : concat(
                keys(pv.iam),
                flatten(values(pv.iam_by_principals)),
                [for bk, bv in pv.iam_bindings_additive : bv.role],
                flatten([
                  for sk, sv in pv.service_accounts : sv.iam_self_roles
                ])
              )
            ])
          )
          sa = flatten([
            for pk, pv in tv.projects : [
              for sk, sv in pv.service_accounts : keys(sv.iam)
            ]
          ])
          }] : concat(
          [
            for role in scoped.project :
            !contains(local._forbidden_project_roles, trimspace(lower(role)))
          ],
          [
            for role in scoped.sa :
            !contains(local._forbidden_sa_roles, trimspace(lower(role)))
          ],
          [
            for role in concat(scoped.project, scoped.sa) : (
              !strcontains(trimspace(lower(role)), "serviceagent") ||
              contains(local._allowed_privileged_roles, trimspace(lower(role)))
            )
          ]
        )
      ]
    ]))
    error_message = "Tenant IAM cannot use forbidden or service agent roles."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for role in concat(
          keys(tv.iam),
          flatten([
            for pk, pv in tv.projects : concat(
              keys(pv.iam),
              flatten(values(pv.iam_by_principals)),
              [for bk, bv in pv.iam_bindings_additive : bv.role],
              flatten([
                for sk, sv in pv.service_accounts :
                concat(sv.iam_self_roles, keys(sv.iam))
              ])
            )
          ])
          ) : (
          startswith(role, "$custom_roles:")
          ? (
            contains(keys(local._custom_role_refs), role) && (
              contains(local._allowed_custom_roles, role) ||
              contains(
                local._allowed_custom_roles,
                lookup(local._custom_role_refs, role, "")
              )
            )
          )
          : (
            can(regex(local._role_id_regexes.predefined, role)) || (
              (
                can(regex(local._role_id_regexes.organization, role)) ||
                can(regex(local._role_id_regexes.project, role))
              ) &&
              contains(local._allowed_custom_roles, role)
            )
          )
        )
      ]
    ]))
    error_message = join(" ", [
      "Tenant IAM roles must be predefined roles/ IDs, custom role IDs in",
      "allowed_custom_roles, or allowlisted $custom_roles references.",
    ])
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects : concat(
          [
            for role in keys(pv.shared_vpc_service_agent_iam) :
            contains(local._allowed_shared_vpc_agent_roles, role)
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
          can(regex(local._svpc_grant_regex, grant)) && contains(
            keys(local._svpc_grant_roles),
            trimprefix(grant, "$service_agents:")
          )
        ]
      ]
    ]))
    error_message = "shared_vpc_service_grants must name a known preset."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects : [
          for api in [
            for grant in pv.shared_vpc_service_grants :
            trimprefix(grant, "$service_agents:")
            ] : (
            !contains(local._privileged_svpc_grant_apis, api) ||
            contains(var.privileged_shared_vpc_service_grants, api)
          )
        ]
      ]
    ]))
    error_message = join(" ", [
      "Shared VPC presets that grant host project roles outside the agent",
      "allowlist require privileged_shared_vpc_service_grants.",
    ])
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects : [
          for subnet in pv.shared_vpc_subnets :
          can(regex(local._subnet_regex, subnet))
        ]
      ]
    ]))
    error_message = "shared_vpc_subnets entries must use <region>/<subnet>."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects :
        pv.shared_vpc_host_project == null ||
        pv.shared_vpc_host_project == lookup(
          local.environment_host_projects, tv.environment, null
        )
      ]
    ]))
    error_message = join(" ", [
      "shared_vpc_host_project must match the host project resolved for",
      "the tenant environment.",
    ])
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects :
        length(pv.shared_vpc_network_users) == 0 ||
        length(pv.shared_vpc_subnets) > 0
      ]
    ]))
    error_message = "shared_vpc_network_users requires shared_vpc_subnets."
  }
  validation {
    condition = var.shared_vpc_subnet_allowlist == null ? true : alltrue(
      flatten([
        for tk, tv in var.tenants : [
          for key in [format(
            "%s/%s",
            tv.environment,
            coalesce(tv.tenant_id, trimprefix(tk, "${tv.environment}/"))
            )] : [
            for pk, pv in tv.projects : [
              for subnet in pv.shared_vpc_subnets : contains(
                lookup(var.shared_vpc_subnet_allowlist, key, []), subnet
              )
            ]
          ]
        ]
      ])
    )
    error_message = "Subnets must be listed in shared_vpc_subnet_allowlist."
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
  validation {
    condition = alltrue([
      for tk, tv in var.tenants :
      tv.automation == null ? true : (
        !tv.automation.create_bucket ||
        tv.automation.bucket_kms_key != null ||
        try(coalesce(
          tv.automation.project_id,
          try(var.automation.project_id, null)
        ), null) == try(var.automation.project_id, null)
      )
    ])
    error_message = join(" ", [
      "automation.bucket_kms_key is required when automation.project_id",
      "differs from the Stage 0 automation project.",
    ])
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for pk, pv in tv.projects : [
          for svc in keys(pv.kms_services) : can(regex(local._api_regex, svc))
        ]
      ]
    ]))
    error_message = "kms_services keys must be <api>.googleapis.com names."
  }
  validation {
    condition = alltrue(flatten([
      for tk, tv in var.tenants : [
        for ref in concat(
          compact([try(tv.automation.bucket_kms_key, null)]),
          flatten([
            for pk, pv in tv.projects : flatten(values(pv.kms_services))
          ])
          ) : (
          contains(keys(var.kms_keys), ref) ||
          can(regex(local._kms_key_id_regex, ref))
        )
      ]
    ]))
    error_message = "KMS references must be kms_keys aliases or key IDs."
  }
}
