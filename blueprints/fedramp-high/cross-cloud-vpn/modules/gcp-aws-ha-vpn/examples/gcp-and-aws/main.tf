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

module "gcp_aws_vpn_both" {
  source = "../../"

  project_id       = var.project_id
  name_prefix      = var.name_prefix
  gcp_network_name = var.gcp_network_name
  gcp_router_name  = var.gcp_router_name
  gcp_bgp_asn      = var.gcp_bgp_asn

  aws_bgp_asn = var.aws_bgp_asn

  create_aws_resources = true
  aws_vpc_id           = var.aws_vpc_id

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
