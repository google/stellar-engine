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
    regime   = optional(string)
    location = optional(string)
    folder   = optional(string)
  })
  nullable = false
  default  = {}
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

variable "billing_override" {
  description = "Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects."
  type = object({
    project         = string
    billing_project = string
  })
  default = null
}

variable "centralized_egress" {
  description = "Optional centralized Internet Egress VPC spoke running Secure Web Proxy in next-hop routing mode with Cloud NAT."
  type = object({
    enabled           = optional(bool, false)
    subnet_cidr       = optional(string, "10.64.250.0/24")
    proxy_subnet_cidr = optional(string, "10.64.251.0/24")
    swp_ip            = optional(string, "10.64.250.10")
    ports             = optional(list(number), [80, 443])
    route_tags        = optional(list(string))
    certificates      = optional(list(string), [])
    policy_rules = optional(map(object({
      priority            = number
      allow               = optional(bool, true)
      description         = optional(string)
      enabled             = optional(bool, true)
      application_matcher = optional(string)
      session_matcher     = optional(string)
      tls_inspect         = optional(bool)
      matcher_args = optional(object({
        application = optional(list(string), [])
        session     = optional(list(string), [])
      }), {})
    })), {})
    url_lists = optional(map(object({
      values      = list(string)
      description = optional(string)
    })), {})
    tls_inspection_config = optional(object({
      create_config = optional(object({
        ca_pool               = optional(string)
        description           = optional(string)
        exclude_public_ca_set = optional(bool, false)
      }))
      id = optional(string)
    }), {})
  })
  default  = {}
  nullable = false
  validation {
    condition = (
      !var.centralized_egress.enabled || length(var.centralized_egress.ports) > 0
    )
    error_message = "centralized_egress.ports must contain at least one TCP port when centralized_egress.enabled is true."
  }
}

variable "cidrs" {
  description = "Named CIDR ranges to use in firewall policy rules."
  type        = map(list(string))
  default     = {}
  nullable    = false
}

variable "common_services_folder" {
  description = "Common services folder ID."
  type        = string
  default     = null
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
  })
  default  = {}
  nullable = false
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

variable "enable_cloud_nat" {
  description = "Enable per-VPC Cloud NAT and default internet gateway routes on the central hub VPC and environment spoke VPCs when centralized_egress.enabled is false."
  type        = bool
  default     = true
  nullable    = false
}

variable "enable_default_ncc_hub" {
  description = "Provision the default STAR-topology Network Connectivity Center hub connecting the central hub VPC (center group) and environment spoke VPCs (edge group)."
  type        = bool
  default     = true
  nullable    = false
}

variable "envs_folders" {
  description = "List of environments to be created for projects to go into."
  type = map(object({
    admin = string
  }))
}

variable "essential_contacts" {
  description = "Email or map of emails to notification category lists used for essential contacts, unset if null or empty."
  type        = any
  default     = {}
  validation {
    condition = (
      var.essential_contacts == null ||
      can(tostring(var.essential_contacts)) ||
      can({ for k, v in tomap(var.essential_contacts) : k => tolist(v) })
    )
    error_message = "essential_contacts must be null, a single email string, or a map of email strings to notification category lists."
  }
}

variable "factories_config" {
  description = "Configuration for network resource factories."
  type = object({
    data_dir              = optional(string, "data")
    dns_policy_rules_file = optional(string)
    firewall_policy_name  = optional(string)
    ncc_hubs              = optional(string)
  })
  default = {
    data_dir = "data"
  }
  nullable = false
  validation {
    condition     = var.factories_config.data_dir != null
    error_message = "Data folder needs to be non-null."
  }
}

variable "fast_features" {
  description = "FAST features enabled."
  type        = any
  default     = null
}

