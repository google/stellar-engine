# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

locals {
  # Cloud DNS uses 35.199.192.0/19 as the source range for outbound
  # forwarding queries. Advertising it ensures peer networks can route
  # DNS replies back across the VPN tunnels.
  advertised_ip_ranges = merge(
    var.advertise_dns_forwarding_range ? {
      "35.199.192.0/19" = "Cloud DNS forwarding range"
    } : {},
    var.custom_advertised_ip_ranges
  )
  custom_advertise = (
    length(local.advertised_ip_ranges) > 0
    ? {
      all_subnets = true
      ip_ranges   = local.advertised_ip_ranges
    }
    : null
  )
  # Merge peer phase overrides with defaults per phase so modules/net-vpn-ha
  # never receives a partial cipher_suite with a null phase1 or phase2 block.
  _peer_cipher_suites = {
    for peer_key, peer in var.peers : peer_key => (
      peer.cipher_suite == null && var.cipher_suite == null
      ? null
      : {
        phase1 = (
          try(peer.cipher_suite.phase1, null) != null
          ? peer.cipher_suite.phase1
          : try(var.cipher_suite.phase1, null)
        )
        phase2 = (
          try(peer.cipher_suite.phase2, null) != null
          ? peer.cipher_suite.phase2
          : try(var.cipher_suite.phase2, null)
        )
      }
    )
  }
  # Convert empty cipher lists to null so AEAD algorithms such as
  # AES-GCM-16-256 never submit an empty integrity field to Cloud VPN.
  normalized_cipher_suites = {
    for peer_key, cs in local._peer_cipher_suites : peer_key => (
      cs == null ? null : {
        phase1 = cs.phase1 == null ? null : {
          dh = (
            try(length(cs.phase1.dh), 0) > 0 ? cs.phase1.dh : null
          )
          encryption = (
            try(length(cs.phase1.encryption), 0) > 0
            ? cs.phase1.encryption
            : null
          )
          integrity = (
            try(length(cs.phase1.integrity), 0) > 0
            ? cs.phase1.integrity
            : null
          )
          prf = (
            try(length(cs.phase1.prf), 0) > 0 ? cs.phase1.prf : null
          )
        }
        phase2 = cs.phase2 == null ? null : {
          encryption = (
            try(length(cs.phase2.encryption), 0) > 0
            ? cs.phase2.encryption
            : null
          )
          integrity = (
            try(length(cs.phase2.integrity), 0) > 0
            ? cs.phase2.integrity
            : null
          )
          pfs = (
            try(length(cs.phase2.pfs), 0) > 0 ? cs.phase2.pfs : null
          )
        }
      }
    )
  }
  _regional_secret_re = (
    "^projects/[a-zA-Z0-9-]+/locations/[a-z]+-[a-z]+[0-9]+/secrets/"
  )
  _tunnel_secrets = merge({}, [
    for peer_key, peer in var.peers : {
      for tun_key, tun in peer.tunnels : "${peer_key}/${tun_key}" => {
        is_regional = (
          tun.psk_secret_location != null ||
          can(regex(local._regional_secret_re, tun.psk_secret_id))
        )
        psk_secret_id         = tun.psk_secret_id
        psk_secret_location   = tun.psk_secret_location
        psk_secret_project_id = tun.psk_secret_project_id
        psk_secret_version    = tun.psk_secret_version
      }
    }
  ]...)
  global_tunnel_secrets = {
    for k, v in local._tunnel_secrets : k => v if !v.is_regional
  }
  regional_tunnel_secrets = {
    for k, v in local._tunnel_secrets : k => v if v.is_regional
  }
}

data "google_secret_manager_secret_version" "tunnel_psk" {
  for_each = local.global_tunnel_secrets
  project = (
    startswith(each.value.psk_secret_id, "projects/")
    ? split("/", each.value.psk_secret_id)[1]
    : coalesce(each.value.psk_secret_project_id, var.project_id)
  )
  secret = (
    startswith(each.value.psk_secret_id, "projects/")
    ? split("/", each.value.psk_secret_id)[3]
    : each.value.psk_secret_id
  )
  version = each.value.psk_secret_version

  lifecycle {
    # Fail closed if a Secret Manager version payload is empty so
    # modules/net-vpn-ha cannot fall back to a random generated PSK.
    postcondition {
      condition     = length(trimspace(self.secret_data)) > 0
      error_message = "Secret Manager PSK payload must be non-empty."
    }
  }
}

data "google_secret_manager_regional_secret_version" "tunnel_psk" {
  for_each = local.regional_tunnel_secrets
  location = (
    startswith(each.value.psk_secret_id, "projects/")
    ? split("/", each.value.psk_secret_id)[3]
    : each.value.psk_secret_location
  )
  project = (
    startswith(each.value.psk_secret_id, "projects/")
    ? split("/", each.value.psk_secret_id)[1]
    : coalesce(each.value.psk_secret_project_id, var.project_id)
  )
  secret = (
    startswith(each.value.psk_secret_id, "projects/")
    ? split("/", each.value.psk_secret_id)[5]
    : each.value.psk_secret_id
  )
  version = each.value.psk_secret_version

  lifecycle {
    # Fail closed if a regional Secret Manager payload is empty so
    # modules/net-vpn-ha cannot fall back to a random generated PSK.
    postcondition {
      condition     = length(trimspace(self.secret_data)) > 0
      error_message = "Regional Secret Manager PSK payload must be non-empty."
    }
  }
}

module "vpn-ha" {
  source     = "../../../modules/net-vpn-ha"
  for_each   = var.peers
  project_id = var.project_id
  region     = var.region
  network    = var.network
  name       = "${var.name_prefix}-${each.key}"
  peer_gateways = {
    default = {
      external = {
        description = coalesce(
          each.value.description,
          "External VPN gateway for ${each.key}"
        )
        interfaces      = each.value.external_interfaces
        redundancy_type = each.value.redundancy_type
      }
    }
  }
  router_config = {
    asn              = coalesce(each.value.router_asn, var.router_asn)
    create           = true
    custom_advertise = local.custom_advertise
    keepalive        = each.value.router_keepalive
  }
  tunnels = {
    for tun_key, tun in each.value.tunnels : tun_key => {
      bgp_peer = {
        address        = tun.bgp_peer_address
        asn            = tun.bgp_peer_asn
        route_priority = tun.bgp_route_priority
      }
      bgp_session_range = tun.bgp_session_range
      cipher_suite = (
        local.normalized_cipher_suites[each.key]
      )
      ike_version                     = 2
      peer_external_gateway_interface = tun.peer_external_gateway_interface
      peer_gateway                    = "default"
      shared_secret = (
        local._tunnel_secrets["${each.key}/${tun_key}"].is_regional
        ? data.google_secret_manager_regional_secret_version.tunnel_psk[
          "${each.key}/${tun_key}"
        ].secret_data
        : data.google_secret_manager_secret_version.tunnel_psk[
          "${each.key}/${tun_key}"
        ].secret_data
      )
      vpn_gateway_interface = tun.vpn_gateway_interface
    }
  }
  vpn_gateway_create = {
    description = coalesce(
      each.value.description,
      "HA VPN gateway for ${each.key}"
    )
    ipv6 = var.stack_type == "IPV4_IPV6"
  }
}
