variable "cluster_id" {
  description = "The ID of the workstation cluster."
  type        = string
  default     = "example-workstation-cluster"
}

variable "config_id" {
  description = "The ID of the workstation configuration."
  type        = string
  default     = "example-workstation-config"
}

variable "core_project_id" {
  description = "The Project ID where the kms key is located."
  type        = string
  default     = null
}

variable "image" { # https://cloud.google.com/workstations/docs/preconfigured-base-images
  description = "Container image used by the workstations."
  type        = string
  default     = null
}

variable "kms_key_name" {
  description = "The name of the kms key."
  type        = string
}

variable "kms_keyring_name" {
  description = "The keyring of the kms key."
  type        = string
}

variable "machine_type" {
  description = "Type of GCE machine for the workstation configuration."
  type        = string
  default     = "e2-standard-4"
}

variable "main_project_id" {
  description = "The Project ID where the workstations will be created."
  type        = string
}

variable "network_name" {
  description = "The name of the network."
  type        = string
}

variable "network_project_id" {
  description = "The ID of the landing zone project where the VPC is located."
  type        = string
  default     = null
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
}

variable "subnetwork_name" {
  description = "The name of the subnet."
  type        = string
}

variable "workstations" {
  description = "The workstations that will be created based on the configuration."
  type = map(object({
    env   = optional(map(string))
    users = optional(list(string))
  }))
}