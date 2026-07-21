variable "address" {
  description = "The IP address of the private service connection."
  type        = string
  default     = "10.5.5.5"
}

variable "dns_code" {
  description = "Code to identify DNS resources in the form of `{dns_code}-{dns_type}`."
  type        = string
  default     = "dz"
}

variable "ip_name" {
  description = "Name of the private IP allocation."
  type        = string
  default     = "psconnect-ip"
}

variable "main_project_id" {
  description = "The GCP Project ID where the PSC will be created."
  type        = string
}

variable "network_name" {
  description = "The network ID where the PSC will be created."
  type        = string
}

variable "psc_name" {
  description = "Name of the forwarding rule used to create the PSC."
  type        = string
  default     = "pscforwardingrule"
}

variable "region" {
  description = "The GCP region."
  type        = string
}

variable "service" {
  description = "Target resource to receive the matched traffic. Only `all-apis` and `vpc-sc` are valid."
  type        = string
  default     = "all-apis"
}