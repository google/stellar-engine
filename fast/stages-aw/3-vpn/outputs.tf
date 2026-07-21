# AWS Outputs

output "aws_gcp_ha_gateway_name" {
  description = "The name of the GCP HA VPN Gateway for AWS."
  value       = try(google_compute_ha_vpn_gateway.aws_ha_gw[0].name, null)
}

output "aws_tunnel_details" {
  description = "Detailed mapping for AWS VPN tunnels."
  value = var.create_gcp_vpn_tunnels_aws ? {
    for k, t in local.aws_tunnels : k => {
      gcp = {
        interface_id = t.gcp_iface_index
        public_ip    = try(google_compute_ha_vpn_gateway.aws_ha_gw[0].vpn_interfaces[t.gcp_iface_index].ip_address, null)
        bgp_ip       = t.gcp_bgp_ip
        asn          = var.gcp_bgp_asn
      }
      aws = {
        interface_id = t.aws_peer_iface_index
        public_ip    = t.external_ip
        bgp_ip       = t.aws_bgp_ip
        asn          = var.aws_bgp_asn
      }
    }
  } : null
}

# Azure Outputs

output "azure_gcp_ha_gateway_name" {
  description = "The name of the GCP HA VPN Gateway for Azure."
  value       = try(google_compute_ha_vpn_gateway.azure_ha_gw[0].name, null)
}

output "azure_tunnel_details" {
  description = "Detailed mapping for Azure VPN tunnels."
  value = var.enable_azure_vpn ? {
    tunnel0 = {
      gcp = {
        interface_id = 0
        public_ip    = try(google_compute_ha_vpn_gateway.azure_ha_gw[0].vpn_interfaces[0].ip_address, null)
        bgp_ip       = var.azure_gcp_bgp_apipa_ip_0
        asn          = var.gcp_bgp_asn
      }
      azure = {
        interface_id = 0
        public_ip    = var.azure_gateway_ip_0
        bgp_ip       = var.azure_peer_bgp_apipa_ip_0
        asn          = var.azure_bgp_asn
      }
    }
    tunnel1 = {
      gcp = {
        interface_id = 1
        public_ip    = try(google_compute_ha_vpn_gateway.azure_ha_gw[0].vpn_interfaces[1].ip_address, null)
        bgp_ip       = var.azure_gcp_bgp_apipa_ip_1
        asn          = var.gcp_bgp_asn
      }
      azure = {
        interface_id = 1
        public_ip    = var.azure_gateway_ip_1
        bgp_ip       = var.azure_peer_bgp_apipa_ip_1
        asn          = var.azure_bgp_asn
      }
    }
  } : null
}

# Panorama Outputs

output "panorama_gcp_ha_gateway_name" {
  description = "The name of the GCP HA VPN Gateway for Panorama."
  value       = try(google_compute_ha_vpn_gateway.panorama_ha_gw[0].name, null)
}

output "panorama_tunnel_details" {
  description = "Detailed mapping for Panorama VPN tunnels."
  value = var.enable_panorama_vpn ? {
    tunnel0 = {
      gcp = {
        interface_id = 0
        public_ip    = try(google_compute_ha_vpn_gateway.panorama_ha_gw[0].vpn_interfaces[0].ip_address, null)
        bgp_ip       = var.panorama_gcp_bgp_apipa_ip_0
        asn          = var.gcp_bgp_asn
      }
      panorama = {
        interface_id = 0
        public_ip    = var.panorama_gateway_ip_0
        bgp_ip       = var.panorama_peer_bgp_apipa_ip_0
        asn          = var.panorama_bgp_asn
      }
    }
    tunnel1 = {
      gcp = {
        interface_id = 1
        public_ip    = try(google_compute_ha_vpn_gateway.panorama_ha_gw[0].vpn_interfaces[1].ip_address, null)
        bgp_ip       = var.panorama_gcp_bgp_apipa_ip_1
        asn          = var.gcp_bgp_asn
      }
      panorama = {
        interface_id = 1
        public_ip    = var.panorama_gateway_ip_1
        bgp_ip       = var.panorama_peer_bgp_apipa_ip_1
        asn          = var.panorama_bgp_asn
      }
    }
  } : null
}

# Variabllized Configurations

output "vpn_network_config" {
  description = "Network-wide BGP and redundancy parameters."
  value = {
    bgp_mask_length          = var.vpn_bgp_mask
    aws_redundancy_type      = var.aws_redundancy_type
    azure_redundancy_type    = var.azure_redundancy_type
    panorama_redundancy_type = var.panorama_redundancy_type
  }
}

output "vpn_security_config" {
  description = "Security parameters used for all VPN tunnels."
  value = {
    ike_version         = var.ike_version
    aws_secret_version  = var.aws_secret_version
    global_cipher_suite = var.tunnel_cipher_suite
    aws_cipher_override = var.aws_tunnel_cipher_suite
  }
}
