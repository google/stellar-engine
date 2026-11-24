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

variable "boot_disk_size_gb" {
  description = "Size of the runner boot disk in GiB."
  type        = number
  default     = 50
  nullable    = false
  validation {
    condition     = var.boot_disk_size_gb >= 20
    error_message = "Boot disk size must be at least 20 GiB."
  }
}

variable "boot_disk_type" {
  description = "Persistent disk type for the runner boot disk."
  type        = string
  default     = "pd-balanced"
  nullable    = false
  validation {
    condition     = contains(["pd-balanced", "pd-ssd"], var.boot_disk_type)
    error_message = "Boot disk type must be pd-balanced or pd-ssd for SEV VMs."
  }
}

variable "create_runner_token_secret" {
  description = "Create a CMEK regional Secret Manager secret for the runner."
  type        = bool
  default     = false
  nullable    = false
}

variable "docker_image" {
  description = "Default Artifact Registry image when executor is docker."
  type        = string
  default     = "us-docker.pkg.dev/google.com/cloudsdktool/google-cloud-cli:slim"
  nullable    = false
  validation {
    condition     = can(regex("^[a-zA-Z0-9._/@:-]{1,256}$", var.docker_image))
    error_message = "Use a valid container image reference without whitespace."
  }
  validation {
    condition     = !can(regex("(^|\\.)gcr\\.io/", var.docker_image))
    error_message = "Legacy gcr.io registries are forbidden; use pkg.dev."
  }
}

variable "enable_apis" {
  description = "Enable required Google Cloud APIs on var.project_id."
  type        = bool
  default     = true
  nullable    = false
}

variable "enable_boot_disk_snapshots" {
  description = "Attach an optional daily 14-day boot disk snapshot schedule."
  type        = bool
  default     = false
  nullable    = false
}

variable "enable_cloud_nat" {
  description = "Provision an optional Cloud NAT in network_project_id."
  type        = bool
  default     = false
  nullable    = false
}

variable "enable_iap_ssh" {
  description = "Create a logged SA-targeted IAP SSH firewall rule."
  type        = bool
  default     = false
  nullable    = false
}

variable "executor" {
  description = "GitLab Runner job executor type: docker or shell."
  type        = string
  default     = "docker"
  nullable    = false
  validation {
    condition     = contains(["docker", "shell"], var.executor)
    error_message = "Executor must be either 'docker' or 'shell'."
  }
}

variable "gitlab_url" {
  description = "HTTPS base URL of the GitLab coordinator instance."
  type        = string
  nullable    = false
  validation {
    condition = can(regex(
      "^https://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/[a-zA-Z0-9._~/-]*)?$",
      var.gitlab_url
    ))
    error_message = "GitLab URL must start with https:// and be a valid URL."
  }
}

variable "golden_image" {
  description = "Pre-baked GCE golden image or family with gitlab-runner."
  type        = string
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^(https://www\\.googleapis\\.com/compute/v1/)?",
        "(projects/[a-z][a-z0-9-]{4,28}[a-z0-9]/global/images/",
        "(family/)?[a-z][a-z0-9-]{0,62}|",
        "[a-z][a-z0-9-]{4,28}[a-z0-9]/[a-z][a-z0-9-]{0,62})$",
      ]),
      var.golden_image
    ))
    error_message = "Use a valid GCE image or image family reference."
  }
}

variable "instance_name" {
  description = "Compute Engine instance name for the GitLab Runner VM."
  type        = string
  default     = "gitlab-runner-0"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z]([a-z0-9-]{0,47}[a-z0-9])?$", var.instance_name)
    )
    error_message = (
      "Instance name must be 1 to 49 lowercase letters, digits, or hyphens."
    )
  }
}

variable "kms_key_id" {
  description = "Regional Cloud KMS crypto key ID in region for CMEK."
  type        = string
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^projects/[a-z][a-z0-9-]{4,28}[a-z0-9]",
        "/locations/[a-z0-9-]+",
        "/keyRings/[a-zA-Z0-9_-]{1,63}",
        "/cryptoKeys/[a-zA-Z0-9_-]{1,63}$",
      ]),
      var.kms_key_id
    ))
    error_message = (
      "Use projects/{proj}/locations/{loc}/keyRings/{ring}/cryptoKeys/{key}."
    )
  }
  validation {
    condition = (
      !strcontains(var.kms_key_id, "/locations/global/") &&
      strcontains(var.kms_key_id, "/locations/${var.region}/")
    )
    error_message = "Use a regional KMS key in the configured region."
  }
}

