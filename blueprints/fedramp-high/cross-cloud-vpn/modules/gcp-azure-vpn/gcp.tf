resource "google_compute_ha_vpn_gateway" "gcp_ha_gw" {
  project            = var.project_id
  region             = var.region
  name               = "${var.name_prefix}-gcp-ha-gw"
  network            = data.google_compute_network.existing.self_link
  stack_type         = var.stack_type
  gateway_ip_version = var.gateway_ip_version
}

resource "google_compute_router" "gcp_router" {
  project = var.project_id
  region  = var.region
  name    = coalesce(var.gcp_router_name, "${var.name_prefix}-router")
  network = data.google_compute_network.existing.self_link
  bgp {
    asn              = var.gcp_bgp_asn
    identifier_range = var.gcp_bgp_identifier_range
  }
}


resource "google_compute_external_vpn_gateway" "azure_peer_gw" {
  project         = var.project_id
  name            = "${var.name_prefix}-azure-peer-gw"
  redundancy_type = "TWO_IPS_REDUNDANCY"

  interface {
    id         = 0
    ip_address = local.azure_ip_0
  }
  interface {
    id         = 1
    ip_address = local.azure_ip_1
  }

  lifecycle {
    precondition {
      condition     = local.azure_ip_0 != null && local.azure_ip_1 != null
      error_message = "Both var.azure_gateway_ip_0 and var.azure_gateway_ip_1 must be explicitly provided when var.create_azure_resources is false."
    }
  }
}

# Tunnels
resource "google_compute_vpn_tunnel" "tunnel0" {
  project                         = var.project_id
  region                          = var.region
  name                            = "${var.name_prefix}-gcp-tun0"
  vpn_gateway                     = google_compute_ha_vpn_gateway.gcp_ha_gw.self_link
  vpn_gateway_interface           = 0
  peer_external_gateway           = google_compute_external_vpn_gateway.azure_peer_gw.self_link
  peer_external_gateway_interface = 0

  shared_secret = var.preshared_keys["tunnel0"]
  router        = google_compute_router.gcp_router.self_link
  ike_version   = 2

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

resource "google_compute_vpn_tunnel" "tunnel1" {
  project                         = var.project_id
  region                          = var.region
  name                            = "${var.name_prefix}-gcp-tun1"
  vpn_gateway                     = google_compute_ha_vpn_gateway.gcp_ha_gw.self_link
  vpn_gateway_interface           = 1
  peer_external_gateway           = google_compute_external_vpn_gateway.azure_peer_gw.self_link
  peer_external_gateway_interface = 1

  shared_secret = var.preshared_keys["tunnel1"]
  router        = google_compute_router.gcp_router.self_link
  ike_version   = 2

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
resource "google_compute_router_interface" "if0" {
  project    = var.project_id
  region     = var.region
  name       = "${var.name_prefix}-gcp-if0"
  router     = google_compute_router.gcp_router.name
  ip_range   = "${var.gcp_bgp_apipa_ip_0}/30"
  vpn_tunnel = google_compute_vpn_tunnel.tunnel0.name
}

resource "google_compute_router_interface" "if1" {
  project    = var.project_id
  region     = var.region
  name       = "${var.name_prefix}-gcp-if1"
  router     = google_compute_router.gcp_router.name
  ip_range   = "${var.gcp_bgp_apipa_ip_1}/30"
  vpn_tunnel = google_compute_vpn_tunnel.tunnel1.name
}

# BGP Peers
resource "google_compute_router_peer" "peer0" {
  project         = var.project_id
  region          = var.region
  name            = "${var.name_prefix}-gcp-peer0"
  router          = google_compute_router.gcp_router.name
  interface       = google_compute_router_interface.if0.name
  peer_ip_address = var.azure_bgp_apipa_ip_0
  peer_asn        = var.azure_bgp_asn
}

resource "google_compute_router_peer" "peer1" {
  project         = var.project_id
  region          = var.region
  name            = "${var.name_prefix}-gcp-peer1"
  router          = google_compute_router.gcp_router.name
  interface       = google_compute_router_interface.if1.name
  peer_ip_address = var.azure_bgp_apipa_ip_1
  peer_asn        = var.azure_bgp_asn
}
