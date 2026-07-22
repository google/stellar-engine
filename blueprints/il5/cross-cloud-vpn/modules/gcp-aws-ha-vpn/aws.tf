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
