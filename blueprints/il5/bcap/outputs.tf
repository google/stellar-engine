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

output "attachment_names" {
  description = "Names of the created VLAN attachments."
  value = {
    for k, attachment in google_compute_interconnect_attachment.attachments : k => attachment.name
  }
}

output "bcap_subnets" {
  description = "Details of the created BCAP Subnets for DoD IP space (map keyed by 'subnet1', 'subnet2'). Includes calculated CIDRs."
  value       = google_compute_subnetwork.bcap_subnets
}

output "cloud_routers" {
  description = "Details of the created Cloud Routers (map keyed by 'router1', 'router2')."
  value       = google_compute_router.routers
}

output "dod_split_cidr_blocks" {
  description = "The calculated /25 CIDR blocks for the two DoD subnets."
  value       = local.dod_split_cidr_blocks
}

output "pairing_keys" {
  description = "Pairing keys for each VLAN attachment. Provide these to the BCAP/DISA team."
  value = {
    for k, attachment in google_compute_interconnect_attachment.attachments : k => attachment.pairing_key
  }
  sensitive = true
}

output "vlan_attachments" {
  description = "Details of the created VLAN attachments."
  value       = google_compute_interconnect_attachment.attachments
}

output "vpc_network" {
  description = "Details of the created VPC Network."
  value       = google_compute_network.vpc_network
}
