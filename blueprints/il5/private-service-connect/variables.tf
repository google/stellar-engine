/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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