variable "backup_schedule" {
  description = "The Backup schedule - select daily or weekly in your tfvars."
  type = object({
    retention         = string
    daily_recurrence  = optional(bool, false)
    weekly_recurrence = optional(string)
  })
  default = null
}

variable "firestore_database_name" {
  type        = string
  description = "The name of the Firestore database instance."
}

variable "main_project_id" {
  type        = string
  description = "The main project ID of the Google Cloud project."
}

variable "region" {
  type        = string
  description = "The location ID where the Firestore database will be created."
}