variable "firewall_policy_rules" {
  description = "Global network firewall policy rules keyed by VPC name (hub, egress, or environment spoke name), supporting Cloud NGFW Essentials, Standard, and Enterprise attributes."
  type = map(object({
    ingress = optional(map(object({
      priority                = number
      action                  = optional(string, "allow")
      description             = optional(string)
      disabled                = optional(bool, false)
      enable_logging          = optional(bool)
      security_profile_group  = optional(string)
      target_resources        = optional(list(string))
      target_service_accounts = optional(list(string))
      target_tags             = optional(list(string))
      tls_inspect             = optional(bool, null)
      match = object({
        address_groups       = optional(list(string))
        fqdns                = optional(list(string))
        region_codes         = optional(list(string))
        threat_intelligences = optional(list(string))
        destination_ranges   = optional(list(string))
        source_ranges        = optional(list(string))
        source_tags          = optional(list(string))
        layer4_configs = optional(list(object({
          protocol = optional(string, "all")
          ports    = optional(list(string))
        })), [{}])
      })
    })), {})
    egress = optional(map(object({
      priority                = number
      action                  = optional(string, "deny")
      description             = optional(string)
      disabled                = optional(bool, false)
      enable_logging          = optional(bool)
      security_profile_group  = optional(string)
      target_resources        = optional(list(string))
      target_service_accounts = optional(list(string))
      target_tags             = optional(list(string))
      tls_inspect             = optional(bool, null)
      match = object({
        address_groups       = optional(list(string))
        fqdns                = optional(list(string))
        region_codes         = optional(list(string))
        threat_intelligences = optional(list(string))
        destination_ranges   = optional(list(string))
        source_ranges        = optional(list(string))
        source_tags          = optional(list(string))
        layer4_configs = optional(list(object({
          protocol = optional(string, "all")
          ports    = optional(list(string))
        })), [{}])
      })
    })), {})
    ingress_mirroring = optional(map(object({
      priority               = number
      action                 = optional(string, "mirror")
      description            = optional(string)
      disabled               = optional(bool, false)
      security_profile_group = optional(string)
      target_tags            = optional(list(string))
      tls_inspect            = optional(bool, null)
      match = object({
        destination_ranges = optional(list(string))
        source_ranges      = optional(list(string))
        source_tags        = optional(list(string))
        layer4_configs = optional(list(object({
          protocol = optional(string, "all")
          ports    = optional(list(string))
        })), [{}])
      })
    })), {})
    egress_mirroring = optional(map(object({
      priority               = number
      action                 = optional(string, "mirror")
      description            = optional(string)
      disabled               = optional(bool, false)
      security_profile_group = optional(string)
      target_tags            = optional(list(string))
      tls_inspect            = optional(bool, null)
      match = object({
        destination_ranges = optional(list(string))
        source_ranges      = optional(list(string))
        source_tags        = optional(list(string))
        layer4_configs = optional(list(object({
          protocol = optional(string, "all")
          ports    = optional(list(string))
        })), [{}])
      })
    })), {})
  }))
  default  = {}
  nullable = false
  validation {
    condition = alltrue(flatten([
      for net, pol in var.firewall_policy_rules : concat(
        [
          for rk, rv in pol.ingress :
          contains(["allow", "deny", "goto_next", "apply_security_profile_group"], rv.action)
        ],
        [
          for rk, rv in pol.egress :
          contains(["allow", "deny", "goto_next", "apply_security_profile_group"], rv.action)
        ],
        [
          for rk, rv in pol.ingress_mirroring :
          contains(["mirror", "do_not_mirror", "goto_next"], rv.action)
        ],
        [
          for rk, rv in pol.egress_mirroring :
          contains(["mirror", "do_not_mirror", "goto_next"], rv.action)
        ]
      )
    ]))
    error_message = "Firewall policy rule action must be allow, deny, goto_next, or apply_security_profile_group (or mirror, do_not_mirror, goto_next for mirroring rules)."
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
    gcp_dev_primary  = "10.68.0.0/16"
    gcp_hub_primary  = "10.200.0.0/16"
    gcp_prod_primary = "10.72.0.0/16"
  }
}

variable "groups" {
  description = "IAM groups mapping."
  type        = any
  default     = null
}

