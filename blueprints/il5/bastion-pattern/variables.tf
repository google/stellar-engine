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

variable "access_mode" {
  description = "Ingress access mode for bastion hosts. Allowed values are 'iap' for Identity-Aware Proxy tunneling and 'bcap' for private DoD Boundary Cloud Access Point source ranges."
  type        = string
  default     = "iap"
  nullable    = false
  validation {
    condition     = contains(["iap", "bcap"], var.access_mode)
    error_message = "access_mode must be either 'iap' or 'bcap'."
  }
}

variable "additional_bastions" {
  description = "Optional map of additional multi-role or per-tenant bastion hosts. Each entry provisions a dedicated service account, SA-targeted logged firewall rule, and hardened Confidential Compute VM."
  type = map(object({
    access_mode                = optional(string)
    allowed_firewall_ports     = optional(list(string))
    allowed_source_ranges      = optional(list(string))
    compute_service_account_id = string
    disk_name                  = optional(string)
    enable_observability_iam   = optional(bool)
    firewall_name              = optional(string)
    image                      = optional(string)
    instance_name              = optional(string)
    instance_type              = optional(string)
    static_internal_ip         = optional(string)
    subnetwork_name            = optional(string)
    zone                       = optional(string)
  }))
  default  = {}
  nullable = false
  validation {
    condition = alltrue([
      for k, v in var.additional_bastions :
      v.access_mode == null || contains(["iap", "bcap"], v.access_mode)
    ])
    error_message = "Each additional bastion access_mode must be 'iap' or 'bcap' when specified."
  }
  validation {
    condition = alltrue([
      for k, v in var.additional_bastions :
      v.allowed_source_ranges == null ? true : (
        length(v.allowed_source_ranges) > 0 && alltrue([
          for r in v.allowed_source_ranges :
          can(cidrhost(r, 0)) ? tonumber(split("/", r)[1]) >= 8 : false
        ])
      )
    ])
    error_message = "Each additional bastion allowed_source_ranges must be non-empty, contain valid CIDRs with prefix length >= 8, and exclude blanket ranges."
  }
  validation {
    condition = alltrue([
      for k, v in var.additional_bastions : (
        coalesce(v.access_mode, var.access_mode) != "bcap" || alltrue([
          for r in(
            v.allowed_source_ranges != null
            ? v.allowed_source_ranges
            : var.allowed_source_ranges
            ) : (
            can(cidrnetmask(r)) ? (
              (
                tonumber(split(".", cidrhost(r, 0))[0]) * 16777216 +
                tonumber(split(".", cidrhost(r, 0))[1]) * 65536 +
                tonumber(split(".", cidrhost(r, 0))[2]) * 256 +
                tonumber(split(".", cidrhost(r, 0))[3])
              ) > 602669055 ||
              (
                tonumber(split(".", cidrhost(r, -1))[0]) * 16777216 +
                tonumber(split(".", cidrhost(r, -1))[1]) * 65536 +
                tonumber(split(".", cidrhost(r, -1))[2]) * 256 +
                tonumber(split(".", cidrhost(r, -1))[3])
              ) < 602664960
            ) : true
          )
        ])
      )
    ])
    error_message = "When an additional bastion uses access_mode 'bcap', its effective allowed_source_ranges must not overlap the IAP range 35.235.240.0/20."
  }
  validation {
    condition = alltrue([
      for k, v in var.additional_bastions :
      v.static_internal_ip == null ? true : (
        can(cidrnetmask("${v.static_internal_ip}/32"))
        ? cidrhost("${v.static_internal_ip}/32", 0) == v.static_internal_ip
        : false
      )
    ])
    error_message = "Each additional bastion static_internal_ip must be a valid IPv4 address."
  }
  validation {
    condition = alltrue([
      for k, v in var.additional_bastions :
      startswith(coalesce(v.zone, var.zone), "${var.region}-")
    ])
    error_message = "Each additional bastion zone must be located within region."
  }
  validation {
    condition = length(distinct(concat(
      [var.instance_name],
      [for k, v in var.additional_bastions : coalesce(v.instance_name, k)]
    ))) == length(var.additional_bastions) + 1
    error_message = "All bastion instance names must be unique across instance_name and additional_bastions."
  }
  validation {
    condition = length(distinct(concat(
      [var.compute_service_account_id],
      [for k, v in var.additional_bastions : v.compute_service_account_id]
    ))) == length(var.additional_bastions) + 1
    error_message = "All bastion service account IDs must be unique across compute_service_account_id and additional_bastions."
  }
  validation {
    condition = length(distinct(concat(
      ["allow-web"],
      [
        for k, v in var.additional_bastions :
        coalesce(v.firewall_name, "allow-bastion-${k}")
      ]
    ))) == length(var.additional_bastions) + 1
    error_message = "All bastion firewall names must be unique and must not collide with 'allow-web'."
  }
  validation {
    condition = length(distinct(compact(concat(
      [
        var.static_internal_ip == null
        ? ""
        : format("%s/%s", var.subnetwork_name, var.static_internal_ip)
      ],
      [
        for k, v in var.additional_bastions :
        v.static_internal_ip == null
        ? ""
        : format(
          "%s/%s",
          coalesce(v.subnetwork_name, var.subnetwork_name),
          v.static_internal_ip
        )
      ]
      )))) == length(compact(concat(
      [var.static_internal_ip == null ? "" : var.static_internal_ip],
      [
        for k, v in var.additional_bastions :
        v.static_internal_ip == null ? "" : v.static_internal_ip
      ]
    )))
    error_message = "Static internal IP addresses must be unique within the same subnetwork across primary and additional bastions."
  }
}

