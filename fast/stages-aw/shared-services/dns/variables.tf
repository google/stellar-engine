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

variable "automation" {
  description = "Automation resources created by the bootstrap stage."
  type = object({
    outputs_bucket = string
  })
}

variable "dns_policy_rules_file" {
  description = "Path to the YAML file containing DNS response policy rules for Private Google Access (googleapis.com, gcr.io, etc.). If set, a response policy is created for the shared-services VPC."
  type        = string
  default     = null
}

variable "forwarding_zones" {
  description = "DNS forwarding zones keyed by name. Each zone forwards queries for the specified domain to the given forwarder IPs via the cross-cloud VPN tunnel. Use domain-specific zones (e.g. 'mil.', 'Enterprise.mil.') — root domain '.' breaks Compute Engine internal DNS."
  type = map(object({
    domain     = string
    forwarders = map(string)
  }))
  default = {}
  validation {
    condition = alltrue([
      for k, v in var.forwarding_zones : v.domain != "."
    ])
    error_message = "Root domain '.' forwarding zones break Compute Engine internal DNS. Use domain-specific zones instead (e.g. 'mil.', 'Enterprise.mil.')."
  }
}

variable "host_project_id" {
  description = "The GCP project ID where DNS zones will be created (the VDSS host project that owns the VPCs)."
  type        = string
}

variable "prefix" {
  description = "Prefix applied to resource names for org-level naming consistency (e.g. 'da1'). Set to null to disable prefixing."
  type        = string
  default     = null
  validation {
    condition     = var.prefix != ""
    error_message = "Prefix cannot be empty, use null instead."
  }
}

variable "private_zone_domain" {
  description = "Domain of the existing private DNS zone in the landing VPC (e.g. 'da1-il5-vdss.private.example.internal.'). A peering zone is created so shared-services and tenant-transit VPCs can resolve records in it."
  type        = string
  default     = null
}

variable "vpc_self_links" {
  description = "VPC self-links used for DNS zone authorization and peering."
  type = object({
    csp_landing     = string
    landing         = string
    shared_services = string
    tenant_transit  = string
  })
}
