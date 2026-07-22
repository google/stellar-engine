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

# GCP-side Resources for AWS VPN connectivity

# PSK Data Sources from GCP Secret Manager
data "google_secret_manager_regional_secret_version" "aws_psk_c1t1" {
  count    = (var.create_gcp_vpn_tunnels_aws && var.secret_name_aws_conn1_tun1 != null) ? 1 : 0
  secret   = var.secret_name_aws_conn1_tun1
  version  = var.aws_secret_version
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "aws_psk_c1t2" {
  count    = (var.create_gcp_vpn_tunnels_aws && var.secret_name_aws_conn1_tun2 != null) ? 1 : 0
  secret   = var.secret_name_aws_conn1_tun2
  version  = var.aws_secret_version
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "aws_psk_tenant1" {
  count    = (var.create_gcp_vpn_tunnels_aws && var.secret_name_aws_conn2_tun1 != null) ? 1 : 0
  secret   = var.secret_name_aws_conn2_tun1
  version  = var.aws_secret_version
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "aws_psk_tenant2" {
  count    = (var.create_gcp_vpn_tunnels_aws && var.secret_name_aws_conn2_tun2 != null) ? 1 : 0
  secret   = var.secret_name_aws_conn2_tun2
  version  = var.aws_secret_version
  project  = var.project_id
  location = var.region
}

locals {
  aws_tunnels = {
    "tun1" = {
      gcp_iface_index      = 0
      aws_peer_iface_index = 0
      aws_psk              = length(data.google_secret_manager_regional_secret_version.aws_psk_c1t1) > 0 ? data.google_secret_manager_regional_secret_version.aws_psk_c1t1[0].secret_data : try(var.secret_name_aws_conn1_tun1, null)
      external_ip          = try(var.aws_tunnel_details["tun1"].external_ip, null)
      gcp_bgp_ip           = try(var.aws_tunnel_details["tun1"].gcp_bgp_ip, null)
      aws_bgp_ip           = try(var.aws_tunnel_details["tun1"].aws_bgp_ip, null)
    },
    "tun2" = {
      gcp_iface_index      = 0
      aws_peer_iface_index = 1
      aws_psk              = length(data.google_secret_manager_regional_secret_version.aws_psk_c1t2) > 0 ? data.google_secret_manager_regional_secret_version.aws_psk_c1t2[0].secret_data : try(var.secret_name_aws_conn1_tun2, null)
      external_ip          = try(var.aws_tunnel_details["tun2"].external_ip, null)
      gcp_bgp_ip           = try(var.aws_tunnel_details["tun2"].gcp_bgp_ip, null)
      aws_bgp_ip           = try(var.aws_tunnel_details["tun2"].aws_bgp_ip, null)
    },
    "tun3" = {
      gcp_iface_index      = 1
      aws_peer_iface_index = 2
      aws_psk              = length(data.google_secret_manager_regional_secret_version.aws_psk_tenant1) > 0 ? data.google_secret_manager_regional_secret_version.aws_psk_tenant1[0].secret_data : try(var.secret_name_aws_conn2_tun1, null)
      external_ip          = try(var.aws_tunnel_details["tun3"].external_ip, null)
      gcp_bgp_ip           = try(var.aws_tunnel_details["tun3"].gcp_bgp_ip, null)
      aws_bgp_ip           = try(var.aws_tunnel_details["tun3"].aws_bgp_ip, null)
    },
    "tun4" = {
      gcp_iface_index      = 1
      aws_peer_iface_index = 3
      aws_psk              = length(data.google_secret_manager_regional_secret_version.aws_psk_tenant2) > 0 ? data.google_secret_manager_regional_secret_version.aws_psk_tenant2[0].secret_data : try(var.secret_name_aws_conn2_tun2, null)
      external_ip          = try(var.aws_tunnel_details["tun4"].external_ip, null)
      gcp_bgp_ip           = try(var.aws_tunnel_details["tun4"].gcp_bgp_ip, null)
      aws_bgp_ip           = try(var.aws_tunnel_details["tun4"].aws_bgp_ip, null)
    }
  }
}

resource "google_compute_ha_vpn_gateway" "aws_ha_gw" {
  count              = 1
  project            = var.project_id
  region             = var.region
  name               = "${var.name_prefix}-aws-ha-gw"
  network            = data.google_compute_network.existing.self_link
  stack_type         = var.stack_type
  gateway_ip_version = var.gateway_ip_version
}

resource "google_compute_external_vpn_gateway" "aws_peer_gw" {
  count = 1

  project         = var.project_id
  name            = "${var.name_prefix}-aws-peer-gw"
  redundancy_type = var.aws_redundancy_type

  dynamic "interface" {
    for_each = local.aws_tunnels
    content {
      id         = interface.value.aws_peer_iface_index
      ip_address = interface.value.external_ip
    }
  }
}

resource "google_compute_vpn_tunnel" "aws_tunnel" {
  for_each = var.create_gcp_vpn_tunnels_aws ? local.aws_tunnels : {}

  project                         = var.project_id
  region                          = var.region
  name                            = "${var.name_prefix}-aws-tun-${each.key}"
  vpn_gateway                     = google_compute_ha_vpn_gateway.aws_ha_gw[0].self_link
  vpn_gateway_interface           = each.value.gcp_iface_index
  peer_external_gateway           = google_compute_external_vpn_gateway.aws_peer_gw[0].self_link
  peer_external_gateway_interface = each.value.aws_peer_iface_index

  shared_secret = each.value.aws_psk
  router        = google_compute_router.gcp_router.self_link
  ike_version   = var.ike_version

  dynamic "cipher_suite" {
    for_each = (var.aws_tunnel_cipher_suite != null ? var.aws_tunnel_cipher_suite : var.tunnel_cipher_suite) != null ? [var.aws_tunnel_cipher_suite != null ? var.aws_tunnel_cipher_suite : var.tunnel_cipher_suite] : []
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

resource "google_compute_router_interface" "aws_if" {
  for_each = var.create_gcp_vpn_tunnels_aws ? local.aws_tunnels : {}

  project    = var.project_id
  region     = var.region
  name       = "${var.name_prefix}-aws-if-${each.key}"
  router     = google_compute_router.gcp_router.name
  ip_range   = each.value.gcp_bgp_ip
  vpn_tunnel = google_compute_vpn_tunnel.aws_tunnel[each.key].name
}

resource "google_compute_router_peer" "aws_peer" {
  for_each = var.create_gcp_vpn_tunnels_aws ? local.aws_tunnels : {}

  project         = var.project_id
  region          = var.region
  name            = "${var.name_prefix}-aws-peer-${each.key}"
  router          = google_compute_router.gcp_router.name
  interface       = google_compute_router_interface.aws_if[each.key].name
  peer_ip_address = each.value.aws_bgp_ip
  peer_asn        = var.aws_bgp_asn
}
