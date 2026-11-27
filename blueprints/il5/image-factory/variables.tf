# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

variable "allow_builder_network_mismatch" {
  description = "Allow builder_subnetwork in a VPC other than peered_network."
  type        = bool
  default     = false
  nullable    = false
}

variable "artifact_registry_name" {
  description = "Name of the private CMEK Artifact Registry Docker repository."
  type        = string
  default     = "image-factory-builders"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{0,61}[a-z0-9]$", var.artifact_registry_name)
    )
    error_message = (
      "The artifact_registry_name must match ^[a-z][a-z0-9-]{0,61}[a-z0-9]$."
    )
  }
}

variable "base_image" {
  description = "Immutable Compute Engine source image path for RHEL 9 builds."
  type        = string
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^projects/[a-z][a-z0-9-]{4,28}[a-z0-9]",
        "/global/images/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$",
      ]),
      var.base_image,
    ))
    error_message = (
      "Use immutable projects/<project>/global/images/<image> format."
    )
  }
}

variable "build_timeout" {
  description = "Maximum Cloud Build pipeline duration in seconds."
  type        = string
  default     = "3600s"
  nullable    = false
  validation {
    condition     = can(regex("^[1-9][0-9]*s$", var.build_timeout))
    error_message = "Set build_timeout to positive seconds ending in s."
  }
}

variable "builder_confidential_compute_type" {
  description = "Confidential VM type for ephemeral builders, or null."
  type        = string
  default     = "SEV"
  nullable    = true
  validation {
    condition = (
      var.builder_confidential_compute_type == null
      || contains(
        ["SEV", "SEV_SNP", "TDX"],
        var.builder_confidential_compute_type,
      )
    )
    error_message = (
      "Set builder_confidential_compute_type to SEV, SEV_SNP, TDX, or null."
    )
  }
  validation {
    condition = (
      var.builder_confidential_compute_type != "SEV"
      || can(regex("^(n2d|c2d|c3d)-", var.builder_machine_type))
    )
    error_message = (
      "SEV requires an n2d, c2d, or c3d builder_machine_type."
    )
  }
  validation {
    condition = (
      var.builder_confidential_compute_type != "SEV_SNP"
      || startswith(var.builder_machine_type, "n2d-")
    )
    error_message = "SEV_SNP requires an n2d builder_machine_type."
  }
  validation {
    condition = (
      var.builder_confidential_compute_type != "TDX"
      || startswith(var.builder_machine_type, "c3-")
    )
    error_message = "TDX requires a c3 builder_machine_type."
  }
}

variable "builder_image_digest" {
  description = "Artifact Registry builder image pinned by @sha256: digest."
  type        = string
  nullable    = false
  validation {
    condition = !strcontains(lower(var.builder_image_digest), "gcr.io")
    error_message = (
      "Legacy gcr.io is forbidden; use a private Artifact Registry image."
    )
  }
  validation {
    condition = can(regex(
      "^[a-z0-9-]+-docker\\.pkg\\.dev/[a-z0-9._:/-]+@sha256:[a-f0-9]{64}$",
      var.builder_image_digest,
    ))
    error_message = (
      "Pin builder_image_digest to Artifact Registry with @sha256: digest."
    )
  }
}

variable "builder_machine_type" {
  description = "Compute Engine machine type for ephemeral RHEL 9 builder VMs."
  type        = string
  default     = "n2d-standard-2"
  nullable    = false
  validation {
    condition = can(regex(
      "^(c2d|c3|c3d|e2|n2|n2d)-(standard|highcpu|highmem)-[0-9]+$",
      var.builder_machine_type,
    ))
    error_message = (
      "Use a valid GCE machine type such as n2d-standard-2."
    )
  }
}