variable "kms_protection_level" {
  # tfdoc:variable:source 0-bootstrap
  description = "KMS protection level."
  type        = string
  nullable    = true
  default     = null
}

variable "logging" {
  description = "Logging configuration."
  type        = any
  default     = null
}

variable "ncc_hubs" {
  description = "Network Connectivity Center hubs, groups, and spokes in hub_name => config format, merged with YAML definitions from factories_config.ncc_hubs."
  type = map(object({
    project_id      = optional(string)
    description     = optional(string)
    export_psc      = optional(bool)
    policy_mode     = optional(string)
    preset_topology = optional(string)
    labels          = optional(map(string), {})
    groups = optional(map(object({
      description = optional(string)
      labels      = optional(map(string), {})
      auto_accept = optional(list(string), [])
    })), {})
    spokes = optional(object({
      vpcs = optional(map(object({
        vpc                   = optional(string)
        name                  = optional(string)
        project_id            = optional(string)
        group                 = optional(string)
        description           = optional(string, "Terraform-managed.")
        labels                = optional(map(string), {})
        exclude_export_ranges = optional(list(string))
        include_export_ranges = optional(list(string))
      })), {})
      tunnels = optional(map(object({
        uris                       = list(string)
        name                       = optional(string)
        location                   = optional(string)
        project_id                 = optional(string)
        group                      = optional(string)
        description                = optional(string, "Terraform-managed.")
        labels                     = optional(map(string), {})
        site_to_site_data_transfer = optional(bool, false)
        include_import_ranges      = optional(list(string), ["ALL_IPV4_RANGES"])
      })), {})
      vlan_attachments = optional(map(object({
        uris                       = list(string)
        name                       = optional(string)
        location                   = optional(string)
        project_id                 = optional(string)
        group                      = optional(string)
        description                = optional(string, "Terraform-managed.")
        labels                     = optional(map(string), {})
        site_to_site_data_transfer = optional(bool, false)
        include_import_ranges      = optional(list(string), ["ALL_IPV4_RANGES"])
      })), {})
      router_appliances = optional(map(object({
        instances = list(object({
          ip_address      = string
          virtual_machine = string
        }))
        name                       = optional(string)
        location                   = optional(string)
        project_id                 = optional(string)
        group                      = optional(string)
        description                = optional(string, "Terraform-managed.")
        labels                     = optional(map(string), {})
        site_to_site_data_transfer = optional(bool, false)
        include_import_ranges      = optional(list(string), ["ALL_IPV4_RANGES"])
      })), {})
    }), {})
  }))
  default  = {}
  nullable = false
  validation {
    condition = alltrue([
      for k, v in var.ncc_hubs :
      v.policy_mode == null || contains(["CUSTOM", "PRESET"], v.policy_mode)
    ])
    error_message = "Each hub policy_mode must be null, CUSTOM, or PRESET."
  }
  validation {
    condition = alltrue([
      for k, v in var.ncc_hubs :
      v.preset_topology == null || (
        coalesce(v.policy_mode, "PRESET") == "PRESET" &&
        contains(["MESH", "STAR"], v.preset_topology)
      )
    ])
    error_message = "Each hub preset_topology must be MESH or STAR when policy_mode is PRESET, and null when policy_mode is CUSTOM."
  }
  validation {
    condition = alltrue(flatten([
      for k, v in var.ncc_hubs : [
        for gk, _ in v.groups : contains(["default", "center", "edge"], gk)
      ]
    ]))
    error_message = "Each group key in ncc_hubs must be default, center, or edge."
  }
  validation {
    condition = alltrue(flatten([
      for k, v in var.ncc_hubs : [
        for sk, sv in v.spokes.router_appliances : length(sv.instances) > 0
      ]
    ]))
    error_message = "Each router_appliances spoke must specify at least one instance."
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

variable "proxy_subnets" {
  description = "VPC proxy-only subnet CIDRs keyed by environment. One entry per key of envs_folders is required: every environment spoke gets a proxy-only subnet in regions.primary."
  type        = map(string)
  default     = {}
  nullable    = false
  validation {
    condition = alltrue([
      for k in keys(var.envs_folders) : contains(keys(var.proxy_subnets), k)
    ])
    error_message = "proxy_subnets needs an entry for every key of envs_folders (keys are case-sensitive and match envs_folders, not their lower-cased form): each environment spoke is created with a proxy-only subnet whose CIDR comes from this map."
  }
}

variable "psa_ranges" {
  description = "Optional Private Services Access (PSA) IP ranges keyed by environment name (for example prod, int, or test) for services that do not use Private Service Connect."
  type = map(list(object({
    deletion_policy  = optional(string)
    ranges           = map(string)
    labels           = optional(map(string), {})
    export_routes    = optional(bool, false)
    import_routes    = optional(bool, false)
    peered_domains   = optional(list(string), [])
    range_prefix     = optional(string)
    service_producer = optional(string, "servicenetworking.googleapis.com")
  })))
  nullable = false
  default  = {}
}

variable "psc_google_apis" {
  description = "Private Service Connect endpoints for Google APIs created in the central hub VPC, environment spoke VPCs, and optional centralized egress VPC."
  type = object({
    enabled   = optional(bool, true)
    bundle    = optional(string, "all-apis")
    hub_ip    = optional(string, "10.255.255.1")
    egress_ip = optional(string, "10.255.255.2")
    spoke_ips = optional(map(string), {})
    service_directory_registration = optional(object({
      namespace = optional(string)
      region    = optional(string)
    }))
  })
  default  = {}
  nullable = false
  validation {
    condition     = contains(["all-apis", "vpc-sc"], var.psc_google_apis.bundle)
    error_message = "psc_google_apis.bundle must be all-apis or vpc-sc."
  }
}

variable "regime_mapping" {
  description = "Compliance regime shorthand mapping."
  type        = any
  default     = null
}

variable "regions" {
  # tfdoc:variable:source 0-bootstrap
  description = "Region definitions. Inherited from 0-bootstrap outputs. Must be specified in bootstrap terraform.tfvars."
  type = object({
    primary = string
  })
  nullable = false
}

variable "security_profile_group_ids" {
  description = "Optional Cloud NGFW Enterprise security profile group IDs in logical_key => //networksecurity.googleapis.com/<id> format."
  type        = map(string)
  default     = {}
  nullable    = false
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

variable "spoke_project_iam" {
  description = "Additional authoritative IAM bindings for environment spoke host projects, keyed by environment name (for example dev or prod) and role."
  type        = map(map(list(string)))
  default     = {}
  nullable    = false
}

variable "subnets" {
  description = "VPC subnet configurations keyed by network name."
  type = map(list(object({
    name                             = string
    ip_cidr_range                    = optional(string)
    region                           = string
    description                      = optional(string)
    enable_private_access            = optional(bool, true)
    allow_subnet_cidr_routes_overlap = optional(bool)
    reserved_internal_range          = optional(string)
    flow_logs_config = optional(object({
      aggregation_interval = optional(string)
      filter_expression    = optional(string)
      flow_sampling        = optional(number)
      metadata             = optional(string)
      metadata_fields      = optional(list(string))
    }))
    secondary_ip_ranges = optional(map(object({
      ip_cidr_range           = optional(string)
      reserved_internal_range = optional(string)
    })))
    iam    = optional(map(list(string)), {})
    tenant = optional(string)
  })))
  default  = {}
  nullable = false
  validation {
    condition = alltrue([
      for k in keys(var.envs_folders) :
      try([for s in var.subnets[lower(k)] : s if s.tenant != null][0].region, null) == var.regions.primary
    ])
    error_message = "Every environment in envs_folders needs a subnet list under subnets[lower(<env>)] whose first subnet with a non-null tenant is in regions.primary: the connectivity-test addresses and the stage outputs index that subnet."
  }
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
