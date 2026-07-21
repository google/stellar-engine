variable "data" {
  description = "Unencoded data to be sent."
  type        = string
  default     = ""
}

variable "description" {
  description = "Description of job."
  type        = string
}

variable "kms_key_name" {
  description = "Full path to KMS key for pubsub."
  type        = string
  default     = null
}

variable "main_project_id" {
  description = "Project id."
  type        = string
}

variable "name" {
  description = "Name of the Cloud Scheduler job."
  type        = string
}

variable "new_topic_name" {
  description = "Name for new PubSub topic if creating one."
  type        = string
  default     = null
}

variable "region" {
  description = "Location to deploy job."
  type        = string
}

variable "retry_count" {
  description = "Number of retries."
  type        = number
  default     = null
}

variable "schedule" {
  description = "Schedule to implement the job -- use cron-based syntax."
  type        = string
}

variable "topic_id" {
  description = "PubSub topic ID."
  type        = string
  default     = null
}