data "google_compute_network" "existing" {
  name    = var.gcp_network_name
  project = var.project_id
}

/*
data "azurerm_resource_group" "rg" {
  count = var.create_azure_resources ? 1 : 0
  name  = var.azure_resource_group_name

  lifecycle {
    precondition {
      condition     = var.azure_resource_group_name != null
      error_message = "var.azure_resource_group_name must be provided when var.create_azure_resources is true."
    }
  }
}

data "azurerm_virtual_network_gateway" "existing" {
  count               = var.create_azure_resources ? 1 : 0
  name                = var.azure_vpn_gateway_name
  resource_group_name = data.azurerm_resource_group.rg[0].name

  lifecycle {
    precondition {
      condition     = var.azure_vpn_gateway_name != null
      error_message = "var.azure_vpn_gateway_name must be provided when var.create_azure_resources is true."
    }
  }
}

# In Azure, the IP string is often not directly exposed, so we extract the Public IP resource ID and fetch it.
data "azurerm_public_ip" "gw_ip0" {
  count               = (var.create_azure_resources && var.azure_gateway_ip_0 == null) ? 1 : 0
  name                = element(split("/", data.azurerm_virtual_network_gateway.existing[0].ip_configuration[0].public_ip_address_id), length(split("/", data.azurerm_virtual_network_gateway.existing[0].ip_configuration[0].public_ip_address_id)) - 1)
  resource_group_name = element(split("/", data.azurerm_virtual_network_gateway.existing[0].ip_configuration[0].public_ip_address_id), 4)
}

data "azurerm_public_ip" "gw_ip1" {
  count               = (var.create_azure_resources && var.azure_gateway_ip_1 == null) ? 1 : 0
  name                = element(split("/", data.azurerm_virtual_network_gateway.existing[0].ip_configuration[1].public_ip_address_id), length(split("/", data.azurerm_virtual_network_gateway.existing[0].ip_configuration[1].public_ip_address_id)) - 1)
  resource_group_name = element(split("/", data.azurerm_virtual_network_gateway.existing[0].ip_configuration[1].public_ip_address_id), 4)
}
*/

locals {
  azure_ip_0 = var.azure_gateway_ip_0 != null ? var.azure_gateway_ip_0 : null # try(data.azurerm_public_ip.gw_ip0[0].ip_address, null)
  azure_ip_1 = var.azure_gateway_ip_1 != null ? var.azure_gateway_ip_1 : null # try(data.azurerm_public_ip.gw_ip1[0].ip_address, null)
}
