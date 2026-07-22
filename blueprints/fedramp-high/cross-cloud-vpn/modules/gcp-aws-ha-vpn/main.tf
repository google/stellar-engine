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

data "google_compute_network" "existing" {
  name    = var.gcp_network_name
  project = var.project_id
}

data "aws_vpc" "existing" {
  count = var.create_aws_resources ? 1 : 0
  id    = var.aws_vpc_id

  lifecycle {
    precondition {
      condition     = var.aws_vpc_id != null
      error_message = "var.aws_vpc_id must be provided when var.create_aws_resources is true."
    }
  }
}

data "aws_route_table" "main" {
  count  = var.create_aws_resources ? 1 : 0
  vpc_id = data.aws_vpc.existing[0].id
  filter {
    name   = "association.main"
    values = ["true"]
  }
}

locals {
  tunnels = {
    "tun1" = {
      gcp_iface_index      = 0
      aws_peer_iface_index = 0
      aws_psk              = var.preshared_keys["conn1_tun1"]
      external_ip          = var.create_aws_resources ? aws_vpn_connection.conn1_to_gcp_if0[0].tunnel1_address : try(var.aws_tunnel_details["tun1"].external_ip, null)
      gcp_bgp_ip           = var.create_aws_resources ? "${aws_vpn_connection.conn1_to_gcp_if0[0].tunnel1_cgw_inside_address}/${split("/", aws_vpn_connection.conn1_to_gcp_if0[0].tunnel1_inside_cidr)[1]}" : try(var.aws_tunnel_details["tun1"].gcp_bgp_ip, null)
      aws_bgp_ip           = var.create_aws_resources ? aws_vpn_connection.conn1_to_gcp_if0[0].tunnel1_vgw_inside_address : try(var.aws_tunnel_details["tun1"].aws_bgp_ip, null)
    },
    "tun2" = {
      gcp_iface_index      = 0
      aws_peer_iface_index = 1
      aws_psk              = var.preshared_keys["conn1_tun2"]
      external_ip          = var.create_aws_resources ? aws_vpn_connection.conn1_to_gcp_if0[0].tunnel2_address : try(var.aws_tunnel_details["tun2"].external_ip, null)
      gcp_bgp_ip           = var.create_aws_resources ? "${aws_vpn_connection.conn1_to_gcp_if0[0].tunnel2_cgw_inside_address}/${split("/", aws_vpn_connection.conn1_to_gcp_if0[0].tunnel2_inside_cidr)[1]}" : try(var.aws_tunnel_details["tun2"].gcp_bgp_ip, null)
      aws_bgp_ip           = var.create_aws_resources ? aws_vpn_connection.conn1_to_gcp_if0[0].tunnel2_vgw_inside_address : try(var.aws_tunnel_details["tun2"].aws_bgp_ip, null)
    },
    "tun3" = {
      gcp_iface_index      = 1
      aws_peer_iface_index = 2
      aws_psk              = var.preshared_keys["conn2_tun1"]
      external_ip          = var.create_aws_resources ? aws_vpn_connection.conn2_to_gcp_if1[0].tunnel1_address : try(var.aws_tunnel_details["tun3"].external_ip, null)
      gcp_bgp_ip           = var.create_aws_resources ? "${aws_vpn_connection.conn2_to_gcp_if1[0].tunnel1_cgw_inside_address}/${split("/", aws_vpn_connection.conn2_to_gcp_if1[0].tunnel1_inside_cidr)[1]}" : try(var.aws_tunnel_details["tun3"].gcp_bgp_ip, null)
      aws_bgp_ip           = var.create_aws_resources ? aws_vpn_connection.conn2_to_gcp_if1[0].tunnel1_vgw_inside_address : try(var.aws_tunnel_details["tun3"].aws_bgp_ip, null)
    },
    "tun4" = {
      gcp_iface_index      = 1
      aws_peer_iface_index = 3
      aws_psk              = var.preshared_keys["conn2_tun2"]
      external_ip          = var.create_aws_resources ? aws_vpn_connection.conn2_to_gcp_if1[0].tunnel2_address : try(var.aws_tunnel_details["tun4"].external_ip, null)
      gcp_bgp_ip           = var.create_aws_resources ? "${aws_vpn_connection.conn2_to_gcp_if1[0].tunnel2_cgw_inside_address}/${split("/", aws_vpn_connection.conn2_to_gcp_if1[0].tunnel2_inside_cidr)[1]}" : try(var.aws_tunnel_details["tun4"].gcp_bgp_ip, null)
      aws_bgp_ip           = var.create_aws_resources ? aws_vpn_connection.conn2_to_gcp_if1[0].tunnel2_vgw_inside_address : try(var.aws_tunnel_details["tun4"].aws_bgp_ip, null)
    }
  }
}
