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