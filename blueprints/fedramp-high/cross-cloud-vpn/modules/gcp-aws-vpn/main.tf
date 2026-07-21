# Look up existing VPCs and route tables to attach the new VPN resources.
data "aws_vpc" "existing" {
  id = var.aws_vpc_id
}
data "google_compute_network" "existing" {
  name = var.gcp_network_name
}
data "aws_route_table" "main" {
  vpc_id = var.aws_vpc_id
  filter {
    name   = "association.main"
    values = ["true"]
  }
}

# Locals
locals {
  tunnels = {
    # Tunnel 1: GCP IF0 -> AWS Conn1, Tun1
    "tun1" = {
      gcp_iface_index      = 0
      aws_peer_iface_index = 0
      aws_psk              = var.preshared_keys["conn1_tun1"]
      aws_cgw_inside_ip    = aws_vpn_connection.conn1_to_gcp_if0.tunnel1_cgw_inside_address
      aws_vgw_inside_ip    = aws_vpn_connection.conn1_to_gcp_if0.tunnel1_vgw_inside_address

      # Optimization: Calculate the mask here once
      # aws_inside_cidr is typically "169.254.x.x/30"
      aws_mask = split("/", aws_vpn_connection.conn1_to_gcp_if0.tunnel1_inside_cidr)[1]
    },
    # Tunnel 2: GCP IF0 -> AWS Conn1, Tun2
    "tun2" = {
      gcp_iface_index      = 0
      aws_peer_iface_index = 1
      aws_psk              = var.preshared_keys["conn1_tun2"]
      aws_cgw_inside_ip    = aws_vpn_connection.conn1_to_gcp_if0.tunnel2_cgw_inside_address
      aws_vgw_inside_ip    = aws_vpn_connection.conn1_to_gcp_if0.tunnel2_vgw_inside_address
      aws_mask             = split("/", aws_vpn_connection.conn1_to_gcp_if0.tunnel2_inside_cidr)[1]
    },
    # Tunnel 3: GCP IF1 -> AWS Conn2, Tun1
    "tun3" = {
      gcp_iface_index      = 1
      aws_peer_iface_index = 2
      aws_psk              = var.preshared_keys["conn2_tun1"]
      aws_cgw_inside_ip    = aws_vpn_connection.conn2_to_gcp_if1.tunnel1_cgw_inside_address
      aws_vgw_inside_ip    = aws_vpn_connection.conn2_to_gcp_if1.tunnel1_vgw_inside_address
      aws_mask             = split("/", aws_vpn_connection.conn2_to_gcp_if1.tunnel1_inside_cidr)[1]
    },
    # Tunnel 4: GCP IF1 -> AWS Conn2, Tun2
    "tun4" = {
      gcp_iface_index      = 1
      aws_peer_iface_index = 3
      aws_psk              = var.preshared_keys["conn2_tun2"]
      aws_cgw_inside_ip    = aws_vpn_connection.conn2_to_gcp_if1.tunnel2_cgw_inside_address
      aws_vgw_inside_ip    = aws_vpn_connection.conn2_to_gcp_if1.tunnel2_vgw_inside_address
      aws_mask             = split("/", aws_vpn_connection.conn2_to_gcp_if1.tunnel2_inside_cidr)[1]
    }
  }
}