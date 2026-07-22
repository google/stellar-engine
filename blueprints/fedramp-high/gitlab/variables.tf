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

variable "bucket_name" {
  description = "Name of the bucket that will hold keycloak yaml files."
  type        = string
  default     = "gitlab-config"
}

variable "existing_cluster" {
  description = "A cluster already exists that will be used for Gitlab deployment."
  type        = bool
  default     = false
}

variable "gitlab_allow_source_ranges" {
  description = "A list of IP ranges for the GitLab firewall rule's source."
  type        = list(string)
  default     = []
}

variable "gke_name" {
  description = "Name of the GKE cluster."
  type        = string
  default     = "gitlab-cluster"
}

variable "kms_key" {
  description = "KMS key path."
  type        = string
  default     = null
}

variable "net_project" {
  description = "Project name of the spoke network. This project has the Stellar Engine Landing Zone deployed default VPC and is in the Networking folder."
  type        = string
  default     = null
}

variable "network" {
  description = "Network path to use for cluster, VM, and load balancer."
  type        = string
  default     = null
}

variable "network_name" {
  description = "Network name to use for Firewall rules. E.G. test-net-spoke."
  type        = string
  default     = null
}

variable "nodepool_node_count" {
  description = "Number of node per zone in the Nodepool."
  type = object({
    current = optional(number)
    initial = number
  })
  default = {
    initial = 0
  }
}

variable "project_id" {
  type        = string
  description = "Project ID where the GitLab cluster, VM, and load balancer will be deployed to."
}

variable "region" {
  description = "Region for deployment."
  type        = string
  default     = "us-east4"
}

variable "sa" {
  description = "Service account to run GKE and VM."
  type        = string
}

variable "subnet_pod_range" {
  description = "The name of the secondary IP range to be used for GKE Pods."
  type        = string
  default     = null
}

variable "subnet_service_range" {
  description = "The name of the secondary IP range to be used for GKE Services."
  type        = string
}

variable "subnetwork" {
  description = "Subnet path to use for cluster, and load balancer."
  type        = string
  default     = null
}
