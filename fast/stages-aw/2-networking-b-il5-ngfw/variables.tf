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

variable "cidrs" {
  description = "Named CIDR ranges to use in firewall rules."
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
  # tfdoc:variable:source 0-bootstrap
  description = "Custom roles defined at the org level, in key => id format."
  type = object({
    service_project_network_admin = string
  })
  default = null
}

variable "dns" {
  description = "DNS configuration."
  type = object({
    enable_logging = optional(bool, true)
    resolvers      = optional(list(string), [])
  })
  default  = {}
  nullable = false
}

variable "dns_forwarding_zones" {
  description = "Optional hybrid Cloud DNS forwarding zones created in the VDSS host project, keyed by zone name suffix. Root domain '.' is forbidden because it breaks Compute Engine internal DNS."
  type = map(object({
    domain          = string
    forwarders      = map(string)
    description     = optional(string, "Terraform-managed hybrid forwarding zone.")
    client_networks = optional(list(string))
  }))
  default  = {}
  nullable = false
  validation {
    condition = alltrue([
      for k, v in var.dns_forwarding_zones :
      trimspace(v.domain) != "." &&
      endswith(v.domain, ".") &&
      length(trimspace(v.domain)) > 1
    ])
    error_message = "Each dns_forwarding_zones domain must end with '.' and must not be the root zone '.'."
  }
  validation {
    condition = alltrue([
      for k, v in var.dns_forwarding_zones : length(v.forwarders) > 0
    ])
    error_message = "Each dns_forwarding_zones entry must specify at least one forwarder IPv4 address."
  }
  validation {
    condition = alltrue(flatten([
      for k, v in var.dns_forwarding_zones : [
        for ip, path in v.forwarders :
        can(cidrhost("${ip}/32", 0)) && contains(["default", "private"], path)
      ]
    ]))
    error_message = "Each dns_forwarding_zones forwarder key must be a valid IPv4 address with a forwarding_path of default or private."
  }
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
    dns_policy_rules_file = optional(string, "data/dns-policy-rules.yaml")
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

variable "folder_ids" {
  # tfdoc:variable:source 1-resman
  description = "Folders to be used for the networking resources in folders/nnnnnnnnnnn format. If null, folder will be created."
  type = object({
    networking = string
    envs       = optional(map(string))
  })
}

variable "force_destroy" {
  description = "Toggles force_destroy for GCS buckets."
  type        = bool
  default     = false
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
        for gk, gv in v.groups : [
          for p in gv.auto_accept : trimspace(p) != "*"
        ]
      ]
    ]))
    error_message = "NCC group auto_accept must list explicit project IDs and cannot contain wildcard '*'."
  }
  validation {
    condition = alltrue(flatten([
      for k, v in var.ncc_hubs : [
        for sk, sv in v.spokes.vpcs : (
          !contains(
            [
              "mgmt", "mgmt-vpc", "vdss-mgmt-0",
              "$vpcs:mgmt", "$networks:mgmt"
            ],
            lower(coalesce(sv.vpc, sk))
          ) &&
          !endswith(lower(coalesce(sv.vpc, sk)), "/networks/vdss-mgmt-0")
        )
      ]
    ]))
    error_message = "Management VPC (mgmt-vpc / vdss-mgmt-0) must never be attached to a data-plane NCC hub."
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

variable "ngfw_admin_password_secret" {
  description = "Optional regional CMEK-encrypted Secret Manager secret storing the NGFW administrator password using write-only secret versions. When enabled, the legacy ngfw_password output returns null."
  type = object({
    enabled          = optional(bool, false)
    secret_id        = optional(string, "ngfw-admin-password")
    wo_version       = optional(number, 1)
    accessor_members = optional(list(string), [])
    deletion_policy  = optional(string, "DELETE")
  })
  default  = {}
  nullable = false
  validation {
    condition     = var.ngfw_admin_password_secret.wo_version >= 1
    error_message = "ngfw_admin_password_secret.wo_version must be at least 1."
  }
  validation {
    condition = contains(
      ["DELETE", "DISABLE", "ABANDON"],
      var.ngfw_admin_password_secret.deletion_policy
    )
    error_message = "ngfw_admin_password_secret.deletion_policy must be DELETE, DISABLE, or ABANDON."
  }
  validation {
    condition     = trimspace(var.ngfw_admin_password_secret.secret_id) != ""
    error_message = "ngfw_admin_password_secret.secret_id must be non-empty."
  }
}

variable "ngfw_health_check" {
  description = "Health check configuration for NGFW managed instance groups and internal load balancers. Defaults to TCP port 22 for backward compatibility; set protocol to HTTPS with port 443 and request_path /unauth/php/health.php for dataplane health probing after adding TCP/443 health check firewall rules on landing and dmz."
  type = object({
    protocol            = optional(string, "TCP")
    port                = optional(number)
    request_path        = optional(string, "/unauth/php/health.php")
    check_interval_sec  = optional(number)
    timeout_sec         = optional(number)
    healthy_threshold   = optional(number)
    unhealthy_threshold = optional(number)
    enable_logging      = optional(bool)
    is_regional         = optional(bool, false)
  })
  default  = {}
  nullable = false
  validation {
    condition     = contains(["TCP", "HTTPS", "HTTP"], var.ngfw_health_check.protocol)
    error_message = "ngfw_health_check.protocol must be TCP, HTTPS, or HTTP."
  }
  validation {
    condition = (
      var.ngfw_health_check.port == null ||
      (var.ngfw_health_check.port >= 1 && var.ngfw_health_check.port <= 65535)
    )
    error_message = "ngfw_health_check.port must be between 1 and 65535."
  }
  validation {
    condition = (
      var.ngfw_health_check.protocol == "TCP" ||
      startswith(coalesce(var.ngfw_health_check.request_path, ""), "/")
    )
    error_message = "ngfw_health_check.request_path must start with '/' for HTTP and HTTPS health checks."
  }
}

variable "ngfw_ilb_config" {
  description = "Optional internal passthrough load balancer hardening and static VIP configuration for the NGFW trusted landing and untrusted DMZ frontends."
  type = object({
    connection_draining_timeout_sec = optional(number)
    failover_config = optional(object({
      disable_conn_drain        = optional(bool)
      drop_traffic_if_unhealthy = optional(bool)
      ratio                     = optional(number)
    }))
    idle_timeout_sec          = optional(number)
    persist_conn_on_unhealthy = optional(string)
    session_affinity          = optional(string)
    track_per_session         = optional(bool)
    trusted_static_ips        = optional(map(string), {})
    untrusted_static_ips      = optional(map(string), {})
  })
  default  = {}
  nullable = false
  validation {
    condition = (
      var.ngfw_ilb_config.persist_conn_on_unhealthy == null ||
      contains(
        ["DEFAULT_FOR_PROTOCOL", "NEVER_PERSIST", "ALWAYS_PERSIST"],
        var.ngfw_ilb_config.persist_conn_on_unhealthy
      )
    )
    error_message = "ngfw_ilb_config.persist_conn_on_unhealthy must be DEFAULT_FOR_PROTOCOL, NEVER_PERSIST, or ALWAYS_PERSIST."
  }
  validation {
    condition = alltrue(concat(
      [for _, ip in var.ngfw_ilb_config.trusted_static_ips : can(cidrhost("${ip}/32", 0))],
      [for _, ip in var.ngfw_ilb_config.untrusted_static_ips : can(cidrhost("${ip}/32", 0))]
    ))
    error_message = "ngfw_ilb_config trusted_static_ips and untrusted_static_ips must be valid IPv4 addresses."
  }
}

variable "ngfw_stig_config" {
  description = "Optional DISA STIG hardening settings for the Palo Alto NGFW bootstrap XML template. Leave null to keep legacy defaults. FIPS-CC mode requires post-boot CLI or MRT activation rather than bootstrap files."
  type = object({
    login_banner        = optional(string)
    min_password_length = optional(number, 16)
    timezone            = optional(string, "UTC")
  })
  default = null
  validation {
    condition = (
      var.ngfw_stig_config == null ||
      var.ngfw_stig_config.min_password_length >= 16
    )
    error_message = "ngfw_stig_config.min_password_length must be at least 16."
  }
  validation {
    condition = (
      var.ngfw_stig_config == null ||
      trimspace(var.ngfw_stig_config.timezone) != ""
    )
    error_message = "ngfw_stig_config.timezone must be a non-empty timezone string."
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
  description = "VPC proxy-only subnet CIDRs keyed by environment."
  type        = map(string)
  default     = {}
  nullable    = false
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

variable "psc_google_apis" {
  description = "Optional per-VPC Private Service Connect endpoints for Google APIs created in the landing hub VPC and environment spoke VPCs. Defaults Service Directory registration to regions.primary when service_directory_registration or its region is unset."
  type = object({
    enabled   = optional(bool, false)
    bundle    = optional(string, "vpc-sc")
    hub_ip    = optional(string, "10.255.255.1")
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
  validation {
    condition = (
      can(cidrhost("${var.psc_google_apis.hub_ip}/32", 0)) &&
      alltrue([
        for _, ip in var.psc_google_apis.spoke_ips :
        can(cidrhost("${ip}/32", 0))
      ])
    )
    error_message = "psc_google_apis hub_ip and spoke_ips must be valid IPv4 addresses."
  }
  validation {
    condition = (
      !var.psc_google_apis.enabled ||
      length(distinct([
        for k in keys(var.envs_folders) :
        substr("psc${replace(lower(k), "/[^a-z0-9]/", "")}0", 0, 20)
      ])) == length(keys(var.envs_folders))
    )
    error_message = "psc_google_apis.enabled requires envs_folders keys to produce unique 20-character PSC forwarding rule names."
  }
}

variable "regime_mapping" {
  description = "Compliance regime shorthand mapping."
  type        = any
  default     = null
}

variable "regions" {
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
    condition = alltrue(flatten([
      for net in ["landing", "dmz", "mgmt"] : [
        for r in values(var.regions) :
        contains([
          for s in try(var.subnets[net], []) :
          s.region if s.name == "${net}-default"
        ], r)
      ]
    ]))
    error_message = "subnets.landing, dmz and mgmt need a <net>-default subnet in every region."
  }
  validation {
    condition = alltrue([
      for k in keys(var.envs_folders) :
      try([
        for s in var.subnets[lower(k)] : s if s.tenant != null
      ][0].region, null) == var.regions.primary
    ])
    error_message = "The first tenant subnet of each environment must be in regions.primary."
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

variable "transit_mode" {
  description = "Spoke-to-landing transit mode: peering for classic VPC peering or ncc for Network Connectivity Center."
  type        = string
  default     = "peering"
  nullable    = false
  validation {
    condition     = contains(["peering", "ncc"], var.transit_mode)
    error_message = "transit_mode must be peering or ncc."
  }
}

# To get a list of available official images, please run the following command:
# `gcloud compute images list --filter="family ~ vmseries" --project paloaltonetworksgcp-public --no-standard-images`

variable "vmseries_image" {
  description = "The image name from which to boot an instance, including a license type (bundle/flex) and version."
  default     = "vmseries-112"
  type        = string
}
