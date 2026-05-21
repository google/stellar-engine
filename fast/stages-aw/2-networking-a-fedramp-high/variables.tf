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

variable "automation" {
  # tfdoc:variable:source 0-bootstrap
  description = "Automation resources created by the bootstrap stage."
  type = object({
    outputs_bucket = string
  })
}

variable "billing_account" {
  # tfdoc:variable:source 0-bootstrap
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

variable "custom_roles" {
  description = "Custom roles defined at the org level, in key => id format."
  type = object({
    service_project_network_admin = string
  })
  default = null
}

variable "dns" {
  description = "DNS configuration."
  type = object({
    enable_logging = optional(bool, true) # CIS Compliance Benchmark 2.12
    resolvers      = optional(list(string), [])
  })
  default  = {}
  nullable = false
}

variable "envs_folders" {
  description = "List of environments to be created for projects to go into."
  type = map(object({
    admin = string
  }))
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

variable "folder_ids" {
  # tfdoc:variable:source 1-resman
  description = "Folders to be used for the networking resources in folders/nnnnnnnnnnn format. If null, folder will be created."
  type = object({
    networking = string
    envs       = optional(map(string))
  })
}

variable "gcp_ranges" {
  description = "GCP address ranges in name => range format."
  type        = map(string)
  default = {
    gcp_dev_primary             = "10.68.0.0/16"
    gcp_landing_landing_primary = "10.200.0.0/16"
    gcp_dmz_primary             = "10.64.128.0/24"
    gcp_prod_primary            = "10.72.0.0/16"
  }
}

variable "organization" {
  # tfdoc:variable:source 0-bootstrap
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
  # tfdoc:variable:source 0-bootstrap
  description = "Prefix used for resources that need unique names. Use 9 characters or less."
  type        = string

  validation {
    condition     = try(length(var.prefix), 0) < 10
    error_message = "Use a maximum of 9 characters for prefix."
  }
}

variable "psa_ranges" {
  description = "IP ranges used for Private Service Access (e.g. CloudSQL). Ranges is in name => range format."
  type = object({
    dev = optional(list(object({
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

variable "regions" {
  # tfdoc:variable:source 0-bootstrap
  description = "Region definitions. Inherited from 0-bootstrap outputs. Must be specified in bootstrap terraform.tfvars."
  type = object({
    primary = string
  })
  nullable = false
}

variable "service_accounts" {
  # tfdoc:variable:source 1-resman
  description = "Automation service accounts in name => email format."
  type = object({
    data-platform-dev    = string
    data-platform-prod   = string
    gke-dev              = string
    gke-prod             = string
    project-factory-dev  = string
    project-factory-prod = string
  })
  default = null
}

variable "tenant_accounts" {
  # tfdoc:variable:soruce 1-resman
  description = "Base Tenant accounts that are created for each folder, provided as a combination of environment and tenant."
  type = map(object({
    tenant          = string
    env             = string
    main_project    = string
    admin_principal = string
  }))
}

variable "billing_override" {
  description = "Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects."
  type = object({
    project         = string
    billing_project = string
  })
  default = null
}

variable "assured_workloads" {
  description = "Assured Workloads configuration."
  type        = any
  default     = null
}

variable "common_services_folder" {
  description = "Common services folder ID."
  type        = string
  default     = null
}

variable "logging" {
  description = "Logging configuration."
  type        = any
  default     = null
}

variable "fast_features" {
  description = "FAST features enabled."
  type        = any
  default     = null
}

variable "groups" {
  description = "IAM groups mapping."
  type        = any
  default     = null
}

variable "regime_mapping" {
  description = "Compliance regime shorthand mapping."
  type        = any
  default     = null
}

variable "subnets" {
  description = "VPC subnet configurations keyed by network name."
  type = map(list(object({
    name                             = string
    ip_cidr_range                    = string
    region                           = string
    description                      = optional(string)
    enable_private_access            = optional(bool, true)
    allow_subnet_cidr_routes_overlap = optional(bool)
    flow_logs_config = optional(object({
      aggregation_interval = optional(string)
      filter_expression    = optional(string)
      flow_sampling        = optional(number)
      metadata             = optional(string)
      metadata_fields      = optional(list(string))
    }))
    secondary_ip_ranges = optional(map(string))
    iam                 = optional(map(list(string)), {})
    tenant              = optional(string)
  })))
  default  = {}
  nullable = false
}

variable "proxy_subnets" {
  description = "VPC proxy-only subnet CIDRs keyed by environment."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "dns_policy_rules" {
  description = "DNS response policy rules in name => rule format."
  type = map(object({
    dns_name = string
    behavior = optional(string, "bypassResponsePolicy")
    local_data = optional(map(object({
      ttl     = optional(number)
      rrdatas = optional(list(string), [])
    })), {})
  }))
  default  = {}
  nullable = false
}

variable "cidrs" {
  description = "Named CIDR ranges to use in firewall rules."
  type        = map(list(string))
  default     = {}
  nullable    = false
}

variable "firewall_rules" {
  description = "Firewall rules for each VPC / environment spoke."
  type = map(object({
    ingress = optional(map(object({
      description          = optional(string)
      deny                 = optional(bool, false)
      source_ranges        = optional(list(string))
      sources              = optional(list(string))
      targets              = optional(list(string))
      use_service_accounts = optional(bool, false)
      rules = optional(list(object({
        protocol = string
        ports    = optional(list(string))
      })))
    })), {})
    egress = optional(map(object({
      description          = optional(string)
      deny                 = optional(bool, true)
      destination_ranges   = optional(list(string))
      targets              = optional(list(string))
      use_service_accounts = optional(bool, false)
      rules = optional(list(object({
        protocol = string
        ports    = optional(list(string))
      })))
    })), {})
  }))
  default  = {}
  nullable = false
}


