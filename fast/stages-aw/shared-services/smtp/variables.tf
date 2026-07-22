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

variable "allowed_client_ranges" {
  description = "Internal CIDR ranges permitted to send mail through the SMTP relay over TCP 25. Defaults to all RFC 1918 space."
  type        = list(string)
  default     = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
}

variable "automation" {
  description = "Automation resources created by the bootstrap stage. Used to write SMTP relay IPs to the GCS outputs bucket for downstream consumption."
  type = object({
    outputs_bucket = string
  })
}

variable "boot_disk_image" {
  description = "Boot disk image for SMTP relay VMs. The startup script installs Postfix via RHUI if not present. Use a hardened RHEL 8 image for full STIG compliance."
  type        = string
  default     = "projects/rhel-cloud/global/images/family/rhel-8"
}

variable "boot_disk_size" {
  description = "Boot disk size in GB for SMTP relay VMs. Must be at least as large as the boot image (20 GB for RHEL 8)."
  type        = number
  default     = 20
}

variable "create_cloud_nat" {
  description = "Create a Cloud NAT and router to provide SMTP relay VMs with outbound access for RHUI package operations. Set to false if the shared-services VPC already has a Cloud NAT."
  type        = bool
  default     = true
}

variable "disa_relay_hosts" {
  description = "DISA EESG relay IP addresses. Must be IP addresses (not hostnames) as they are also used in firewall destination_ranges."
  type        = list(string)
  validation {
    condition     = length(var.disa_relay_hosts) >= 1
    error_message = "At least one DISA relay host IP address must be specified."
  }
}

variable "disa_relay_port" {
  description = "TCP port for the DISA EESG relay. Standard SMTP is 25."
  type        = number
  default     = 25
}

variable "encryption_key" {
  description = "KMS key self-link for CMEK disk encryption on SMTP relay VMs. Required for IL5 deployments where constraints/gcp.restrictNonCmekServices is enforced."
  type        = string
}

variable "hub_project_id" {
  description = "The GCP project ID where SMTP relay resources will be deployed. Must be the project that owns the VPC (the Security Host Project), since Cloud Router, Cloud NAT, and firewall rules cannot cross-project reference networks."
  type        = string
}

variable "instance_name_prefix" {
  description = "Name prefix for SMTP relay VM instances."
  type        = string
  default     = "smtp-relay"
}

variable "machine_type" {
  description = "Machine type for SMTP relay VMs. e2-small provides sufficient resources for Postfix workloads."
  type        = string
  default     = "e2-small"
}

variable "network" {
  description = "Self-link of the VPC network to attach SMTP relay VMs to."
  type        = string
}

variable "prefix" {
  description = "Prefix applied to resource names for org-level naming consistency (e.g. 'da1'). Set to null to disable prefixing."
  type        = string
  default     = null
  validation {
    condition     = var.prefix != ""
    error_message = "Prefix cannot be empty, use null instead."
  }
}

variable "region" {
  description = "GCP region for SMTP relay VM deployment."
  type        = string
}

variable "smtp_domain" {
  description = "Domain name used in Postfix mydomain directive."
  type        = string
  default     = "example.com"
}

variable "smtp_hostname" {
  description = "Hostname used in Postfix myhostname directive."
  type        = string
  default     = "smtp.example.com"
}

variable "subnetwork" {
  description = "Self-link of the subnetwork to attach SMTP relay VMs to."
  type        = string
}
