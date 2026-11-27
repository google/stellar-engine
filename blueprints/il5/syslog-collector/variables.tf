# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

variable "allowed_source_ranges" {
  description = "CIDR ranges permitted to send RFC 5425 TLS syslog traffic."
  type        = list(string)
  nullable    = false

  validation {
    condition     = length(var.allowed_source_ranges) > 0
    error_message = "Specify at least one allowed source CIDR range."
  }

  validation {
    condition = alltrue([
      for cidr in var.allowed_source_ranges : can(cidrhost(cidr, 0))
    ])
    error_message = "Every allowed_source_ranges entry must be a valid CIDR."
  }

  validation {
    condition = !anytrue([
      for cidr in var.allowed_source_ranges :
      contains(["0.0.0.0/0", "::/0"], trimspace(cidr)) ||
      try(tonumber(split("/", trimspace(cidr))[1]) == 0, false)
    ])
    error_message = (
      "Do not include wildcard ranges (0.0.0.0/0 or ::/0) in source ranges."
    )
  }
}

variable "boot_disk_size_gb" {
  description = "Size in GiB for each CMEK-encrypted collector boot disk."
  type        = number
  default     = 50
  nullable    = false

  validation {
    condition = (
      var.boot_disk_size_gb >= 20 &&
      var.boot_disk_size_gb <= 65536 &&
      floor(var.boot_disk_size_gb) == var.boot_disk_size_gb
    )
    error_message = "boot_disk_size_gb must be an integer from 20 to 65536."
  }
}

variable "distribution_zones" {
  description = "Optional list of at least two compute zones in var.region."
  type        = list(string)
  default     = null
  nullable    = true

  validation {
    condition = (
      var.distribution_zones == null || (
        length(var.distribution_zones) >= 2 &&
        alltrue([
          for zone in var.distribution_zones :
          startswith(zone, "${var.region}-")
        ])
      )
    )
    error_message = (
      "distribution_zones must be null or list >= 2 zones in var.region."
    )
  }
}

variable "enable_apis" {
  description = "Enable required Google Cloud APIs on var.project_id."
  type        = bool
  default     = true
  nullable    = false
}

variable "golden_image" {
  description = "Hardened Compute Engine golden image with Fluent Bit."
  type        = string
  nullable    = false

  validation {
    condition = can(regex(
      join("", [
        "^(https://www\\.googleapis\\.com/compute/v1/)?",
        "projects/[a-z][a-z0-9-]{4,28}[a-z0-9]",
        "/global/images/(family/)?[a-z0-9-]+$",
      ]),
      var.golden_image
    ))
    error_message = (
      "Use a valid projects/<project>/global/images/<image> or family path."
    )
  }
}

variable "grant_shared_vpc_subnet_iam" {
  description = "Grant Shared VPC subnet networkUser to the Google APIs agent."
  type        = bool
  default     = false
  nullable    = false
}

variable "health_check_port" {
  description = "Unprivileged TCP port for the Fluent Bit HTTP health API."
  type        = number
  default     = 2020
  nullable    = false

  validation {
    condition = (
      var.health_check_port >= 1024 &&
      var.health_check_port <= 65535 &&
      floor(var.health_check_port) == var.health_check_port
    )
    error_message = (
      "health_check_port must be an unprivileged integer (1024 to 65535)."
    )
  }

  validation {
    condition     = var.health_check_port != var.syslog_port
    error_message = "health_check_port must differ from syslog_port."
  }
}

variable "ilb_global_access" {
  description = "Allow clients in other regions to reach the ILB VIP."
  type        = bool
  default     = false
  nullable    = false
}

variable "ilb_ip_address" {
  description = "Optional static internal IPv4 address or self-link for ILB."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.ilb_ip_address == null ||
      can(cidrhost("${var.ilb_ip_address}/32", 0)) ||
      can(regex(
        join("", [
          "^(https://www\\.googleapis\\.com/compute/v1/)?",
          "projects/[a-z][a-z0-9-]{4,28}[a-z0-9]",
          "/regions/[a-z]+-[a-z]+[0-9]+/addresses/[a-z][-a-z0-9]{0,62}$",
        ]),
        var.ilb_ip_address
      ))
    )
    error_message = (
      "Set ilb_ip_address to null, an IPv4 address, or regional address path."
    )
  }
}

variable "kms_key_id" {
  description = "Regional Cloud KMS CryptoKey ID in var.region for boot disks."
  type        = string
  nullable    = false

  validation {
    condition = (
      can(regex(
        join("", [
          "^projects/[a-z][a-z0-9-]{4,28}[a-z0-9]",
          "/locations/[a-z0-9-]+",
          "/keyRings/[a-zA-Z0-9_-]+",
          "/cryptoKeys/[a-zA-Z0-9_-]+$",
        ]),
        var.kms_key_id
      )) &&
      !strcontains(var.kms_key_id, "/locations/global/") &&
      strcontains(var.kms_key_id, "/locations/${var.region}/")
    )
    error_message = (
      "kms_key_id must be a regional Cloud KMS CryptoKey ID in var.region."
    )
  }
}

