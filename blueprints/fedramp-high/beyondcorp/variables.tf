variable "endpoint_name" {
  description = "Name for endpoint."
  type        = string
}

variable "iap_user_email" {
  description = "User or group email for IAP access."
  type        = string
}

variable "main_project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "oauth_client_id" {
  description = "OAuth Client ID for IAP."
  type        = string
}

variable "oauth_client_secret" {
  description = "OAuth Client Secret for IAP."
  type        = string
}

variable "organization_id" {
  description = "GCP Organization ID."
  type        = string
}

variable "policy_title" {
  description = "Title for the Access Context Manager Policy."
  type        = string
}

variable "region" {
  description = "Region for deployment."
  type        = string
}




