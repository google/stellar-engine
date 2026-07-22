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

variable "bucket-name" {
  description = "Name of the bucket that will hold keycloak yaml files."
  type        = string
  default     = "keycloak-config"
}

variable "domain" {
  description = "Domain of the keycloak instance."
  type        = string
}

variable "kms_key" {
  description = "Project path to a KMS key."
  type        = string
}

variable "network" {
  description = "Network of the Bastion VM and GKE Cluster."
  type        = string
}

variable "network_project_id" {
  description = "Project ID that hosts the VPC that will be used by keycloak."
  type        = string
}

variable "node_count" {
  description = "Amount of initial nodes in the nodepool."
  type        = number
  default     = 1
}

variable "pod_range" {
  description = "GKE pod range name."
  type        = string
}

variable "project_id" {
  description = "ID of the project that keycloak will be deployed in."
  type        = string
}

variable "region" {
  description = "Region to deploy keycloak to."
  type        = string
  default     = "us-east4"
}

variable "service_range" {
  description = "GKE service range name."
  type        = string
}

variable "subnetwork" {
  description = "Subnetwork of the Bastion VM and GKE Cluster."
  type        = string
}
