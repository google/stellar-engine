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

variable "gitlab_uri" {
  description = "The URL hostname that the gitlab instance will be attached to."
  type        = string
}

variable "gke_initial_node_per_zone" {
  description = "Initial node amount per zone."
  type        = number
  default     = 1
}

variable "gke_name" {
  description = "Name of the GKE cluster."
  type        = string
  default     = "gitlab-cluster"
}

variable "instance_name" {
  description = "Name of the vm."
  type        = string
  default     = "gitlab-instance"
}

variable "kms_key" {
  description = "KMS key path."
  type        = string
}

variable "lb_name" {
  description = "Application load balancer name."
  type        = string
  default     = "gitlab-load-balancer"
}

variable "net_project" {
  description = "Project name of the spoke network. This project has the Stellar Engine deployed default VPC and is in the Networking folder."
  type        = string
}

variable "network" {
  description = "Network path to use for cluster, VM, and load balancer."
  type        = string
}

variable "network_name" {
  description = "Network name to use for Firewall rules. E.G. test-net-spoke."
  type        = string
}

variable "nodepool_node_count" {
  description = "Number of node per zone in the Nodepool."
  type = object({
    current = optional(number)
    initial = number
  })
  nullable = false
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

variable "subnetwork" {
  description = "Subnet path to use for cluster, VM, and load balancer."
  type        = string
}

variable "vm_name" {
  description = "VM name."
  type        = string
  default     = "gitlab-vm"
}

variable "zone" {
  description = "Zone to deploy to."
  type        = string
  default     = "us-east4-a"
}

variable "compute_image" {
  description = "The image used to provision the compute instance."
  type        = string
  default     = "projects/ubuntu-os-cloud/global/images/ubuntu-2404-noble-amd64-v20241219"
}

variable "gitlab_install_script_sha256" {
  description = "Expected SHA-256 hash for the GitLab package repository install script."
  type        = string
  default     = "47c124527729776870cf09cd6bd46a9b94f55d40c7545ca26640c75de86b560d"
}
