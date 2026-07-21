/**
 * Copyright 2022 Google LLC
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

output "local_network_peering" {
  description = "Network peering resource."
  value       = module.peering.local_network_peering
}

output "peer_network_peering" {
  description = "Peer network peering resource."
  value       = module.peering.peer_network_peering
}

output "subnet_ipv6_external_prefixes" {
  description = "Map of subnet external IPv6 prefixes keyed by name."
  value       = module.vpc.subnet_ipv6_external_prefixes
}

output "subnet_regions" {
  description = "Map of subnet regions keyed by name."
  value       = module.vpc.subnet_regions
}

output "subnet_secondary_ranges" {
  description = "Map of subnet secondary ranges keyed by name."
  value       = module.vpc.subnet_secondary_ranges
}

output "subnet_self_links" {
  description = "Map of subnet self links keyed by name."
  value       = module.vpc.subnet_self_links
}

output "subnets" {
  description = "Subnet resources."
  value       = module.vpc.subnets
}

output "vpc-network" {
  description = "Network resource."
  value       = module.vpc.network
}

output "vpc-network-self_link" {
  description = "Network self link."
  value       = module.vpc.self_link
}

output "vpc-network_attachment_ids" {
  description = "IDs of network attachments."
  value       = module.vpc.network_attachment_ids
}

output "vpc-subnet_ids" {
  description = "Map of subnet IDs keyed by name."
  value       = module.vpc.subnet_ids
}

output "vpc-subnet_ips" {
  description = "Map of subnet address ranges keyed by name."
  value       = module.vpc.subnet_ips
}