variable "labels" {
  description = "Labels applied to the runner instance and boot disk."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "machine_type" {
  description = "AMD SEV-compatible GCE machine type for the runner VM."
  type        = string
  default     = "n2d-standard-4"
  nullable    = false
  validation {
    condition = can(regex(
      join("", [
        "^(n2d-((standard|highmem|highcpu)-[0-9]+",
        "|custom-[0-9]+-[0-9]+(-ext)?)|",
        "(c2d|c3d)-(standard|highmem|highcpu)-[0-9]+)$",
      ]),
      var.machine_type
    ))
    error_message = "Use an AMD SEV-compatible n2d, c2d, or c3d machine shape."
  }
}

variable "manage_kms_iam" {
  description = "Manage Cloud KMS IAM bindings for Compute and Secret agents."
  type        = bool
  default     = true
  nullable    = false
}

variable "network_name" {
  description = "VPC network name in network_project_id."
  type        = string
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$", var.network_name)
    )
    error_message = "Network name must match GCP VPC naming rules."
  }
}

variable "network_project_id" {
  description = "Project ID hosting the Shared VPC network and subnetwork."
  type        = string
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.network_project_id)
    )
    error_message = "Network project ID must be a valid 6-30 char project ID."
  }
}

variable "project_id" {
  description = "Workload project ID hosting the GitLab Runner VM and SA."
  type        = string
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id)
    )
    error_message = "Project ID must be a valid 6-30 character GCP project ID."
  }
}

variable "region" {
  description = "GCP region for subnetwork, regional secret, and Cloud NAT."
  type        = string
  nullable    = false
  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]+$", var.region))
    error_message = "Region must be a valid GCP region such as us-east4."
  }
}

variable "runner_token_secret_id" {
  description = "Regional Secret Manager ID holding the GitLab Runner token."
  type        = string
  nullable    = false
  validation {
    condition = can(
      regex("^[a-zA-Z0-9_-]{1,255}$", var.runner_token_secret_id)
    )
    error_message = "Secret ID must be 1-255 alphanumeric, _, or - chars."
  }
}

variable "runner_token_secret_project_id" {
  description = "Optional project ID hosting an existing regional secret."
  type        = string
  default     = null
  validation {
    condition = (
      var.runner_token_secret_project_id == null ||
      can(
        regex(
          "^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
          var.runner_token_secret_project_id,
        )
      )
    )
    error_message = "Secret project ID must be null or a valid GCP project ID."
  }
  validation {
    condition = (
      !var.create_runner_token_secret ||
      var.runner_token_secret_project_id == null ||
      var.runner_token_secret_project_id == var.project_id
    )
    error_message = (
      "Set runner_token_secret_project_id to null or project_id when creating."
    )
  }
}

variable "runner_token_secret_version" {
  description = "Secret Manager version identifier read by startup script."
  type        = string
  default     = "latest"
  nullable    = false
  validation {
    condition = can(
      regex("^(latest|[1-9][0-9]*)$", var.runner_token_secret_version)
    )
    error_message = "Secret version must be 'latest' or a positive integer."
  }
}

variable "runner_token_secret_wo" {
  description = "Optional write-only secret version avoiding Terraform state."
  type = object({
    path       = optional(string)
    value      = optional(string)
    wo_version = number
  })
  sensitive = true
  default   = null
  validation {
    condition = (
      var.runner_token_secret_wo == null ||
      var.create_runner_token_secret
    )
    error_message = (
      "runner_token_secret_wo requires create_runner_token_secret = true."
    )
  }
  validation {
    condition = (
      var.runner_token_secret_wo == null ||
      var.runner_token_secret_wo.wo_version >= 1
    )
    error_message = "runner_token_secret_wo.wo_version must be at least 1."
  }
  validation {
    condition = (
      var.runner_token_secret_wo == null ||
      (
        (
          var.runner_token_secret_wo.path != null &&
          length(trimspace(var.runner_token_secret_wo.path)) > 0
          ) != (
          var.runner_token_secret_wo.value != null &&
          length(trimspace(var.runner_token_secret_wo.value)) > 0
        )
      )
    )
    error_message = (
      "Provide exactly one non-empty path or value in runner_token_secret_wo."
    )
  }
}

variable "service_account_id" {
  description = "Account ID for the dedicated GitLab Runner service account."
  type        = string
  default     = "gitlab-runner-sa"
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.service_account_id)
    )
    error_message = "Service account ID must be 6-30 lowercase chars/hyphens."
  }
}

variable "subnetwork_name" {
  description = "Subnetwork name in network_project_id and region."
  type        = string
  nullable    = false
  validation {
    condition = can(
      regex("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$", var.subnetwork_name)
    )
    error_message = "Subnetwork name must match GCP subnetwork naming rules."
  }
}

variable "zone" {
  description = "GCP compute zone inside region for the GitLab Runner VM."
  type        = string
  nullable    = false
  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]+-[a-z]$", var.zone))
    error_message = "Zone must be a valid GCP zone such as us-east4-a."
  }
  validation {
    condition     = startswith(var.zone, "${var.region}-")
    error_message = "Zone must belong to the configured region."
  }
}
