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
# --- Peering Connection Outputs ---
output "local_network_peering" {
  description = "The peering resource for the local VPC side of the connection."
  value       = module.peering.local_network_peering
}

output "peer_network_peering" {
  description = "The peering resource for the peer VPC side of the connection."
  value       = module.peering.peer_network_peering
}

# --- Local VPC Outputs (First VPC created by this blueprint) ---
output "local_vpc_network" {
  description = "The network resource object for the local VPC created by this blueprint."
  value       = module.vpc_networks["local"].network
}

output "local_vpc_network_self_link" {
  description = "The self-link for the local VPC created by this blueprint."
  value       = module.vpc_networks["local"].self_link
}

output "local_vpc_subnet_ids" {
  description = "A map of subnet IDs keyed by name for the local VPC."
  value       = module.vpc_networks["local"].subnet_ids
}

output "local_vpc_subnet_ips" {
  description = "A map of subnet address ranges keyed by name for the local VPC."
  value       = module.vpc_networks["local"].subnet_ips
}

output "local_vpc_subnet_self_links" {
  description = "A map of subnet self links keyed by name for the local VPC."
  value       = module.vpc_networks["local"].subnet_self_links
}

output "local_vpc_subnet_regions" {
  description = "A map of subnet regions keyed by name for the local VPC."
  value       = module.vpc_networks["local"].subnet_regions
}

# Optional detailed subnet outputs for local VPC
output "local_vpc_subnets" {
  description = "List of subnet resources for the local VPC."
  value       = module.vpc_networks["local"].subnets
}

output "local_vpc_subnet_secondary_ranges" {
  description = "Map of subnet secondary ranges keyed by name for the local VPC."
  value       = module.vpc_networks["local"].subnet_secondary_ranges
}

output "local_vpc_subnet_ipv6_external_prefixes" {
  description = "Map of subnet external IPv6 prefixes keyed by name for the local VPC."
  value       = module.vpc_networks["local"].subnet_ipv6_external_prefixes
}

output "local_vpc_network_attachment_ids" {
  description = "IDs of network attachments for the local VPC."
  value       = module.vpc_networks["local"].network_attachment_ids
}

# --- Peer VPC Outputs (Second VPC created by this blueprint) ---
output "peer_vpc_network" {
  description = "The network resource object for the peer VPC created by this blueprint."
  value       = module.vpc_networks["peer"].network
}

output "peer_vpc_network_self_link" {
  description = "The self-link for the peer VPC created by this blueprint."
  value       = module.vpc_networks["peer"].self_link
}

output "peer_vpc_subnet_ids" {
  description = "A map of subnet IDs keyed by name for the peer VPC."
  value       = module.vpc_networks["peer"].subnet_ids
}

output "peer_vpc_subnet_ips" {
  description = "A map of subnet address ranges keyed by name for the peer VPC."
  value       = module.vpc_networks["peer"].subnet_ips
}

output "peer_vpc_subnet_self_links" {
  description = "A map of subnet self links keyed by name for the peer VPC."
  value       = module.vpc_networks["peer"].subnet_self_links
}

output "peer_vpc_subnet_regions" {
  description = "A map of subnet regions keyed by name for the peer VPC."
  value       = module.vpc_networks["peer"].subnet_regions
}

# Optional detailed subnet outputs for peer VPC
output "peer_vpc_subnets" {
  description = "List of subnet resources for the peer VPC."
  value       = module.vpc_networks["peer"].subnets
}

output "peer_vpc_subnet_secondary_ranges" {
  description = "Map of subnet secondary ranges keyed by name for the peer VPC."
  value       = module.vpc_networks["peer"].subnet_secondary_ranges
}

output "peer_vpc_subnet_ipv6_external_prefixes" {
  description = "Map of subnet external IPv6 prefixes keyed by name for the peer VPC."
  value       = module.vpc_networks["peer"].subnet_ipv6_external_prefixes
}

output "peer_vpc_network_attachment_ids" {
  description = "IDs of network attachments for the peer VPC."
  value       = module.vpc_networks["peer"].network_attachment_ids
}

