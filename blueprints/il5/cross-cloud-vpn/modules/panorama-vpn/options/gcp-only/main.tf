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

# Deploy the GCP side of the GCP-to-Azure HA VPN
module "gcp_azure_vpn_gcp_only" {
  source = "../../"

  project_id       = var.project_id
  region           = var.region
  name_prefix      = var.name_prefix
  gcp_network_name = var.gcp_network_name
  gcp_router_name  = var.gcp_router_name
  gcp_bgp_asn      = var.gcp_bgp_asn

  azure_bgp_asn = var.azure_bgp_asn

  # Explicitly instruct the module NOT to look up or create Azure resources
  # create_azure_resources = false

  # Required since we are not discovering Azure resources dynamically
  azure_gateway_ip_0 = var.azure_gateway_ip_0
  azure_gateway_ip_1 = var.azure_gateway_ip_1

  stack_type          = var.stack_type
  gateway_ip_version  = var.gateway_ip_version
  tunnel_cipher_suite = var.tunnel_cipher_suite

  gcp_bgp_apipa_ip_0       = var.gcp_bgp_apipa_ip_0
  azure_bgp_apipa_ip_0     = var.azure_bgp_apipa_ip_0
  gcp_bgp_apipa_ip_1       = var.gcp_bgp_apipa_ip_1
  azure_bgp_apipa_ip_1     = var.azure_bgp_apipa_ip_1
  gcp_bgp_identifier_range = var.gcp_bgp_identifier_range

  preshared_keys = {
    tunnel0 = data.google_secret_manager_regional_secret_version.psk_tun0.secret_data
    tunnel1 = data.google_secret_manager_regional_secret_version.psk_tun0.secret_data
  }
}