variable "labels" {
  description = "Labels applied to collector Compute Engine and ILB resources."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "machine_type" {
  description = "AMD SEV-compatible machine type for collector instances."
  type        = string
  default     = "n2d-standard-2"
  nullable    = false

  validation {
    condition = can(regex(
      join("", [
        "^(n2d-((standard|highmem|highcpu)-[0-9]+",
        "|custom-[0-9]+-[0-9]+(-ext)?)",
        "|c2d-(standard|highmem|highcpu)-[0-9]+)$",
      ]),
      var.machine_type
    ))
    error_message = (
      "Use a valid AMD SEV-compatible n2d or c2d machine type."
    )
  }
}

variable "manage_kms_iam" {
  description = "Grant Cloud KMS encrypter/decrypter IAM to Compute agent."
  type        = bool
  default     = true
  nullable    = false
}

variable "max_replicas" {
  description = "Maximum collector instances maintained by the autoscaler."
  type        = number
  default     = 6
  nullable    = false

  validation {
    condition = (
      var.max_replicas >= var.min_replicas &&
      floor(var.max_replicas) == var.max_replicas
    )
    error_message = "max_replicas must be an integer >= min_replicas."
  }
}

variable "min_replicas" {
  description = "Minimum collector instances maintained across zones for HA."
  type        = number
  default     = 2
  nullable    = false

  validation {
    condition = (
      var.min_replicas >= 2 &&
      floor(var.min_replicas) == var.min_replicas
    )
    error_message = "min_replicas must be an integer >= 2 for multi-zone HA."
  }
}

variable "name_prefix" {
  description = "Lowercase naming prefix applied to collector resources."
  type        = string
  default     = "syslog-collector"
  nullable    = false

  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{1,24}[a-z0-9]$", var.name_prefix)
    )
    error_message = (
      "name_prefix must be 3 to 26 lowercase alphanumeric/hyphen chars."
    )
  }
}

variable "network_name" {
  description = "Name of the existing VPC network in var.network_project_id."
  type        = string
  nullable    = false

  validation {
    condition = can(
      regex("^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$", var.network_name)
    )
    error_message = "network_name must be a valid Compute Engine VPC name."
  }
}

variable "network_project_id" {
  description = "Project ID hosting the Shared VPC network and firewall rules."
  type        = string
  nullable    = false

  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.network_project_id)
    )
    error_message = "network_project_id must be a valid GCP project ID."
  }
}

variable "project_id" {
  description = "Workload project ID hosting the collector MIG, ILB, and SA."
  type        = string
  nullable    = false

  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id)
    )
    error_message = "project_id must be a valid Google Cloud project ID."
  }
}

variable "region" {
  description = "US Google Cloud region for MIG, ILB, and regional secrets."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^us-[a-z]+[0-9]+$", var.region))
    error_message = "region must be a valid US region (e.g. us-east4)."
  }
}

variable "secret_project_id" {
  description = "Optional project ID hosting Regional Secret Manager secrets."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.secret_project_id == null ||
      can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.secret_project_id))
    )
    error_message = (
      "secret_project_id must be null or a valid GCP project ID."
    )
  }
}

variable "subnetwork_name" {
  description = "Name of the regional subnetwork in var.network_project_id."
  type        = string
  nullable    = false

  validation {
    condition = can(
      regex("^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$", var.subnetwork_name)
    )
    error_message = "subnetwork_name must be a valid GCE subnetwork name."
  }
}

variable "syslog_framing_format" {
  description = "TCP framing format for RFC 5425 syslog."
  type        = string
  default     = "octet_counting"
  nullable    = false

  validation {
    condition = contains(
      ["octet_counting", "newline"],
      var.syslog_framing_format
    )
    error_message = (
      "syslog_framing_format must be octet_counting or newline."
    )
  }
}

variable "syslog_port" {
  description = "Unprivileged TCP port for RFC 5425 mutual TLS syslog."
  type        = number
  default     = 6514
  nullable    = false

  validation {
    condition = (
      var.syslog_port >= 1024 &&
      var.syslog_port <= 65535 &&
      floor(var.syslog_port) == var.syslog_port
    )
    error_message = (
      "syslog_port must be an unprivileged integer (1024 to 65535)."
    )
  }
}

variable "tls_secret_ids" {
  description = "Regional CMEK Secret Manager IDs for TLS cert, key, and CA."
  type = object({
    client_ca_cert = string
    server_cert    = string
    server_key     = string
  })
  nullable = false

  validation {
    condition = alltrue([
      for secret_id in [
        var.tls_secret_ids.client_ca_cert,
        var.tls_secret_ids.server_cert,
        var.tls_secret_ids.server_key,
      ] : can(regex("^[a-zA-Z0-9_-]{1,255}$", secret_id))
    ])
    error_message = (
      "tls_secret_ids must be valid Secret Manager IDs, never inline PEM."
    )
  }

  validation {
    condition = length(distinct([
      var.tls_secret_ids.client_ca_cert,
      var.tls_secret_ids.server_cert,
      var.tls_secret_ids.server_key,
    ])) == 3
    error_message = (
      "Use distinct secret IDs for client_ca_cert, server_cert, server_key."
    )
  }
}
