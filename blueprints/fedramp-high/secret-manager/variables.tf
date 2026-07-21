variable "iam" {
  description = "IAM bindings in {SECRET => {ROLE => [MEMBERS]}} format."
  type        = map(map(list(string)))
  default     = {}
}

variable "main_project_id" {
  description = "The Project ID where the secrets will be created."
  type        = string
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
  default     = "us-east4"
}

variable "secrets" {
  description = "Map of secrets to manage, their locations and KMS keys in {LOCATION => KEY} format."
  type = map(object({
    location = string # A location is required for every secret
    key      = string # A key is required for the location (the key and secret must be in the same region)
  }))
  default = {}
}

variable "zone" {
  description = "The Google Cloud zone within the specified region."
  type        = string
  default     = "us-east4-a"
}
