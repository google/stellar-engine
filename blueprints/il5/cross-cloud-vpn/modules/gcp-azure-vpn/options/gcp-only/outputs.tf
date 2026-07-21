output "gcp_ha_gateway_name" {
  description = "The name of the provisioned GCP HA VPN Gateway."
  value       = module.gcp_azure_vpn_gcp_only.gcp_ha_gateway_name
}

output "gcp_bgp_asn" {
  description = "The BGP ASN for the GCP Cloud Router."
  value       = module.gcp_azure_vpn_gcp_only.gcp_bgp_asn
}

output "tunnel_details" {
  description = "Detailed mapping of the IPs and ASNs for both sides of the VPN tunnels."
  value       = module.gcp_azure_vpn_gcp_only.tunnel_details
}
