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
# defaults for variables marked with global tfdoc annotations, can be set via
# the tfvars file generated in stage 00 and stored in its outputs

variable "alert_email" {
  description = "Email to receive log alerts."
  type        = string
}

variable "automation" {
  # tfdoc:variable:source 1-assured-workload
  description = "Automation resources created by the bootstrap stage."
  type = object({
    inputs_bucket           = string
    outputs_bucket          = string
    project_id              = string
    project_number          = string
    federated_identity_pool = string
    federated_identity_providers = map(object({
      audiences        = list(string)
      issuer           = string
      issuer_uri       = string
      name             = string
      principal_branch = string
      principal_repo   = string
    }))
    service_accounts = object({
      resman   = string
      resman-r = string
      tenant   = string
    })
    tenant_bucket = string
  })
}

variable "cicd" {
  description = "Optional CICD variables to add Workload Identity Federation and a GitLab provider."
  type = object({
    gitlab_project_path = string
    gitlab_uri          = string
    jwks_json           = optional(string)
  })
}

variable "edge_group_id" {
  description = "ID of the edge group created in stage 3 for the spoke to join."
  type        = string
}

variable "hub_id" {
  description = "ID of the hub created in stage 3 so we can add spokes to it."
  type        = string
}

variable "ilb_ips" {
  description = "ILB IP addresses for each environment."
  type = object({
    transit = string
  })
}


variable "locations" {
  # tfdoc:variable:source 1-assured-workload
  description = "Optional locations for GCS, BigQuery, and logging buckets created here."
  type = object({
    bq      = string
    gcs     = list(string)
    logging = list(string)
    pubsub  = list(string)
    kms     = list(string)
  })
  default = {
    bq      = "US"
    gcs     = ["US"]
    kms     = ["nam9"]
    logging = ["us"]
    pubsub  = []
  }
  nullable = false
}

variable "logging" {
  # tfdoc:variables:source 1-assured-workload
  description = "Logging resources created by the bootstrap stage."
  type = object({
    project_id        = string
    project_number    = string
    writer_identities = optional(map(string))
    pubsub_topics     = optional(map(string))
    service_accounts = object({
      c5isr-pubsub = string
    })
  })
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
  description = "Enable writing provider, tfvars and CI/CD workflow files to local filesystem. Leave null to disable."
  type        = string
  default     = null
}

variable "prefix" {
  # tfdoc:variable:source 1-assured-workload
  description = "Prefix used for resources that need unique names. Use 7 characters or less."
  type        = string

  validation {
    condition     = try(length(var.prefix), 0) <= 10
    error_message = "Use a maximum of 7 characters for prefix."
  }
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

variable "tenant" {
  description = "Lightweight tenant definition for a single environment."
  type = object({
    name                 = string
    macom                = string
    admin_principal      = string
    size                 = string
    tenant_specific_envs = list(string)
    compliance = optional(object({
      regime   = string
      location = string
    }))
    locations = optional(object({
      gcs = string
      kms = string
    }))
    organization = optional(object({
      customer_id = string
      domain      = string
      id          = number
    }))
    spoke_subnets = object({
      dev  = string
      test = string
      prod = string
    })
    tenant_groups = optional(map(object({
      roles = list(string)
    })))
    deploy_network_project = optional(bool)
  })
  nullable = false

  validation {
    condition     = length(var.tenant.name) < 8
    error_message = "Tenant keys must be less than 8 characters."
  }
  validation {
    condition     = length(var.tenant.macom) < 8
    error_message = "Macom name must be less than 8 characters."
  }
}

variable "tenant_config" {
  description = "Lightweight tenants shared configuration. Roles will be assigned to tenant admin group and service accounts."
  type = object({
    core_folder_roles   = optional(list(string), [])
    tenant_folder_roles = optional(list(string), [])
    top_folder_roles    = optional(list(string), [])
  })
  nullable = false
  default  = {}
}

variable "tenants_folder_id" {
  description = "The Overarching Tenant Folder inside of Dev."
  type        = string
}
