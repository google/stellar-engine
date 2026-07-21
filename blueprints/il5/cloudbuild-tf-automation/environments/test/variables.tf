
variable "project_id" {
  description = "The ID of the project where the Cloud Build service account will be created and operate."
  type        = string
}

variable "bucket_name" {
  description = "The name of the GCS bucket used for Terraform remote state."
  type        = string
}

variable "locations" {
  description = "Optional locations for GCS, BigQuery, and logging buckets created here."
  type = object({
    bq      = optional(string, "US")
    gcs     = optional(string, "US")
    logging = optional(string, "global")
    pubsub  = optional(list(string), [])
    kms     = optional(string, "US")
  })
  nullable = false
  default  = {}
}

variable "prefix" {
  description = "Prefix used for resources that need unique names. Use 7 characters or less."
  type        = string
  validation {
    condition     = try(length(var.prefix), 0) <= 7
    error_message = "Use a maximum of 7 characters for prefix."
  }
}

variable "state_bucket" {
  description = "The bucket created in the blueprint to hold project state."
  type        = string
}