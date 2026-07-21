variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "kms_key_name" {
  description = "Full path to KMS key for pubsub."
  type        = string
  default     = null
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Project id."
  type        = string
}

variable "name" {
  description = "Name of DataFusion instance."
  type        = string
}

variable "network_name" {
  description = "Full path to VPC."
  type        = string
}

variable "network_project_id" {
  description = "Landing project id."
  type        = string
}

variable "region" {
  description = "Location to deploy job."
  type        = string
}

variable "subnetwork_name" {
  description = "Full path to subnet."
  type        = string
}
