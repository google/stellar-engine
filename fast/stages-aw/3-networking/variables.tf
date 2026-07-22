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

variable "auth_code" {
  description = "Optional Palo Alto auth-code for BYOL license activation."
  type        = string
  default     = ""
}

variable "automation" {
  # tfdoc:variable:source 1-assured-workload
  description = "Automation resources created by the bootstrap stage."
  type = object({
    config_bucket           = optional(string)
    inputs_bucket           = optional(string)
    outputs_bucket          = string
    tenant_bucket           = optional(string)
    project_id              = string
    project_number          = string
    federated_identity_pool = optional(string)
    federated_identity_providers = map(object({
      audiences        = list(string)
      issuer           = string
      issuer_uri       = string
      name             = string
      principal_branch = string
      principal_repo   = string
    }))
    service_accounts = object({
      bootstrap   = string
      bootstrap-r = string
      resman      = string
      resman-r    = string
    })
  })
}

variable "billing_account" {
  # tfdoc:variable:source 1-assured-workload
  description = "Billing account id. If billing account is not part of the same org set `is_org_level` to false."
  type = object({
    id           = string
    is_org_level = optional(bool, true)
    no_iam       = optional(bool, false)
  })
  validation {
    condition     = var.billing_account.is_org_level != null
    error_message = "Invalid `null` value for `billing_account.is_org_level`."
  }
}
/*
variable "common_services_folder" {
  description = "Folder ID for common services."
  type        = string
  default     = null
}

variable "custom_roles" {
  description = "Custom roles for the organization."
  type        = map(string)
  default     = {}
}
*/
variable "dns" {
  description = "DNS configuration."
  type = object({
    enable_logging = optional(bool, true)
    resolvers      = optional(list(string), [])
  })
  default  = {}
  nullable = false
}

variable "essential_contacts" {
  description = "Email used for essential contacts, unset if null."
  type        = string
  default     = null
}

variable "factories_config" {
  description = "Configuration for network resource factories."
  type = object({
    data_dir              = optional(string, "data")
    dns_policy_rules_file = optional(string, "data/dns-policy-rules.yaml")
    firewall_policy_name  = optional(string, "net-default")
  })
  default = {
    data_dir = "data"
  }
  nullable = false
  validation {
    condition     = var.factories_config.data_dir != null
    error_message = "Data folder needs to be non-null."
  }
  validation {
    condition     = var.factories_config.firewall_policy_name != null
    error_message = "Firewall policy name needs to be non-null."
  }
}
/*
variable "fast_features" {
  description = "Enable/disable FAST features."
  type        = map(bool)
  default     = {}
}
*/
variable "folder_ids" {
  # tfdoc:variable:source 2-resman
  description = "Folders to be used for the networking resources in folders/nnnnnnnnnnn format. If null, folder will be created."
  type = object({
    networking = string
    envs       = optional(map(string))
    security   = optional(string)
  })
}


/*
variable "groups" {
  description = "GCP groups for the organization."
  type        = map(string)
  default     = {}
}

variable "locations" {
  description = "Locations for different GCP services."
  type = object({
    bq      = optional(string, "US")
    gcs     = optional(list(string), ["US"])
    logging = optional(list(string), ["global"])
    pubsub  = optional(list(string), [])
    kms     = optional(list(string), ["US"])
  })
}

variable "logging" {
  description = "Logging configuration."
  type = object({
    project_id        = string
    project_number    = string
    writer_identities = map(string)
  })
}


variable "network_quota_preferred_value" {
  description = "The preferred target value for the Google Cloud network quota preference."
  type        = number
  default     = 50
}
*/
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
  description = "Path where providers and tfvars files for the following stages are written. Leave empty to disable."
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
/*
variable "psa_ranges" {
  description = "IP ranges used for Private Service Access (e.g. CloudSQL). Ranges is in name => range format."
  type = object({
    dev = optional(list(object({
      ranges         = map(string)
      export_routes  = optional(bool, false)
      import_routes  = optional(bool, false)
      peered_domains = optional(list(string), [])
    })), [])
    test = optional(list(object({
      ranges         = map(string)
      export_routes  = optional(bool, false)
      import_routes  = optional(bool, false)
      peered_domains = optional(list(string), [])
    })), [])
    prod = optional(list(object({
      ranges         = map(string)
      export_routes  = optional(bool, false)
      import_routes  = optional(bool, false)
      peered_domains = optional(list(string), [])
    })), [])
  })
  nullable = false
  default  = {}
}
*/
variable "regime_mapping" {
  description = "Mapping of compliance regime names to short codes."
  type        = map(string)
}

variable "regions" {
  description = "Region definitions."
  type = object({
    primary   = string
    secondary = list(string)
  })
  default = {
    primary   = "us-east4"
    secondary = [""]
  }
}

variable "service_accounts" {
  # tfdoc:variable:source 2-resman
  description = "Automation service accounts in name => email format."
  type = object({
    data-platform-dev    = string
    data-platform-prod   = string
    gke-dev              = string
    gke-prod             = string
    project-factory-dev  = string
    project-factory-prod = string
    shared-services      = optional(string)
  })
  default = null
}

variable "shared_services_project_id" {
  description = "The project ID for shared services inherited from Stage 1."
  type        = string
}

# To get a list of available official images, please run the following command:
# `gcloud compute images list --filter="family ~ vmseries" --project paloaltonetworksgcp-public --no-standard-images`
/*
variable "tenant_accounts" {
  description = "Tenant accounts configuration."
  type        = any
  default     = {}
}
*/
variable "tenant_environments" {
  description = "List of environments to be created for projects to go into."
  type = map(object({
    admin = string
  }))
}

