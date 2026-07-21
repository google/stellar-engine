resource "aws_vpn_gateway" "aws_vgw" {
  count           = var.create_aws_resources ? 1 : 0
  vpc_id          = data.aws_vpc.existing[0].id
  amazon_side_asn = var.aws_bgp_asn
  tags = {
    Name = "${var.name_prefix}-aws-vgw"
  }
}

resource "aws_customer_gateway" "cgw_gcp_if0" {
  count      = var.create_aws_resources ? 1 : 0
  bgp_asn    = google_compute_router.gcp_router.bgp[0].asn
  ip_address = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[0].ip_address
  type       = "ipsec.1"
  tags = {
    Name = "${var.name_prefix}-cgw-if0"
  }
}

resource "aws_customer_gateway" "cgw_gcp_if1" {
  count      = var.create_aws_resources ? 1 : 0
  bgp_asn    = google_compute_router.gcp_router.bgp[0].asn
  ip_address = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[1].ip_address
  type       = "ipsec.1"
  tags = {
    Name = "${var.name_prefix}-cgw-if1"
  }
}

resource "aws_vpn_connection" "conn1_to_gcp_if0" {
  count               = var.create_aws_resources ? 1 : 0
  vpn_gateway_id      = aws_vpn_gateway.aws_vgw[0].id
  customer_gateway_id = aws_customer_gateway.cgw_gcp_if0[0].id
  type                = "ipsec.1"
  static_routes_only  = false

  tunnel1_preshared_key = var.preshared_keys["conn1_tun1"]
  tunnel2_preshared_key = var.preshared_keys["conn1_tun2"]

  tags = {
    Name = "${var.name_prefix}-conn-1-if0"
  }
}

resource "aws_vpn_connection" "conn2_to_gcp_if1" {
  count               = var.create_aws_resources ? 1 : 0
  vpn_gateway_id      = aws_vpn_gateway.aws_vgw[0].id
  customer_gateway_id = aws_customer_gateway.cgw_gcp_if1[0].id
  type                = "ipsec.1"
  static_routes_only  = false

  tunnel1_preshared_key = var.preshared_keys["conn2_tun1"]
  tunnel2_preshared_key = var.preshared_keys["conn2_tun2"]

  tags = {
    Name = "${var.name_prefix}-conn-2-if1"
  }
}

resource "aws_vpn_gateway_route_propagation" "main" {
  count          = var.create_aws_resources ? 1 : 0
  route_table_id = data.aws_route_table.main[0].id
  vpn_gateway_id = aws_vpn_gateway.aws_vgw[0].id
}
