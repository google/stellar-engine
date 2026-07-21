output "gcp_ha_gateway_name" {
  description = "The name of the GCP HA VPN Gateway."
  value       = google_compute_ha_vpn_gateway.gcp_ha_gw.name
}

output "gcp_bgp_asn" {
  description = "The BGP ASN for the GCP side."
  value       = google_compute_router.gcp_router.bgp[0].asn
}

output "aws_bgp_asn" {
  description = "The BGP ASN for the AWS side."
  value       = var.aws_bgp_asn
}

output "aws_vpn_gateway_id" {
  description = "The ID of the AWS Virtual Private Gateway (VGW)."
  value       = var.create_aws_resources ? aws_vpn_gateway.aws_vgw[0].id : null
}

output "tunnel_details" {
  description = "Detailed mapping of both GCP and AWS sides for each VPN tunnel."
  value = {
    for k, t in local.tunnels : k => {
      gcp = {
        interface_id = t.gcp_iface_index
        public_ip    = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[t.gcp_iface_index].ip_address
        bgp_ip       = t.gcp_bgp_ip
        asn          = google_compute_router.gcp_router.bgp[0].asn
      }
      aws = {
        interface_id = t.aws_peer_iface_index
        public_ip    = t.external_ip
        bgp_ip       = t.aws_bgp_ip
        asn          = var.aws_bgp_asn
      }
    }
  }
}
