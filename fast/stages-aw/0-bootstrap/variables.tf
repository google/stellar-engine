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
variable "alert_email" {
  description = "Email to receive log alerts."
  type        = string
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

variable "billing_budget_amount" {
  description = "Optional Budget configuration for the AW folder. Includes amount and optional threshold rules (defaults to 0.5, 0.75, 0.9). If null, no budget will be created."
  type = object({
    amount          = number
    threshold_rules = optional(list(number), [0.5, 0.75, 0.9])
  })
  default = null
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

variable "custom_roles" {
  description = "Map of role names => list of permissions to additionally create at the organization level."
  type        = map(list(string))
  nullable    = false
  default     = {}
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

variable "groups" {
  # https://cloud.google.com/docs/enterprise/setup-checklist
  description = "Group names or IAM-format principals to grant organization-level permissions. If just the name is provided, the 'group:' principal and organization domain are interpolated."
  type = object({
    gcp-billing-admins      = optional(string, "gcp-billing-admins")
    gcp-devops              = optional(string, "gcp-devops")
    gcp-vpc-network-admins  = optional(string, "gcp-vpc-network-admins")
    gcp-organization-admins = optional(string, "gcp-organization-admins")
    gcp-security-admins     = optional(string, "gcp-security-admins")
    # aliased to gcp-devops as the checklist does not create it
    gcp-support = optional(string, "gcp-devops")
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
    gcs     = optional(string, "US")
    logging = optional(string, "global")
    pubsub  = optional(list(string), [])
    kms     = optional(string, "US")
  })
  nullable = false
  default  = {}
}

# See https://cloud.google.com/architecture/exporting-stackdriver-logging-for-security-and-access-analytics
# for additional logging filter examples

variable "log_sinks" {
  description = "Org-level log sinks, in name => {type, filter} format."
  type = map(object({
    filter = string
    type   = string
  }))
  default = {
    audit-logs = {
      filter = "logName:\"/logs/cloudaudit.googleapis.com%2Factivity\" OR logName:\"/logs/cloudaudit.googleapis.com%2Fsystem_event\" OR protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.TransparencyLog\""
      type   = "logging"
    }
    vpc-sc = {
      filter = "protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata\""
      type   = "logging"
    }
    workspace-audit-logs = {
      filter = "logName:\"/logs/cloudaudit.googleapis.com%2Fdata_access\" and protoPayload.serviceName:\"login.googleapis.com\""
      type   = "logging"
    }

    # CIS Compliance Benchmark 2.2
    empty-audit-logs = {
      filter = ""
      type   = "logging"
    }
  }
  validation {
    condition = alltrue([
      for k, v in var.log_sinks :
      contains(["bigquery", "logging", "pubsub", "storage"], v.type)
    ])
    error_message = "Type must be one of 'bigquery', 'logging', 'pubsub', 'storage'."
  }
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

variable "outputs_location" {
  description = "Enable writing provider, tfvars and CI/CD workflow files to local filesystem. Leave null to disable."
  type        = string
  default     = null
}

variable "prefix" {
  description = "Prefix used for resources that need unique names. Use 9 characters or less."
  type        = string
  validation {
    condition     = try(length(var.prefix), 0) <= 7
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

variable "regions" {
  description = "Region definitions. Must be specified in terraform.tfvars. Example: us-east4 for FedRAMP High compliance."
  type = object({
    primary = string
  })
  nullable = false
  default  = {
    primary = "us-east4"
  }
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




variable "federated_identity_providers" {
  description = "Workload Identity Federation providers."
  type = map(object({
    attribute_condition = optional(string)
    issuer              = string
    custom_settings = optional(object({
      issuer_uri = optional(string)
      audiences  = optional(list(string), [])
      jwks_json  = optional(string)
    }), {})
    attribute_mapping = optional(map(string))
    audiences         = optional(list(string))
  }))
  default  = {}
  nullable = false
}

variable "workforce_identity_pool" {
  description = "Workforce Identity Federation pool configuration."
  type = object({
    display_name     = optional(string)
    description      = optional(string)
    disabled         = optional(bool, false)
    session_duration = optional(string)
  })
  default = null
}
