variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "developer_registries" {
  description = "A map of developer registries and readers/writers for those developer registries."
  type = map(object({
    readers = optional(list(string))
    writers = optional(list(string))
  }))
}

variable "kms_key_name" {
  description = "The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for disk encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type        = string
}

variable "main_project_id" {
  description = "GCP Project to deploy Google Artifact Registries into."
  type        = string
}

variable "network_project_id" {
  description = "Project that the Consumer Compute Engine VPC is located."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy Consumer VM into."
  type        = string
}

variable "subnetwork_name" {
  description = "VPC Subnet to deploy Consumer VM into."
  type        = string
}

variable "vpc_network_name" {
  description = "Name of the VPC where the subnet is deployed."
  type        = string
  default     = ""
  nullable    = false
}
