variable "access_levels" {
  description = "List of access levels to create. Each access level is a map containing 'name', 'description', and 'conditions'."
  type = list(object({
    name        = string
    description = string
    conditions = list(object({
      ip_subnetworks = list(string)
      members        = list(string)
      negate         = bool
      device_policy = object({
        require_screen_lock = bool
      })
      regions = list(string)
    }))
  }))
}

variable "access_policy_title" {
  description = "The title for the Access Context Manager policy."
  type        = string
}

variable "domain" {
  type        = string
  description = "Domain of the project that you will be using."
}

variable "main_project_id" {
  description = "The project ID where the Access Context Manager resources will be created."
  type        = string
}

variable "organization_id" {
  description = "The organization ID."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "service_perimeters" {
  description = "List of service perimeters to create. Each service perimeter is a map containing 'name', 'description', 'status', and 'resources'."
  type = list(object({
    name        = string
    description = string
    status = object({
      restricted_services = list(string)
      resources           = list(string)
    })
  }))
}