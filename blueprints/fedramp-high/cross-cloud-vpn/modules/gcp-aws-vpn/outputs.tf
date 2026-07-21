output "aws_bgp_asn" {
  description = "The BGP ASN for the AWS side."
  value       = aws_vpn_gateway.aws_vgw.amazon_side_asn
}

output "aws_connection_1_tunnel_1_ip" {
  description = "The public IP for AWS Connection 1, Tunnel 1 (peers with GCP IF0)."
  value       = aws_vpn_connection.conn1_to_gcp_if0.tunnel1_address
}

output "aws_connection_1_tunnel_2_ip" {
  description = "The public IP for AWS Connection 1, Tunnel 2 (peers with GCP IF0)."
  value       = aws_vpn_connection.conn1_to_gcp_if0.tunnel2_address
}

output "aws_connection_2_tunnel_1_ip" {
  description = "The public IP for AWS Connection 2, Tunnel 1 (peers with GCP IF1)."
  value       = aws_vpn_connection.conn2_to_gcp_if1.tunnel1_address
}

output "aws_connection_2_tunnel_2_ip" {
  description = "The public IP for AWS Connection 2, Tunnel 2 (peers with GCP IF1)."
  value       = aws_vpn_connection.conn2_to_gcp_if1.tunnel2_address
}

output "aws_vpn_gateway_id" {
  description = "The ID of the AWS Virtual Private Gateway (VGW)."
  value       = aws_vpn_gateway.aws_vgw.id
}

output "gcp_bgp_asn" {
  description = "The BGP ASN for the GCP side."
  value       = google_compute_router.gcp_router.bgp[0].asn
}

output "gcp_cloud_router_name" {
  description = "The name of the GCP Cloud Router handling BGP."
  value       = google_compute_router.gcp_router.name
}

output "gcp_ha_gateway_interface_0_ip" {
  description = "The public IP address for GCP's HA VPN Interface 0."
  value       = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[0].ip_address
}

output "gcp_ha_gateway_interface_1_ip" {
  description = "The public IP address for GCP's HA VPN Interface 1."
  value       = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[1].ip_address
}