variable "builder_sa_name" {
  description = "Short account name for the Cloud Build service account."
  type        = string
  default     = "image-builder"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.builder_sa_name)
    )
    error_message = (
      "Use 6 to 30 lowercase letters, digits, or hyphens starting with a-z."
    )
  }
  validation {
    condition = (
      length(
        var.prefix == null
        ? var.builder_sa_name
        : "${var.prefix}-${var.builder_sa_name}"
      ) >= 6
      && length(
        var.prefix == null
        ? var.builder_sa_name
        : "${var.prefix}-${var.builder_sa_name}"
      ) <= 30
    )
    error_message = (
      "Combined prefix and builder_sa_name must be 6 to 30 characters."
    )
  }
}

variable "builder_subnetwork" {
  description = "Full resource path of the private builder VPC subnetwork."
  type        = string
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^projects/[a-z][a-z0-9-]{4,28}[a-z0-9]",
        "/regions/[a-z]+-[a-z]+[0-9]+",
        "/subnetworks/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$",
      ]),
      var.builder_subnetwork,
    ))
    error_message = (
      "Use projects/<project>/regions/<region>/subnetworks/<name> format."
    )
  }
  validation {
    condition = strcontains(
      var.builder_subnetwork,
      "/regions/${var.region}/",
    )
    error_message = "The builder_subnetwork region must match var.region."
  }
}

variable "builder_zone" {
  description = "Compute Engine zone in var.region for ephemeral builder VMs."
  type        = string
  nullable    = false
  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]+-[a-z]$", var.builder_zone))
    error_message = "Use a valid Compute Engine zone such as us-east4-a."
  }
  validation {
    condition     = startswith(var.builder_zone, "${var.region}-")
    error_message = "The builder_zone must belong to var.region."
  }
}

variable "cloudbuild_config_object_name" {
  description = "Object path in the staging bucket for the Cloud Build YAML."
  type        = string
  default     = "cloudbuild/cloudbuild-rhel9-stig.yaml"
  nullable    = false
  validation {
    condition = (
      length(trimspace(var.cloudbuild_config_object_name)) > 0
      && !startswith(var.cloudbuild_config_object_name, "/")
    )
    error_message = (
      "Set cloudbuild_config_object_name to a non-empty relative object path."
    )
  }
}

variable "enable_apis" {
  description = "Enable required Google Cloud APIs on project_id."
  type        = bool
  default     = true
  nullable    = false
}

variable "enable_ssh_firewall_rule" {
  description = "Create an ingress TCP 22 rule from peered_network_ip_range."
  type        = bool
  default     = false
  nullable    = false
  validation {
    condition = (
      !var.enable_ssh_firewall_rule
      || (
        var.peered_network_ip_range != null
        && can(cidrnetmask(var.peered_network_ip_range))
      )
    )
    error_message = (
      "Set peered_network_ip_range to a full CIDR when enabling SSH firewall."
    )
  }
}

variable "grant_service_agent_kms_iam" {
  description = "Grant Cloud KMS encrypter/decrypter IAM to service agents."
  type        = bool
  default     = true
  nullable    = false
}

variable "guest_os_features" {
  description = "Guest OS features stamped on golden images."
  type        = list(string)
  default     = ["SEV_CAPABLE", "UEFI_COMPATIBLE", "GVNIC"]
  nullable    = false
  validation {
    condition = (
      var.builder_confidential_compute_type != "SEV"
      || contains(var.guest_os_features, "SEV_CAPABLE")
    )
    error_message = "SEV builders require SEV_CAPABLE in guest_os_features."
  }
  validation {
    condition = (
      var.builder_confidential_compute_type != "SEV_SNP"
      || contains(var.guest_os_features, "SEV_SNP_CAPABLE")
    )
    error_message = (
      "SEV_SNP builders require SEV_SNP_CAPABLE in guest_os_features."
    )
  }
  validation {
    condition = (
      var.builder_confidential_compute_type != "TDX"
      || contains(var.guest_os_features, "TDX_CAPABLE")
    )
    error_message = "TDX builders require TDX_CAPABLE in guest_os_features."
  }
  validation {
    condition = alltrue([
      for feature in var.guest_os_features : contains([
        "GVNIC",
        "IDPF",
        "MULTI_IP_SUBNET",
        "SECURE_BOOT",
        "SEV_CAPABLE",
        "SEV_LIVE_MIGRATABLE",
        "SEV_LIVE_MIGRATABLE_V2",
        "SEV_SNP_CAPABLE",
        "TDX_CAPABLE",
        "UEFI_COMPATIBLE",
        "VIRTIO_SCSI_MULTIQUEUE",
        "WINDOWS",
      ], feature)
    ])
    error_message = "Use supported Compute Engine guest_os_features values."
  }
}

