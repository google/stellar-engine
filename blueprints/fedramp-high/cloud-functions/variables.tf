variable "artifact_registry_name" {
  description = "Name of the Artifact Registry being deployed."
  type        = string
  default     = "cloud-func-reg"
}

variable "bucket_name" {
  description = "The name of the Cloud Storage bucket where the Cloud Function source code is stored."
  type        = string
}

variable "function_entry_point" {
  description = "The entry point for the Cloud Function."
  type        = string
  default     = "helloHttp"
}

variable "function_memory_mb" {
  description = "The amount of memory (in MB) allocated for the Cloud Function."
  type        = number
  default     = 256
}

variable "function_name" {
  description = "The name of the Cloud Function."
  type        = string
}

variable "function_runtime" {
  description = "The runtime to use for the Cloud Function (e.g., nodejs18, python39, etc.)."
  type        = string
  default     = "nodejs20"
}

variable "function_timeout_seconds" {
  description = "The maximum amount of time (in seconds) the Cloud Function is allowed to run."
  type        = number
  default     = 60
}

variable "kms_key_name" {
  description = "Path to the kms key."
  type        = string
}

variable "main_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region where the Cloud Function will be deployed."
  type        = string
}
