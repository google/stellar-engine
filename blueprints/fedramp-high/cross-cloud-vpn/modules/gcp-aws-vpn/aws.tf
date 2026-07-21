# AWS Virtual Private Gateway

resource "aws_vpn_gateway" "aws_vgw" {
  vpc_id          = data.aws_vpc.existing.id
  amazon_side_asn = var.aws_bgp_asn
  tags = {
    Name = "${var.vpn_name}-aws-vgw"
  }
}

# AWS Customer Gateway 1 (Points to GCP Interface 0)

resource "aws_customer_gateway" "cgw_gcp_if0" {
  bgp_asn    = var.gcp_bgp_asn
  ip_address = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[0].ip_address
  type       = "ipsec.1"
  tags = {
    Name = "${var.vpn_name}-cgw-if0"
  }
}

# AWS Customer Gateway 2 (Points to GCP Interface 1)

resource "aws_customer_gateway" "cgw_gcp_if1" {
  bgp_asn    = var.gcp_bgp_asn
  ip_address = google_compute_ha_vpn_gateway.gcp_ha_gw.vpn_interfaces[1].ip_address
  type       = "ipsec.1"
  tags = {
    Name = "${var.vpn_name}-cgw-if1"
  }
}

# VPN Connection 1 (AWS VGW <-> GCP IF0)

resource "aws_vpn_connection" "conn1_to_gcp_if0" {
  vpn_gateway_id      = aws_vpn_gateway.aws_vgw.id
  customer_gateway_id = aws_customer_gateway.cgw_gcp_if0.id
  type                = "ipsec.1"
  static_routes_only  = false # We use BGP

  # Securely inject the keys from the variable map
  tunnel1_preshared_key = var.preshared_keys["conn1_tun1"]
  tunnel2_preshared_key = var.preshared_keys["conn1_tun2"]

  tags = {
    Name = "${var.vpn_name}-conn-1-if0"
  }
}

# VPN Connection 2 (AWS VGW <-> GCP IF1)

resource "aws_vpn_connection" "conn2_to_gcp_if1" {
  vpn_gateway_id      = aws_vpn_gateway.aws_vgw.id
  customer_gateway_id = aws_customer_gateway.cgw_gcp_if1.id
  type                = "ipsec.1"
  static_routes_only  = false

  # Securely inject the keys from the variable map
  tunnel1_preshared_key = var.preshared_keys["conn2_tun1"]
  tunnel2_preshared_key = var.preshared_keys["conn2_tun2"]

  tags = {
    Name = "${var.vpn_name}-conn-2-if1"
  }
}

# Route Propagation

resource "aws_vpn_gateway_route_propagation" "main" {
  route_table_id = data.aws_route_table.main.id
  vpn_gateway_id = aws_vpn_gateway.aws_vgw.id
}