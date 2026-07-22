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
variable "allowed_firewall_ports" {
  description = "The list of the Allowed Ports."
  type        = list(any)
  #Example  default     = ["22", "443"]
}

variable "compute_service_account_id" {
  description = "The Service Account for Compute Engine."
  type        = string
  # Example  default = "compute-service-account"
}

variable "core_project_id" {
  description = "Core Project ID."
  type        = string
}

variable "disksize" {
  description = "Provide the Size of the size in GB."
  type        = number
  default     = 40
}

variable "instance_name" {
  description = "Provide the name of the Shielded Compute VM."
  type        = string
  default     = "shielded-vm-inst"
}

variable "instance_type" {
  description = "The Machine Type for the Shielded Compute VM."
  type        = string
  default     = "e2-micro"
  #Example  default     = "e2-micro"
}

variable "kms_key_name" {
  description = "The full self-link (projects/../locations/../cryptoKeys/..) of the existing KMS key to use for encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type        = string
}

variable "main_project_id" {
  description = "Project ID."
  type        = string
}

variable "network_name" {
  description = "The name of the VPC."
  type        = string
}

variable "network_project_id" {
  description = "Project that the Compute Engine VPC is located."
  type        = string
}

variable "region" {
  description = "Region of the Shielded Compute VM."
  type        = string
  default     = "us-east4"
}

variable "source_ranges_allowed" {
  description = "The List of the source IP CIDR range allowed to connect to the Shielded Compute VM."
  type        = list(any)
  # #Example   default     = ["10.0.1.0/24"]
}

variable "subnetwork_name" {
  description = "The name of the subnet."
  type        = string
}

variable "zone" {
  description = "Zone of the Shielded Compute VM us-east4-c , us-east4-a, us-east4-b."
  type        = string
  default     = "us-east4-c"
}