variable "image_family" {
  description = "Compute Engine image family assigned to golden images."
  type        = string
  default     = "rhel-9-stig-golden"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{0,61}[a-z0-9]$", var.image_family)
    )
    error_message = (
      "The image_family must match ^[a-z][a-z0-9-]{0,61}[a-z0-9]$."
    )
  }
}

variable "image_name_prefix" {
  description = "Prefix prepended to golden image names (max 26 characters)."
  type        = string
  default     = "rhel9-stig"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{0,24}[a-z0-9]$", var.image_name_prefix)
    )
    error_message = (
      "Keep image_name_prefix <= 26 lowercase alphanumeric/hyphen chars."
    )
  }
}

variable "kms_key_id" {
  description = "Regional Cloud KMS CryptoKey ID in var.region for CMEK."
  type        = string
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^projects/[a-z][a-z0-9-]{4,28}[a-z0-9]",
        "/locations/[a-z0-9-]+",
        "/keyRings/[a-zA-Z0-9_-]+",
        "/cryptoKeys/[a-zA-Z0-9_-]+$",
      ]),
      var.kms_key_id,
    ))
    error_message = (
      "Use projects/<proj>/locations/<loc>/keyRings/<ring>/cryptoKeys/<key>."
    )
  }
  validation {
    condition = (
      !strcontains(var.kms_key_id, "/locations/global/")
      && strcontains(var.kms_key_id, "/locations/${var.region}/")
    )
    error_message = "Use a regional Cloud KMS key in var.region."
  }
}

variable "labels" {
  description = "Labels applied to the staging bucket and Artifact Registry."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "peered_network" {
  description = "Peered VPC network path for the private worker pool."
  type        = string
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^projects/[a-z0-9][a-z0-9-]{0,29}",
        "/global/networks/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$",
      ]),
      var.peered_network,
    ))
    error_message = (
      "Use projects/<project-number-or-id>/global/networks/<network> format."
    )
  }
}

variable "peered_network_ip_range" {
  description = "Optional CIDR block or prefix length for Cloud Build workers."
  type        = string
  default     = null
  validation {
    condition = (
      var.peered_network_ip_range == null
      || can(cidrnetmask(var.peered_network_ip_range))
      || can(regex("^/(1[6-9]|2[0-9])$", var.peered_network_ip_range))
    )
    error_message = (
      "Use a valid IPv4 CIDR (10.250.0.0/24) or prefix size (/16 to /29)."
    )
  }
}

variable "prefix" {
  description = "Optional prefix prepended to bucket, SA, and pool names."
  type        = string
  default     = null
  validation {
    condition = (
      var.prefix == null
      || can(regex("^[a-z][a-z0-9-]{0,8}[a-z0-9]$", var.prefix))
    )
    error_message = (
      "The prefix must be 2 to 10 lowercase letters, digits, or hyphens."
    )
  }
}

variable "project_id" {
  description = "Google Cloud project ID hosting the golden image factory."
  type        = string
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id)
    )
    error_message = (
      "The project_id must be a valid 6 to 30 character GCP project ID."
    )
  }
}

