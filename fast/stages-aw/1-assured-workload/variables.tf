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

variable "apply_tier_1_pubsub_sink" {
  description = "Toggles whether to apply org tier-1 pubsub sink."
  type        = bool
  nullable    = false
  default     = true
}

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

variable "bootstrap_user" {
  description = "Email of the nominal user running this stage for the first time."
  type        = string
  default     = null
}

variable "cicd_repositories" {
  description = "CI/CD repository configuration. Identity providers reference keys in the `federated_identity_providers` variable. Set to null to disable, or set individual repositories to null if not needed."
  type = object({
    bootstrap = optional(object({
      name              = string
      type              = string
      branch            = optional(string)
      identity_provider = optional(string)
    }))
    resman = optional(object({
      name              = string
      type              = string
      branch            = optional(string)
      identity_provider = optional(string)
    }))
    tenant = optional(object({
      name              = string
      type              = string
      branch            = optional(string)
      identity_provider = optional(string)
    }))
  })
  default = null
  validation {
    condition = alltrue([
      for k, v in coalesce(var.cicd_repositories, {}) :
      v == null || try(v.name, null) != null
    ])
    error_message = "Non-null repositories need a non-null name."
  }
  validation {
    condition = alltrue([
      for k, v in coalesce(var.cicd_repositories, {}) :
      v == null || (
        try(v.identity_provider, null) != null
        ||
        try(v.type, null) == "sourcerepo"
      )
    ])
    error_message = "Non-null repositories need a non-null provider unless type is 'sourcerepo'."
  }
  validation {
    condition = alltrue([
      for k, v in coalesce(var.cicd_repositories, {}) :
      v == null || (
        contains(["github", "gitlab", "sourcerepo"], coalesce(try(v.type, null), "null"))
      )
    ])
    error_message = "Invalid repository type, supported types: 'github' 'gitlab' or 'sourcerepo'."
  }
}

variable "essential_contacts" {
  description = "Email used for essential contacts, unset if null."
  type        = string
  default     = null
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

variable "fast_features" {
  description = "Selective control for top-level FAST features."
  type = object({
    data_platform   = optional(bool, false)
    gcve            = optional(bool, false)
    gke             = optional(bool, false)
    project_factory = optional(bool, false)
    sandbox         = optional(bool, false)
    teams           = optional(bool, false)
    envs            = optional(bool, false)
  })
  default  = {}
  nullable = false
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

variable "log_sinks" {
  description = "Organization-level log sinks configuration."
  type = map(object({
    filter = string
    type   = string
  }))
  nullable = false
  default  = {}
}

variable "logging_kms_key" {
  description = "value of the KMS key used for logging."
  type        = string
  default     = null
}

variable "organization" {
  description = "Organization details."
  type = object({
    id          = number
    domain      = optional(string)
    customer_id = optional(string)
  })
}

variable "outputs_location" {
  description = "Enable writing provider, tfvars and CI/CD workflow files to local filesystem. Leave null to disable."
  type        = string
  default     = null
}

variable "prefix" {
  description = "Prefix used for resources that need unique names. Use 9 characters or less."
  type        = string
  validation {
    condition     = try(length(var.prefix), 0) <= 10
    error_message = "Use a maximum of 7 characters for prefix."
  }
}

variable "project_parent_ids" {
  description = "Optional parents for projects created here in folders/nnnnnnn format. Null values will use the organization as parent."
  type = object({
    automation = optional(string)
    billing    = optional(string)
    logging    = optional(string)
  })
  default  = {}
  nullable = false
}

variable "regime_mapping" {
  description = "Mapping of compliance regime names to short codes."
  type        = map(string)
  default = {
    "COMPLIANCE_REGIME_UNSPECIFIED" = "CRU"
    "IL2"                           = "IL2"
    "IL4"                           = "IL4"
    "IL5"                           = "IL5"
    "FEDRAMP_HIGH"                  = "FRH"
    "FEDRAMP_MODERATE"              = "FRM"
    # other compliance regimes supported by google
    "CJIS"                                              = "CJIS"
    "US_REGIONAL_ACCESS"                                = "USRE"
    "HIPAA"                                             = "HIPAA"
    "HITRUST"                                           = "HITRUST"
    "EU_REGIONS_AND_SUPPORT"                            = "EURS"
    "CA_REGIONS_AND_SUPPORT"                            = "CARS"
    "ITAR"                                              = "ITAR"
    "AU_REGIONS_AND_US_SUPPORT"                         = "AUUSRS"
    "ASSURED_WORKLOADS_FOR_PARTNERS"                    = "PART"
    "ISR_REGIONS"                                       = "ISR"
    "ISR_REGIONS_AND_SUPPORT"                           = "ISRSUPP"
    "CA_PROTECTED_B"                                    = "CA_PROT_B"
    "JP_REGIONS_AND_SUPPORT"                            = "JP_REGIONS"
    "KSA_REGIONS_AND_SUPPORT_WITH_SOVEREIGNTY_CONTROLS" = "KSA_SOV"
    "REGIONAL_CONTROLS"                                 = "REGIONAL"
    "HEALTHCARE_AND_LIFE_SCIENCES_CONTROLS"             = "HCLS"
    "HEALTHCARE_AND_LIFE_SCIENCES_CONTROLS_US_SUPPORT"  = "HCLS_US"
    "IRS_1075"                                          = "IRS_1075"
    "CANADA_CONTROLLED_GOODS"                           = "CAGOODS"
  }
}

variable "top_level_folder" {
  description = "Top Level Folder Details."
  type = object({
    name = string
    id   = string
  })
}

variable "workload_identity_providers" {
  description = "Workload Identity Federation pools. The `cicd_repositories` variable references keys here."
  type = map(object({
    attribute_condition = optional(string)
    issuer              = string
    custom_settings = optional(object({
      issuer_uri = optional(string)
      audiences  = optional(list(string), [])
      jwks_json  = optional(string)
    }), {})
  }))
  default  = {}
  nullable = false
  # TODO: fix validation
  # validation {
  #   condition     = var.federated_identity_providers.custom_settings == null
  #   error_message = "Custom settings cannot be null."
  # }
}
