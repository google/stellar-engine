# Panorama VPN Resources
data "google_secret_manager_regional_secret_version" "pano_psk_tun0" {
  secret   = var.secret_name_panorama_tunnel0
  project  = local.panorama_project
  location = var.region
}

data "google_secret_manager_regional_secret_version" "pano_psk_tun1" {
  secret   = var.secret_name_panorama_tunnel1
  project  = local.panorama_project
  location = var.region
}

locals {
  panorama_ip_0    = var.panorama_gateway_ip_0 != null ? var.panorama_gateway_ip_0 : null
  panorama_ip_1    = var.panorama_gateway_ip_1 != null ? var.panorama_gateway_ip_1 : null
  panorama_project = coalesce(var.panorama_project_id, var.project_id)
  panorama_vpc     = coalesce(var.panorama_vpc_name, var.gcp_network_name)
}

data "google_compute_network" "panorama_vpc" {
  count   = 1
  name    = local.panorama_vpc
  project = local.panorama_project
}

resource "google_compute_router" "panorama_router" {
  count   = 1
  project = local.panorama_project
  region  = var.region
  name    = coalesce(var.panorama_router_name, "${var.name_prefix}-mgmt-router")
  network = data.google_compute_network.panorama_vpc[0].self_link
  bgp {
    asn              = var.mgmt_bgp_asn
    identifier_range = var.gcp_bgp_identifier_range
  }
}

# GCP Resources for Panorama VPN

resource "google_compute_ha_vpn_gateway" "panorama_ha_gw" {
  count              = 1
  project            = local.panorama_project
  region             = var.region
  name               = "${var.name_prefix}-panorama-ha-gw"
  network            = data.google_compute_network.panorama_vpc[0].self_link
  stack_type         = var.stack_type
  gateway_ip_version = var.gateway_ip_version
}

resource "google_compute_external_vpn_gateway" "panorama_peer_gw" {
  count           = 1
  project         = local.panorama_project
  name            = "${var.name_prefix}-panorama-peer-gw"
  redundancy_type = var.panorama_redundancy_type

  interface {
    id         = 0
    ip_address = local.panorama_ip_0
  }
  interface {
    id         = 1
    ip_address = local.panorama_ip_1
  }

  lifecycle {
    precondition {
      condition     = local.panorama_ip_0 != null && local.panorama_ip_1 != null
      error_message = "Both var.panorama_gateway_ip_0 and var.panorama_gateway_ip_1 must be provided."
    }
  }
}

# Tunnels
resource "google_compute_vpn_tunnel" "panorama_tunnel0" {
  count                           = var.enable_panorama_vpn ? 1 : 0
  project                         = local.panorama_project
  region                          = var.region
  name                            = "${var.name_prefix}-panorama-tun0"
  vpn_gateway                     = google_compute_ha_vpn_gateway.panorama_ha_gw[0].self_link
  vpn_gateway_interface           = 0
  peer_external_gateway           = google_compute_external_vpn_gateway.panorama_peer_gw[0].self_link
  peer_external_gateway_interface = 0

  shared_secret = data.google_secret_manager_regional_secret_version.pano_psk_tun0.secret_data
  router        = google_compute_router.panorama_router[0].self_link
  ike_version   = var.ike_version

  dynamic "cipher_suite" {
    for_each = var.tunnel_cipher_suite != null ? [var.tunnel_cipher_suite] : []
    content {
      dynamic "phase1" {
        for_each = cipher_suite.value.phase1 != null ? [cipher_suite.value.phase1] : []
        content {
          encryption = length(phase1.value.encryption) > 0 ? phase1.value.encryption : null
          integrity  = length(phase1.value.integrity) > 0 ? phase1.value.integrity : null
          prf        = length(phase1.value.prf) > 0 ? phase1.value.prf : null
          dh         = length(phase1.value.dh) > 0 ? phase1.value.dh : null
        }
      }
      dynamic "phase2" {
        for_each = cipher_suite.value.phase2 != null ? [cipher_suite.value.phase2] : []
        content {
          encryption = length(phase2.value.encryption) > 0 ? phase2.value.encryption : null
          integrity  = length(phase2.value.integrity) > 0 ? phase2.value.integrity : null
          pfs        = length(phase2.value.pfs) > 0 ? phase2.value.pfs : null
        }
      }
    }
  }
}

