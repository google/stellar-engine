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

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "kms_key_name" {
  description = "Short name of the existing KMS crypto key (for example `my-key`) used for Pub/Sub, not the full resource path. It is looked up in the key ring named by `kms_keyring_name`. Required in practice: the lookup fails when this is left at the `null` default."
  type        = string
  default     = null
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Project id."
  type        = string
}

variable "name" {
  description = "Name of DataFusion instance."
  type        = string
}

variable "network_name" {
  description = "Short name of the existing VPC network (for example `prod-spoke-0`), not the full resource path. It is looked up in `network_project_id`."
  type        = string
}

variable "network_project_id" {
  description = "Landing project id."
  type        = string
}

variable "region" {
  description = "Location to deploy job."
  type        = string
}

variable "subnetwork_name" {
  description = "Short name of the existing subnetwork (for example `prod-subnet-0`), not the full resource path. It is looked up in `region` and `network_project_id`."
  type        = string
}
