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

# Pull tunnel secrets from GCP Secrets Manager
data "google_secret_manager_secret_version" "vpn_keys" {
  provider = google
  for_each = var.tunnel_secret_names
  project  = var.gcp_project_id
  secret   = each.value
  version  = "latest"
}

# MODULES
# This module creates a High Availability VPN connection between GCP and AWS.

module "gcp_aws_ha_vpn" {
  source = "./modules/gcp-aws-vpn" # The path to your module


  # Module variables

  vpn_name         = var.vpn_name
  aws_vpc_id       = var.aws_vpc_id
  gcp_network_name = var.gcp_network_name
  aws_bgp_asn      = var.aws_bgp_asn
  gcp_bgp_asn      = var.gcp_bgp_asn


  # Define Secrets
  # This transforms the data resource results into a simple map: { key_name = secret_value }
  preshared_keys = { for k, v in data.google_secret_manager_secret_version.vpn_keys : k => v.secret_data }

}