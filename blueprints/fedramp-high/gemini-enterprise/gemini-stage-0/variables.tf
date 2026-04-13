/**
 * Copyright 2025 Google LLC
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

variable "environment" {
  description = "The environment identifier (e.g. prod, dev, staging)."
  type        = string
}

variable "tenant" {
  description = "The tenant identifier (e.g. g4g)."
  type        = string
}

variable "compliance_regime" {
  description = "Compliance regime this environment is deployed in (e.g. FEDRAMP_HIGH, IL4, IL5, NONE)."
  type        = string
  default     = "NONE"
}

variable "kms_project_id" {
  description = "The Project ID where CMEK keys are stored."
  type        = string
}

variable "us_keyring_name" {
  description = "The name of the US Multi-Region KeyRing (if existing). If empty, one will be created."
  type        = string
  default     = ""
}

variable "domain" {
  description = "FQDN for the load-balancer hosted apps, where the subdomain will be prepended to."
  type        = string
}

variable "main_project_id" {
  description = "The GCP Project name."
  type        = string
}

variable "prefix" {
  description = "Prefix for naming resources in this blueprint."
  type        = string
  default     = "cnap"
}

variable "access_policy_number" {
  description = "There can only be one Access Policy per GCP Org. Use gcloud access-context-manager policies list --organization <org-number> to list it."
  type        = number
}

variable "admin_group" {
  description = "The email address of the admin user group for Gemini Enterprise."
  type        = string
}

variable "user_groups" {
  description = "A list of email addresses or principal sets for the Gemini Enterprise users group."
  type        = list(string)
}

variable "gemini_enterprise_gcs_bucket_name" {
  description = "The name of the GCS bucket to be used as the data source for the Discovery Engine Data Connector."
  type        = string
  default     = "your-bucket-name-placeholder"
}

variable "geolocation" {
  description = "Location for Discovery Engine resources (us, eu, or global)."
  type        = string
  default     = "us"
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "allowed_ip_ranges" {
  description = "The IP range to allow traffic from."
  type        = list(string)
  default     = []
}

variable "access_start_hour" {
  description = "The hour (0-23) in America/New_York timezone when access starts."
  type        = number
  default     = 7
}

variable "access_end_hour" {
  description = "The hour (0-23) in America/New_York timezone when access ends."
  type        = number
  default     = 21
}

variable "access_start_day" {
  description = "The day of the week when access starts (1 for Monday, 7 for Sunday)."
  type        = number
  default     = 1
}

variable "access_end_day" {
  description = "The day of the week when access ends (1 for Monday, 7 for Sunday)."
  type        = number
  default     = 5
}

variable "access_time_zone" {
  description = "The timezone for time-based access controls (e.g. America/New_York)."
  type        = string
  default     = "America/New_York"
}

variable "access_expiration_timestamp" {
  description = "The timestamp when access expires (RFC 3339 format, e.g. 2028-01-01T00:00:00Z)."
  type        = string
  default     = "2028-01-01T00:00:00Z"
}

variable "kms_key_id" {
  description = "The full resource name of the Cloud KMS key to use for CMEK (e.g. projects/p/locations/l/keyRings/r/cryptoKeys/k). If not provided, a new key will be created."
  type        = string
  default     = null
}

variable "deployment_type" {
  description = "Type of deployment: 'internal', 'external', or 'none'"
  type        = string
  default     = "external" # Default to external as per original design
  validation {
    condition     = contains(["internal", "external", "none"], var.deployment_type)
    error_message = "Allowed values for deployment_type are 'internal', 'external', or 'none'."
  }
}

variable "cert_management_choice" {
  description = "Certificate management choice for external deployments: 'google_managed' or 'self_managed'."
  type        = string
  default     = "self_managed"
  validation {
    condition     = contains(["google_managed", "self_managed"], var.cert_management_choice)
    error_message = "Allowed values for cert_management_choice are 'google_managed' or 'self_managed'."
  }
}

variable "custom_domain" {
  description = "The fully qualified domain name (FQDN) to use for the Google-managed certificate."
  type        = string
  default     = ""
}

variable "create_ip_based_access" {
  description = "Whether to create the IP-based access level."
  type        = bool
  default     = true
}

variable "create_us_access" {
  description = "Whether to create the US-only access level."
  type        = bool
  default     = true
}

variable "create_time_access" {
  description = "Whether to create the Time-based access level."
  type        = bool
  default     = true
}

variable "create_expire_access" {
  description = "Whether to create the Expiration access level."
  type        = bool
  default     = true
}

variable "create_lenient_device_access" {
  description = "Whether to create the Lenient device access level."
  type        = bool
  default     = true
}

variable "create_moderate_device_access" {
  description = "Whether to create the Moderate device access level."
  type        = bool
  default     = true
}

variable "create_strict_device_access" {
  description = "Whether to create the Strict device access level."
  type        = bool
  default     = true
}

variable "create_data_stores" {
  description = "Whether to create example Data Stores (BigQuery, GCS) and associated CMEK config."
  type        = bool
  default     = true
}

variable "acl_idp_type" {
  description = "The Identity Provider type for Discovery Engine ACLs. Options: 'GSUITE', 'THIRD_PARTY', 'GOOGLE_CLOUD_IDENTITY'."
  type        = string
  default     = "GOOGLE_CLOUD_IDENTITY"
  validation {
    condition     = contains(["GSUITE", "THIRD_PARTY", "GOOGLE_CLOUD_IDENTITY"], var.acl_idp_type)
    error_message = "The acl_idp_type value must be either 'GSUITE', 'THIRD_PARTY', or 'GOOGLE_CLOUD_IDENTITY'."
  }
}

variable "acl_workforce_pool_name" {
  description = "The resource name of the Workforce Identity Pool (required if acl_idp_type is 'THIRD_PARTY'). Format: locations/global/workforcePools/<pool_id>"
  type        = string
  default     = ""
}

variable "acl_workforce_provider_id" {
  description = "The ID of the Workforce Identity Pool Provider (required if acl_idp_type is 'THIRD_PARTY'). Format: <provider_id> (without acl_workforce_pool_name prefix)"
  type        = string
  default     = ""
}

variable "enable_chrome_enterprise_premium" {
  description = "Enable Chrome Enterprise Premium features (e.g., Zero Trust)."
  type        = bool
  default     = false
}

variable "terraform_state_bucket" {
  description = "The name of the Terraform state bucket. If not provided, it will be constructed from prefix and project ID."
  type        = string
  default     = null
}

variable "use_shared_vpc" {
  description = "Whether to use an existing Shared VPC instead of creating a new one."
  type        = bool
  default     = false
}

variable "network_project_id" {
  description = "The Project ID where the Shared VPC resides (Host Project). Required if use_shared_vpc is true."
  type        = string
  default     = ""
}

variable "shared_vpc_network_name" {
  description = "The name of the existing Shared VPC network. Required if use_shared_vpc is true."
  type        = string
  default     = ""
}

variable "shared_vpc_subnet_name" {
  description = "The name of the existing subnetwork to use. Required if use_shared_vpc is true."
  type        = string
  default     = ""
}

variable "shared_vpc_proxy_subnet_name" {
  description = "The name of the existing proxy-only subnetwork to use. Required if use_shared_vpc is true."
  type        = string
  default     = ""
}

variable "gcs_data_store_configs" {
  description = "A map of configurations for Google Cloud Storage (GCS) Data Stores. If create_bucket is true, the script will create the bucket."
  type = map(object({
    name          = string
    create_bucket = bool
    display_name  = optional(string)
  }))
  default = {}
}

variable "bq_data_store_configs" {
  description = "A map of configurations for BigQuery Data Stores. If create_dataset is true, it creates the dataset. Schema provides the structure for the data."
  type = map(object({
    dataset_id     = string
    table_id       = string
    create_dataset = bool
    schema         = optional(string)
    display_name   = optional(string)
  }))
  default = {}
}


variable "internal_lb_subnet_range" {
  description = "The IP CIDR range for the internal load balancer subnet."
  type        = string
  default     = "10.10.10.0/24"
}

variable "lenient_device_access_levels" {
  description = "List of Access Levels to include in the Lenient Device Policy."
  type        = list(string)
  default     = []
}

variable "moderate_device_access_levels" {
  description = "List of Access Levels to include in the Moderate Device Policy."
  type        = list(string)
  default     = []
}

variable "enable_data_store_cmek" {
  description = "Whether to encrypt Data Stores with CMEK. If false, Google-managed keys will be used."
  type        = bool
  default     = true
}

variable "enable_analytics" {
  description = "Enable analytics for Gemini Enterprise via Discovery Engine Audit Logs."
  type        = bool
  default     = false
}
