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

data "google_secret_manager_regional_secret_version" "psk_conn1_tun1" {
  secret   = var.secret_name_conn1_tun1
  version  = "latest"
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "psk_conn1_tun2" {
  secret   = var.secret_name_conn1_tun2
  version  = "latest"
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "psk_conn2_tun1" {
  secret   = var.secret_name_conn2_tun1
  version  = "latest"
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "psk_conn2_tun2" {
  secret   = var.secret_name_conn2_tun2
  version  = "latest"
  project  = var.project_id
  location = var.region
}

module "gcp_aws_vpn_gcp_only" {
  source = "../../"

  project_id       = var.project_id
  region           = var.region
  name_prefix      = var.name_prefix
  gcp_network_name = var.gcp_network_name
  gcp_router_name  = var.gcp_router_name
  gcp_bgp_asn      = var.gcp_bgp_asn

  aws_bgp_asn = var.aws_bgp_asn

  create_gcp_vpn_tunnels = var.create_gcp_vpn_tunnels
  create_aws_resources   = false
  aws_tunnel_details     = var.aws_tunnel_details

  stack_type          = var.stack_type
  gateway_ip_version  = var.gateway_ip_version
  tunnel_cipher_suite = var.tunnel_cipher_suite

  preshared_keys = {
    conn1_tun1 = data.google_secret_manager_regional_secret_version.psk_conn1_tun1.secret_data
    conn1_tun2 = data.google_secret_manager_regional_secret_version.psk_conn1_tun2.secret_data
    conn2_tun1 = data.google_secret_manager_regional_secret_version.psk_conn2_tun1.secret_data
    conn2_tun2 = data.google_secret_manager_regional_secret_version.psk_conn2_tun2.secret_data
  }
}
