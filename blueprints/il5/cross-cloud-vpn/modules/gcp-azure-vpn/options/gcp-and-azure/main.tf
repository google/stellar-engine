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

# Retrieve the PSKs from regional Secret Manager secrets
data "google_secret_manager_regional_secret_version" "psk_tun0" {
  secret   = var.secret_name_tunnel0
  version  = "latest"
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "psk_tun1" {
  secret   = var.secret_name_tunnel1
  version  = "latest"
  project  = var.project_id
  location = var.region
}

# Deploy both sides of the GCP-to-Azure HA VPN
module "gcp_azure_vpn_both" {
  source = "../../"

  project_id       = var.project_id
  name_prefix      = var.name_prefix
  gcp_network_name = var.gcp_network_name
  gcp_router_name  = var.gcp_router_name
  gcp_bgp_asn      = var.gcp_bgp_asn

  azure_bgp_asn = var.azure_bgp_asn

  # Enable module to directly manage Azure resources
  create_azure_resources = true

  # Azure targets for reading the Gateway and building Connections
  azure_resource_group_name = var.azure_resource_group_name
  azure_vpn_gateway_name    = var.azure_vpn_gateway_name

  stack_type          = var.stack_type
  gateway_ip_version  = var.gateway_ip_version
  tunnel_cipher_suite = var.tunnel_cipher_suite

  preshared_keys = {
    tunnel0 = data.google_secret_manager_regional_secret_version.psk_tun0.secret_data
    tunnel1 = data.google_secret_manager_regional_secret_version.psk_tun1.secret_data
  }
}
