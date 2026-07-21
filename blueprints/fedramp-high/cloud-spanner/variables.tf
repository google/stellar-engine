variable "config_name" {
  description = "Cloud spanner instance config name."
  type        = string
  default     = "regional-us-east4"
}

variable "database_drop_protection" {
  description = "Cloud spanner level protection against accidental deletion of database in Terraform, gcloud command or Cloud Console."
  type        = bool
}

variable "database_name" {
  description = "Database name."
  type        = string
}

variable "database_user" {
  description = "Database user or group. Must start with \"user:\" or \"group:\" or \"serviceAccount:\"."
  type        = string
}

variable "display_name" {
  description = "Cloud spanner display name."
  type        = string
}

variable "edition" {
  description = "The Spanner instance edition. Valid values are 'EDITION_UNSPECIFIED', 'STANDARD', 'ENTERPRISE', or 'ENTERPRISE_PLUS'."
  type        = string
  default     = "ENTERPRISE"
  validation {
    condition     = contains(["EDITION_UNSPECIFIED", "STANDARD", "ENTERPRISE", "ENTERPRISE_PLUS"], var.edition)
    error_message = "The edition must be one of 'EDITION_UNSPECIFIED', 'STANDARD', 'ENTERPRISE', or 'ENTERPRISE_PLUS'."
  }
}

variable "high_priority_cpu_utilization_percent" {
  description = "High priority cpu utilization percent."
  type        = number
  default     = 75
}

variable "instance_name" {
  description = "Cloud spanner instance name."
  type        = string
}

variable "main_project_id" {
  description = "Project to deploy Cloud Spanner instance."
  type        = string
}

variable "max_processing_units" {
  description = "Max processing units for autoscaling."
  type        = number
  default     = 3000
}

variable "min_processing_units" {
  description = "Min processing units for autoscaling."
  type        = number
  default     = 2000
}

variable "region" {
  description = "Region to create your App Engine resource."
  type        = string
  default     = "us-east4"
}

variable "storage_utilization_percent" {
  description = "Storage utilization percent."
  type        = number
  default     = 90
}