variable "binary_authorization_mode" {
  description = "Binary Authorization mode for the Cloud Run service."
  type        = string
  default     = "default"
  validation {
    condition     = contains(["default", "policy", "disabled"], var.binary_authorization_mode)
    error_message = "Allowed values for binary_authorization_mode are 'default', 'policy', or 'disabled'."
  }
}

variable "binary_authorization_policy" {
  description = "The full resource name of the Binary Authorization policy (e.g., 'projects/YOUR_PROJECT_ID/policies/YOUR_POLICY_ID')."
  type        = string
  default     = null
  validation {
    condition     = var.binary_authorization_mode != "policy" || (var.binary_authorization_mode == "policy" && var.binary_authorization_policy != null)
    error_message = "If binary_authorization_mode is set to 'policy', then binary_authorization_policy must be specified."
  }
}

variable "container_image" {
  description = "Container image to be hosted on cloud run."
  type        = string
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "cpu" {
  description = "Sets the CPU limit. 1000m = 1 vCPU."
  type        = string
  default     = "1000m"
}

variable "cpu_idle" {
  description = "Allows the container to scale to zero."
  type        = bool
  default     = true
}

variable "env_vars" {
  description = "Environment variables for the Cloud Run service or job."
  type        = map(string)
  default     = {}
}

variable "ingress" {
  description = "Ingress settings."
  type        = string
  default     = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
}

variable "is_job" {
  description = "Set to true to create a job instead of a service."
  type        = bool
  default     = false
}

variable "kms_key_name" {
  description = "Path to the kms key to use."
  type        = string
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Main Project ID."
  type        = string
}

variable "memory" {
  description = "Sets the memory limit. 512Mi = 512MiB."
  type        = string
  default     = "512Mi"
}

variable "name" {
  description = "Name of the cloud run instance to be created."
  type        = string
}

variable "port" {
  description = "Mapping of port number and port name to open."
  type        = number
  default     = 8080
}

variable "region" {
  description = "Google Cloud Region."
  type        = string
}
