variable "deletion_protection" {
  description = "Deletion protection."
  type        = bool
  default     = true
}

variable "description" {
  description = "Description of the workflow."
  type        = string
  default     = null
}

variable "env_vars" {
  description = "Environment variables made available to your workflow execution."
  type        = map(string)
  default     = null
}

variable "file" {
  description = "File path to the instructions for the workflow."
  type        = string
  default     = "code/example.yaml"
}

variable "logging_level" {
  description = "Logging level of workflow executions."
  type        = string
  default     = "LOG_ERRORS_ONLY"
}

variable "main_project_id" {
  description = "The Google Project ID."
  type        = string
}

variable "name" {
  description = "Name of the workflow."
  type        = string
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
}