variable "region" {
  description = "Google Cloud region hosting image factory resources."
  type        = string
  nullable    = false
  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]+$", var.region))
    error_message = "Use a valid Google Cloud region such as us-east4."
  }
}

variable "staging_bucket_force_destroy" {
  description = "Allow Terraform destroy to delete objects in staging bucket."
  type        = bool
  default     = false
  nullable    = false
}

variable "staging_bucket_name" {
  description = "Name suffix of the CMEK Cloud Storage staging bucket."
  type        = string
  default     = "image-factory-staging"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z0-9][a-z0-9-_]{1,61}[a-z0-9]$", var.staging_bucket_name)
    )
    error_message = "Use a valid Cloud Storage bucket name suffix."
  }
}

variable "trigger_config" {
  description = "Optional Cloud Build trigger for repo or Pub/Sub events."
  type = object({
    approval_required = optional(bool, false)
    description       = optional(string, "Golden image factory trigger.")
    disabled          = optional(bool, false)
    filename          = optional(string)
    name              = string
    pubsub_topic      = optional(string)
    repository_event = optional(object({
      branch       = optional(string)
      invert_regex = optional(bool, false)
      repository   = string
      tag          = optional(string)
    }))
    substitutions = optional(map(string), {})
    tags          = optional(list(string), ["image-factory", "rhel9-stig"])
  })
  default = null
  validation {
    condition = var.trigger_config == null || (
      (var.trigger_config.repository_event != null ? 1 : 0) +
      (var.trigger_config.pubsub_topic != null ? 1 : 0)
    ) == 1
    error_message = (
      "Specify one of trigger_config.repository_event or pubsub_topic."
    )
  }
  validation {
    condition = (
      var.trigger_config == null
      || var.trigger_config.repository_event == null
      || var.trigger_config.filename != null
    )
    error_message = (
      "Set trigger_config.filename when using repository_event."
    )
  }
  validation {
    condition = (
      var.trigger_config == null
      || var.trigger_config.repository_event == null
      || (
        (var.trigger_config.repository_event.branch != null ? 1 : 0) +
        (var.trigger_config.repository_event.tag != null ? 1 : 0)
      ) == 1
    )
    error_message = (
      "Specify either branch or tag inside trigger_config.repository_event."
    )
  }
  validation {
    condition = (
      var.trigger_config == null
      || var.trigger_config.pubsub_topic == null
      || can(regex(
        "^projects/[a-z][a-z0-9-]{4,28}[a-z0-9]/topics/[a-zA-Z0-9._~%+-]+$",
        var.trigger_config.pubsub_topic,
      ))
    )
    error_message = (
      "Use projects/<project>/topics/<topic> for trigger_config.pubsub_topic."
    )
  }
}

variable "worker_pool_disk_size_gb" {
  description = "Boot disk size in GB for private Cloud Build workers."
  type        = number
  default     = 100
  nullable    = false
  validation {
    condition = (
      var.worker_pool_disk_size_gb >= 100
      && var.worker_pool_disk_size_gb <= 1000
    )
    error_message = "Set worker_pool_disk_size_gb between 100 and 1000 GB."
  }
}

variable "worker_pool_machine_type" {
  description = "Compute Engine machine type for private Cloud Build workers."
  type        = string
  default     = "e2-standard-4"
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^(e2-medium|",
        "(c2|c2d|c3|e2|n1|n2|n2d|t2d)-(standard|highcpu|highmem)-[0-9]+)$",
      ]),
      var.worker_pool_machine_type,
    ))
    error_message = (
      "Use a supported worker pool machine type such as e2-standard-4."
    )
  }
}

variable "worker_pool_name" {
  description = "Name suffix of the private Cloud Build worker pool."
  type        = string
  default     = "image-factory-pool"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{0,61}[a-z0-9]$", var.worker_pool_name)
    )
    error_message = (
      "The worker_pool_name must match ^[a-z][a-z0-9-]{0,61}[a-z0-9]$."
    )
  }
}
