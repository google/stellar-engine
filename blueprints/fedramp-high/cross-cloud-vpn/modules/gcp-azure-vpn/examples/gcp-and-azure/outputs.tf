output "gcp_ha_gateway_name" {
  description = "The name of the provisioned GCP HA VPN Gateway."
  value       = module.gcp_azure_vpn_both.gcp_ha_gateway_name
}

output "tunnel_details" {
  description = "Detailed mapping of the IPs and ASNs for both sides of the VPN tunnels."
  value       = module.gcp_azure_vpn_both.tunnel_details
}
