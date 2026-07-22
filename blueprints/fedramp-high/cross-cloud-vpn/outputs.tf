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

output "aws_bgp_asn" {
  description = "The BGP ASN for the AWS side."
  value       = module.gcp_aws_ha_vpn.aws_bgp_asn
}

output "aws_connection_1_tunnel_1_ip" {
  description = "The public IP for AWS Connection 1, Tunnel 1."
  value       = module.gcp_aws_ha_vpn.aws_connection_1_tunnel_1_ip
}

output "aws_connection_1_tunnel_2_ip" {
  description = "The public IP for AWS Connection 1, Tunnel 2."
  value       = module.gcp_aws_ha_vpn.aws_connection_1_tunnel_2_ip
}

output "aws_connection_2_tunnel_1_ip" {
  description = "The public IP for AWS Connection 2, Tunnel 1."
  value       = module.gcp_aws_ha_vpn.aws_connection_2_tunnel_1_ip
}

output "aws_connection_2_tunnel_2_ip" {
  description = "The public IP for AWS Connection 2, Tunnel 2."
  value       = module.gcp_aws_ha_vpn.aws_connection_2_tunnel_2_ip
}

output "aws_vpn_gateway_id" {
  description = "The ID of the AWS Virtual Private Gateway (VGW)."
  value       = module.gcp_aws_ha_vpn.aws_vpn_gateway_id
}

output "gcp_bgp_asn" {
  description = "The BGP ASN for the GCP side."
  value       = module.gcp_aws_ha_vpn.gcp_bgp_asn
}

output "gcp_cloud_router_name" {
  description = "The name of the GCP Cloud Router handling BGP."
  value       = module.gcp_aws_ha_vpn.gcp_cloud_router_name
}

output "gcp_ha_gateway_interface_0_ip" {
  description = "The public IP address for GCP's HA VPN Interface 0."
  value       = module.gcp_aws_ha_vpn.gcp_ha_gateway_interface_0_ip
}

output "gcp_ha_gateway_interface_1_ip" {
  description = "The public IP address for GCP's HA VPN Interface 1."
  value       = module.gcp_aws_ha_vpn.gcp_ha_gateway_interface_1_ip
}