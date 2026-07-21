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


resource "google_compute_external_vpn_gateway" "aws_peer_gw" {
  count = var.create_gcp_vpn_tunnels ? 1 : 0

  project         = var.project_id
  name            = "${var.name_prefix}-aws-peer-gw"
  redundancy_type = "FOUR_IPS_REDUNDANCY"

  interface {
    id         = 0
    ip_address = local.tunnels["tun1"].external_ip
  }
  interface {
    id         = 1
    ip_address = local.tunnels["tun2"].external_ip
  }
  interface {
    id         = 2
    ip_address = local.tunnels["tun3"].external_ip
  }
  interface {
    id         = 3
    ip_address = local.tunnels["tun4"].external_ip
  }

  lifecycle {
    precondition {
      condition     = var.create_aws_resources || var.aws_tunnel_details != null
      error_message = "var.aws_tunnel_details must be explicitly provided when var.create_aws_resources is false."
    }
  }
}

resource "google_compute_vpn_tunnel" "tunnel" {
  for_each = var.create_gcp_vpn_tunnels ? local.tunnels : {}

  project                         = var.project_id
  region                          = var.region
  name                            = "${var.name_prefix}-gcp-${each.key}"
  vpn_gateway                     = google_compute_ha_vpn_gateway.gcp_ha_gw.self_link
  vpn_gateway_interface           = each.value.gcp_iface_index
  peer_external_gateway           = google_compute_external_vpn_gateway.aws_peer_gw[0].self_link
  peer_external_gateway_interface = each.value.aws_peer_iface_index

  shared_secret = each.value.aws_psk
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

resource "google_compute_router_interface" "if" {
  for_each = var.create_gcp_vpn_tunnels ? local.tunnels : {}

  project    = var.project_id
  region     = var.region
  name       = "${var.name_prefix}-gcp-if-${each.key}"
  router     = google_compute_router.gcp_router.name
  ip_range   = each.value.gcp_bgp_ip
  vpn_tunnel = google_compute_vpn_tunnel.tunnel[each.key].name
}

resource "google_compute_router_peer" "peer" {
  for_each = var.create_gcp_vpn_tunnels ? local.tunnels : {}

  project         = var.project_id
  region          = var.region
  name            = "${var.name_prefix}-gcp-peer-${each.key}"
  router          = google_compute_router.gcp_router.name
  interface       = google_compute_router_interface.if[each.key].name
  peer_ip_address = each.value.aws_bgp_ip
  peer_asn        = var.aws_bgp_asn
}
# change