variable "allowed_firewall_ports" {
  description = "The allowed ports for the firewall."
  type        = list(string)
}

variable "allowed_source_ranges" {
  description = "Allowed ingress CIDR ranges for the primary bastion firewall rule. Must be non-empty, use prefix length >= 8, and not overlap the IAP range 35.235.240.0/20 when access_mode is 'bcap'."
  type        = list(string)
  nullable    = false
  validation {
    condition     = length(var.allowed_source_ranges) > 0
    error_message = "allowed_source_ranges must contain at least one CIDR range."
  }
  validation {
    condition = alltrue([
      for r in var.allowed_source_ranges :
      can(cidrhost(r, 0)) ? tonumber(split("/", r)[1]) >= 8 : false
    ])
    error_message = "allowed_source_ranges must contain valid CIDR ranges with prefix length >= 8 (blocking 0.0.0.0/0, 0.0.0.0/1, ::/0, and ::/1)."
  }
  validation {
    condition = (
      var.access_mode != "bcap" || alltrue([
        for r in var.allowed_source_ranges : (
          can(cidrnetmask(r)) ? (
            (
              tonumber(split(".", cidrhost(r, 0))[0]) * 16777216 +
              tonumber(split(".", cidrhost(r, 0))[1]) * 65536 +
              tonumber(split(".", cidrhost(r, 0))[2]) * 256 +
              tonumber(split(".", cidrhost(r, 0))[3])
            ) > 602669055 ||
            (
              tonumber(split(".", cidrhost(r, -1))[0]) * 16777216 +
              tonumber(split(".", cidrhost(r, -1))[1]) * 65536 +
              tonumber(split(".", cidrhost(r, -1))[2]) * 256 +
              tonumber(split(".", cidrhost(r, -1))[3])
            ) < 602664960
          ) : true
        )
      ])
    )
    error_message = "When access_mode is 'bcap', allowed_source_ranges must use explicit BCAP CIDR ranges and must not overlap the IAP range 35.235.240.0/20."
  }
}

variable "compute_service_account_id" {
  description = "This is the compute service account id."
  type        = string
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "disk_name" {
  description = "This is the disk name."
  type        = string
}

variable "enable_observability_iam" {
  description = "Grant roles/logging.logWriter and roles/monitoring.metricWriter on main_project_id to bastion service accounts."
  type        = bool
  default     = true
  nullable    = false
}

variable "image" {
  description = "Disk image."
  type        = string
  default     = "cos-cloud/cos-stable"
}

variable "instance_name" {
  description = "This is the instance name."
  type        = string
}

variable "instance_type" {
  description = "Instance type."
  type        = string
  default     = "n2d-standard-2"
}

variable "kms_key_name" {
  description = "Short name of the existing KMS crypto key (for example `my-key`) used for disk encryption, not the full resource path. It is looked up in the key ring named by `kms_keyring_name`."
  type        = string
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type        = string
}

variable "main_project_id" {
  description = "This is the ID of project."
  type        = string
}

variable "network_name" {
  description = "VPC to use."
  type        = string
}

variable "network_project_id" {
  description = "Project that the Compute Engine VPC is located."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "static_internal_ip" {
  description = "Optional static internal IPv4 address assigned to the primary bastion VM network interface."
  type        = string
  default     = null
  validation {
    condition = (
      var.static_internal_ip == null ? true : (
        can(cidrnetmask("${var.static_internal_ip}/32"))
        ? cidrhost("${var.static_internal_ip}/32", 0) == var.static_internal_ip
        : false
      )
    )
    error_message = "static_internal_ip must be a valid IPv4 address."
  }
}

variable "subnetwork_name" {
  description = "Subnet to use."
  type        = string
}

variable "zone" {
  description = "This is the zone of the instance."
  type        = string
  validation {
    condition     = startswith(var.zone, "${var.region}-")
    error_message = "zone must be located within region."
  }
}
