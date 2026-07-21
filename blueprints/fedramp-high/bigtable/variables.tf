variable "bigtable_service_account_id" {
  description = "The Service Account for Bigtable."
  type        = string
}

variable "cluster_id" {
  description = "The Bigtable cluster ID."
  type        = string
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "instance_name" {
  description = "Provide the name of the Bigtable."
  type        = string
}

variable "kms_key_name" {
  description = "The Cloud KMS key for encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Main project ID."
  type        = string
}

variable "num_nodes" {
  description = "Number of nodes in the Bigtable cluster."
  type        = number
  default     = 1
}

variable "region" {
  description = "Google Cloud Region."
  type        = string
  default     = "us-east4"
}

variable "storage_type" {
  description = "Either SSD or HDD."
  type        = string
  default     = "SSD"
}

variable "table" {
  description = "Table to create in the bigtable instance. Default is null."
  type = map(object({
    split_keys      = optional(list(string))
    column_families = map(object({}))
  }))
  default = {
    "Test" = {
      column_families = {}
    }
  }
}

variable "zone" {
  description = "Google Cloud Zone."
  type        = string
  default     = "us-east4-a"
}