# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

variable "stage_0_state_bucket" {
  description = "The name of the GCS bucket used for Stage 0 Terraform state."
  type        = string
}

variable "gemini_enterprise_domain" {
  description = "Your domain that you associated the reserved IP from stage 0 to"
  type        = string
}

# Variable for the customer-provided SSL certificate name
variable "ssl_certificate_name" {
  description = "The name of the pre-uploaded SSL certificate in Google Cloud."
  type        = string
  default     = ""
}

variable "cert_management_choice" {
  description = "Certificate management choice for external deployments: 'google_managed' or 'self_managed'."
  type        = string
  default     = "self_managed"
  validation {
    condition     = contains(["google_managed", "self_managed"], var.cert_management_choice)
    error_message = "Allowed values for cert_management_choice are 'google_managed' or 'self_managed'."
  }
}

variable "gemini_config_id" {
  description = "ID for your Gemini Enterprise instance after running Gem4Gov CLI"
  type        = string
}

variable "network_name" {
  description = "The name of the VPC network."
  type        = string
  default     = ""
}

variable "host_project_id" {
  description = "The ID of the host project where the VPC network resides."
  type        = string
  default     = ""
}
