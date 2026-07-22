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
variable "auto_delete" {
  description = "Persistent Disk auto delete options."
  type        = bool
  # Example default = true
}

variable "compute_service_account_id" {
  description = "The Service Account for Compute Engine."
  type        = string
  # Example default = "computeblue"
}

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "instance_name" {
  description = "Provide the name of the Compute Instance."
  type        = string
  #Example default     = "Compute-Instance-Name-1"
}

variable "instance_type" {
  description = "The Machine Type for the Compute Engine VM."
  type        = string
  default     = "n2d-standard-2"
  #Example  default     = "e2-micro"
}

variable "kms_key_name" {
  description = "The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for disk encryption."
  type        = string
  # Example: "projects/my-kms-project/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-compute-key"
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Main project ID."
  type        = string
}

variable "network_name" {
  description = "The name of the existing VPC network to use."
  type        = string
}

variable "network_project_id" {
  description = "Project that the Compute Engine VPC is located."
  type        = string
}

variable "region" {
  description = "Location of the Compute Engine VM."
  type        = string
  default     = "us-east4"
}

variable "subnetwork_name" {
  description = "The name of the existing subnetwork to use within the specified VPC network and region."
  type        = string
}

variable "zone" {
  description = "Zone of the Compute Engine VM us-east4-c , us-east4-a, us-east4-b."
  type        = string
  default     = "us-east4-c"
}
