resource "google_compute_ha_vpn_gateway" "gcp_ha_gw" {
  name    = "${var.vpn_name}-gcp-ha-gw"
  network = data.google_compute_network.existing.self_link
}

resource "google_compute_router" "gcp_router" {
  name    = "${var.vpn_name}-gcp-router"
  network = data.google_compute_network.existing.self_link
  bgp {
    asn = var.gcp_bgp_asn
  }
}

resource "google_compute_external_vpn_gateway" "aws_peer_gw" {
  name            = "${var.vpn_name}-aws-peer-gw"
  redundancy_type = "FOUR_IPS_REDUNDANCY"

  interface {
    id         = 0
    ip_address = aws_vpn_connection.conn1_to_gcp_if0.tunnel1_address
  }
  interface {
    id         = 1
    ip_address = aws_vpn_connection.conn1_to_gcp_if0.tunnel2_address
  }
  interface {
    id         = 2
    ip_address = aws_vpn_connection.conn2_to_gcp_if1.tunnel1_address
  }
  interface {
    id         = 3
    ip_address = aws_vpn_connection.conn2_to_gcp_if1.tunnel2_address
  }
}

# Tunnels

resource "google_compute_vpn_tunnel" "tunnel" {
  for_each = local.tunnels

  name                            = "${var.vpn_name}-gcp-${each.key}"
  vpn_gateway                     = google_compute_ha_vpn_gateway.gcp_ha_gw.self_link
  vpn_gateway_interface           = each.value.gcp_iface_index
  peer_external_gateway           = google_compute_external_vpn_gateway.aws_peer_gw.self_link
  peer_external_gateway_interface = each.value.aws_peer_iface_index

  shared_secret = each.value.aws_psk
  router        = google_compute_router.gcp_router.self_link
  ike_version   = 2
}

# BGP Interfaces (Using for_each from main.tf locals)
resource "google_compute_router_interface" "if" {
  for_each = local.tunnels

  name     = "${var.vpn_name}-gcp-if-${each.key}"
  router   = google_compute_router.gcp_router.name
  ip_range = "${each.value.aws_cgw_inside_ip}/${each.value.aws_mask}"

  vpn_tunnel = google_compute_vpn_tunnel.tunnel[each.key].name
}

# BGP Peers (Using for_each from main.tf locals)
resource "google_compute_router_peer" "peer" {
  for_each = local.tunnels

  name   = "${var.vpn_name}-gcp-peer-${each.key}"
  router = google_compute_router.gcp_router.name

  interface = google_compute_router_interface.if[each.key].name

  peer_ip_address = each.value.aws_vgw_inside_ip
  peer_asn        = var.aws_bgp_asn
}