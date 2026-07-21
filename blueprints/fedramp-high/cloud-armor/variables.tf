variable "main_project_id" {
  description = "Main project ID for Cloud Armor policies."
  type        = string
}

variable "region" {
  description = "Google Cloud Region."
  type        = string
  default     = "us-east4"
}

variable "rules_file" {
  description = "Path to the YAML file containing the rules."
  type        = string
  default     = "rules.yaml"
}