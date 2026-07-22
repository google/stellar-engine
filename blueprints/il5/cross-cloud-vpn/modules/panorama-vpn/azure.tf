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

/*
# Local Network Gateways to represent the GCP interfaces in Azure
resource "azurerm_local_network_gateway" "gcp_lng_0" {
  count               = var.create_azure_resources ? 1 : 0
  name                = "${var.name_prefix}-gcp-lng0"
  resource_group_name = data.azurerm_resource_group.rg[0].name
  location            = data.azurerm_resource_group.rg[0].location
  gateway_address     = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[0].ip_address

  bgp_settings {
    asn                 = google_compute_router.gcp_router.bgp[0].asn
    bgp_peering_address = var.gcp_bgp_apipa_ip_0
  }
}

resource "azurerm_local_network_gateway" "gcp_lng_1" {
  count               = var.create_azure_resources ? 1 : 0
  name                = "${var.name_prefix}-gcp-lng1"
  resource_group_name = data.azurerm_resource_group.rg[0].name
  location            = data.azurerm_resource_group.rg[0].location
  gateway_address     = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[1].ip_address

  bgp_settings {
    asn                 = google_compute_router.gcp_router.bgp[0].asn
    bgp_peering_address = var.gcp_bgp_apipa_ip_1
  }
}

# VPN Connections
resource "azurerm_virtual_network_gateway_connection" "azure_conn_0" {
  count               = var.create_azure_resources ? 1 : 0
  name                = "${var.name_prefix}-conn0"
  location            = data.azurerm_resource_group.rg[0].location
  resource_group_name = data.azurerm_resource_group.rg[0].name

  type                       = "IPsec"
  virtual_network_gateway_id = data.azurerm_virtual_network_gateway.existing[0].id
  local_network_gateway_id   = azurerm_local_network_gateway.gcp_lng_0[0].id

  shared_key  = var.preshared_keys["tunnel0"]
  bgp_enabled = true

  custom_bgp_addresses {
    primary = var.azure_bgp_apipa_ip_0
  }
}

resource "azurerm_virtual_network_gateway_connection" "azure_conn_1" {
  count               = var.create_azure_resources ? 1 : 0
  name                = "${var.name_prefix}-conn1"
  location            = data.azurerm_resource_group.rg[0].location
  resource_group_name = data.azurerm_resource_group.rg[0].name

  type                       = "IPsec"
  virtual_network_gateway_id = data.azurerm_virtual_network_gateway.existing[0].id
  local_network_gateway_id   = azurerm_local_network_gateway.gcp_lng_1[0].id

  shared_key  = var.preshared_keys["tunnel1"]
  bgp_enabled = true

  custom_bgp_addresses {
    primary = var.azure_bgp_apipa_ip_1
  }
}
*/
