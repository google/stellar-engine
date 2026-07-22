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

# PSK Data Sources from GCP Secret Manager
data "google_secret_manager_regional_secret_version" "azure_psk_tun0" {
  count    = (var.enable_azure_vpn && var.secret_name_azure_tunnel0 != null) ? 1 : 0
  secret   = var.secret_name_azure_tunnel0
  project  = var.project_id
  location = var.region
}

data "google_secret_manager_regional_secret_version" "azure_psk_tun1" {
  count    = (var.enable_azure_vpn && var.secret_name_azure_tunnel1 != null) ? 1 : 0
  secret   = var.secret_name_azure_tunnel1
  project  = var.project_id
  location = var.region
}

locals {
  azure_ip_0 = var.azure_gateway_ip_0 != null ? var.azure_gateway_ip_0 : null
  azure_ip_1 = var.azure_gateway_ip_1 != null ? var.azure_gateway_ip_1 : null

  azure_tunnels = {
    "tun0" = {
      gcp_iface_index  = 0
      peer_iface_index = 0
      psk              = length(data.google_secret_manager_regional_secret_version.azure_psk_tun0) > 0 ? data.google_secret_manager_regional_secret_version.azure_psk_tun0[0].secret_data : try(var.secret_name_azure_tunnel0, null)
      external_ip      = local.azure_ip_0
      gcp_bgp_ip       = "${var.azure_gcp_bgp_apipa_ip_0}/${var.vpn_bgp_mask}"
      peer_bgp_ip      = var.azure_peer_bgp_apipa_ip_0
    },
    "tun1" = {
      gcp_iface_index  = 1
      peer_iface_index = 1
      psk              = length(data.google_secret_manager_regional_secret_version.azure_psk_tun1) > 0 ? data.google_secret_manager_regional_secret_version.azure_psk_tun1[0].secret_data : try(var.secret_name_azure_tunnel1, null)
      external_ip      = local.azure_ip_1
      gcp_bgp_ip       = "${var.azure_gcp_bgp_apipa_ip_1}/${var.vpn_bgp_mask}"
      peer_bgp_ip      = var.azure_peer_bgp_apipa_ip_1
    }
  }
}

# GCP Resources for Azure VPN

resource "google_compute_ha_vpn_gateway" "azure_ha_gw" {
  count              = 1
  project            = var.project_id
  region             = var.region
  name               = "${var.name_prefix}-azure-ha-gw"
  network            = var.gcp_network_name
  stack_type         = var.stack_type
  gateway_ip_version = var.gateway_ip_version
}

resource "google_compute_external_vpn_gateway" "azure_peer_gw" {
  count           = 1
  project         = var.project_id
  name            = "${var.name_prefix}-azure-vpn-gw"
  redundancy_type = var.azure_redundancy_type

  dynamic "interface" {
    for_each = local.azure_tunnels
    content {
      id         = interface.value.peer_iface_index
      ip_address = interface.value.external_ip
    }
  }

  lifecycle {
    precondition {
      condition     = local.azure_ip_0 != null && local.azure_ip_1 != null
      error_message = "Both var.azure_gateway_ip_0 and var.azure_gateway_ip_1 must be explicitly provided."
    }
  }
}

resource "google_compute_vpn_tunnel" "azure_tunnel" {
  for_each = var.enable_azure_vpn ? local.azure_tunnels : {}

  project                         = var.project_id
  region                          = var.region
  name                            = "${var.name_prefix}-azure-${each.key}"
  vpn_gateway                     = google_compute_ha_vpn_gateway.azure_ha_gw[0].self_link
  vpn_gateway_interface           = each.value.gcp_iface_index
  peer_external_gateway           = google_compute_external_vpn_gateway.azure_peer_gw[0].self_link
  peer_external_gateway_interface = each.value.peer_iface_index

  shared_secret = each.value.psk
  router        = google_compute_router.gcp_router.self_link
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

resource "google_compute_router_interface" "azure_if" {
  for_each = var.enable_azure_vpn ? local.azure_tunnels : {}

  project    = var.project_id
  region     = var.region
  name       = "${var.name_prefix}-azure-if-${each.key}"
  router     = google_compute_router.gcp_router.name
  ip_range   = each.value.gcp_bgp_ip
  vpn_tunnel = google_compute_vpn_tunnel.azure_tunnel[each.key].name
}

resource "google_compute_router_peer" "azure_peer" {
  for_each = var.enable_azure_vpn ? local.azure_tunnels : {}

  project         = var.project_id
  region          = var.region
  name            = "${var.name_prefix}-azure-peer-${each.key}"
  router          = google_compute_router.gcp_router.name
  interface       = google_compute_router_interface.azure_if[each.key].name
  peer_ip_address = each.value.peer_bgp_ip
  peer_asn        = var.azure_bgp_asn
}