resource "google_compute_vpn_tunnel" "panorama_tunnel1" {
  count                           = var.enable_panorama_vpn ? 1 : 0
  project                         = local.panorama_project
  region                          = var.region
  name                            = "${var.name_prefix}-panorama-tun1"
  vpn_gateway                     = google_compute_ha_vpn_gateway.panorama_ha_gw[0].self_link
  vpn_gateway_interface           = 1
  peer_external_gateway           = google_compute_external_vpn_gateway.panorama_peer_gw[0].self_link
  peer_external_gateway_interface = 1

  shared_secret = data.google_secret_manager_regional_secret_version.pano_psk_tun1.secret_data
  router        = google_compute_router.panorama_router[0].self_link
  ike_version   = var.ike_version

  dynamic "cipher_suite" {
    for_each = var.tunnel_cipher_suite != null ? [var.tunnel_cipher_suite] : []
    content {
      dynamic "phase1" {
        for_each = cipher_suite.value.phase1 != null ? [cipher_suite.value.phase1] : []
        content {
          encryption = length(phase1.value.encryption) > 0 ? phase1.value.encryption : null
          integrity  = length(phase1.value.integrity) > 0 ? phase1.value.integrity : null
          prf        = length(phase1.value.prf) > 0 ? phase1.value.prf : null
          dh         = length(phase1.value.dh) > 0 ? phase1.value.dh : null
        }
      }
      dynamic "phase2" {
        for_each = cipher_suite.value.phase2 != null ? [cipher_suite.value.phase2] : []
        content {
          encryption = length(phase2.value.encryption) > 0 ? phase2.value.encryption : null
          integrity  = length(phase2.value.integrity) > 0 ? phase2.value.integrity : null
          pfs        = length(phase2.value.pfs) > 0 ? phase2.value.pfs : null
        }
      }
    }
  }
}

# BGP Interfaces
resource "google_compute_router_interface" "panorama_if0" {
  count      = var.enable_panorama_vpn ? 1 : 0
  project    = local.panorama_project
  region     = var.region
  name       = "${var.name_prefix}-panorama-if0"
  router     = google_compute_router.panorama_router[0].name
  ip_range   = "${var.panorama_gcp_bgp_apipa_ip_0}/${var.vpn_bgp_mask}"
  vpn_tunnel = var.enable_panorama_vpn ? google_compute_vpn_tunnel.panorama_tunnel0[0].name : null
}

resource "google_compute_router_interface" "panorama_if1" {
  count      = var.enable_panorama_vpn ? 1 : 0
  project    = local.panorama_project
  region     = var.region
  name       = "${var.name_prefix}-panorama-if1"
  router     = google_compute_router.panorama_router[0].name
  ip_range   = "${var.panorama_gcp_bgp_apipa_ip_1}/${var.vpn_bgp_mask}"
  vpn_tunnel = var.enable_panorama_vpn ? google_compute_vpn_tunnel.panorama_tunnel1[0].name : null
}

# BGP Peers
resource "google_compute_router_peer" "panorama_peer0" {
  count           = var.enable_panorama_vpn ? 1 : 0
  project         = local.panorama_project
  region          = var.region
  name            = "${var.name_prefix}-panorama-peer0"
  router          = google_compute_router.panorama_router[0].name
  interface       = var.enable_panorama_vpn ? google_compute_router_interface.panorama_if0[0].name : null
  peer_ip_address = var.panorama_peer_bgp_apipa_ip_0
  peer_asn        = var.panorama_bgp_asn
}

resource "google_compute_router_peer" "panorama_peer1" {
  count           = var.enable_panorama_vpn ? 1 : 0
  project         = local.panorama_project
  region          = var.region
  name            = "${var.name_prefix}-panorama-peer1"
  router          = google_compute_router.panorama_router[0].name
  interface       = var.enable_panorama_vpn ? google_compute_router_interface.panorama_if1[0].name : null
  peer_ip_address = var.panorama_peer_bgp_apipa_ip_1
  peer_asn        = var.panorama_bgp_asn
}

