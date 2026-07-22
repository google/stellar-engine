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

output "gcp_ha_gateway_name" {
  description = "The name of the GCP HA VPN Gateway."
  value       = google_compute_ha_vpn_gateway.gcp_ha_gw.name
}

output "gcp_ha_gateway_interface_0_ip" {
  description = "The public IP address for GCP's HA VPN Interface 0."
  value       = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[0].ip_address
}

output "gcp_ha_gateway_interface_1_ip" {
  description = "The public IP address for GCP's HA VPN Interface 1."
  value       = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[1].ip_address
}

output "azure_virtual_network_gateway_ip_0" {
  description = "The public IP address for Azure's Virtual Network Gateway Interface 0."
  value       = local.azure_ip_0
}

output "azure_virtual_network_gateway_ip_1" {
  description = "The public IP address for Azure's Virtual Network Gateway Interface 1."
  value       = local.azure_ip_1
}

output "gcp_bgp_asn" {
  description = "The BGP ASN for the GCP side."
  value       = google_compute_router.gcp_router.bgp[0].asn
}

output "azure_bgp_asn" {
  description = "The BGP ASN for the Azure side."
  value       = var.azure_bgp_asn
}

output "tunnel_details" {
  description = "Detailed mapping of both GCP and Azure sides for each VPN tunnel."
  value = {
    tunnel0 = {
      gcp = {
        interface_id = 0
        public_ip    = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[0].ip_address
        bgp_ip       = var.gcp_bgp_apipa_ip_0
        asn          = google_compute_router.gcp_router.bgp[0].asn
      }
      azure = {
        interface_id = 0
        public_ip    = local.azure_ip_0
        bgp_ip       = var.azure_bgp_apipa_ip_0
        asn          = var.azure_bgp_asn
      }
    }
    tunnel1 = {
      gcp = {
        interface_id = 1
        public_ip    = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[1].ip_address
        bgp_ip       = var.gcp_bgp_apipa_ip_1
        asn          = google_compute_router.gcp_router.bgp[0].asn
      }
      azure = {
        interface_id = 1
        public_ip    = local.azure_ip_1
        bgp_ip       = var.azure_bgp_apipa_ip_1
        asn          = var.azure_bgp_asn
      }
    }
  }
}
