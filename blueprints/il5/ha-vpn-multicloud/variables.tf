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

variable "advertise_dns_forwarding_range" {
  description = "Advertise 35.199.192.0/19 on routers for Cloud DNS return traffic."
  type        = bool
  default     = true
  nullable    = false
}

variable "cipher_suite" {
  description = "Default IKEv2 Phase 1 and Phase 2 cipher suite for VPN tunnels."
  type = object({
    phase1 = optional(object({
      dh         = optional(list(string))
      encryption = optional(list(string))
      integrity  = optional(list(string))
      prf        = optional(list(string))
    }))
    phase2 = optional(object({
      encryption = optional(list(string))
      integrity  = optional(list(string))
      pfs        = optional(list(string))
    }))
  })
  default = {
    phase1 = {
      dh         = ["Group-20"]
      encryption = ["AES-GCM-16-256"]
      integrity  = null
      prf        = ["PRF-HMAC-SHA2-384"]
    }
    phase2 = {
      encryption = ["AES-GCM-16-256"]
      integrity  = null
      pfs        = ["Group-20"]
    }
  }

  validation {
    condition = (
      var.cipher_suite == null
      ? true
      : (
        var.cipher_suite.phase1 != null &&
        var.cipher_suite.phase2 != null
      )
    )
    error_message = "Non-null cipher_suite must define both phase1 and phase2."
  }
}

variable "custom_advertised_ip_ranges" {
  description = "Extra CIDR ranges and descriptions advertised on Cloud Routers."
  type        = map(string)
  default     = {}
  nullable    = false

  validation {
    condition = alltrue([
      for cidr in keys(var.custom_advertised_ip_ranges) :
      can(cidrhost(cidr, 0))
    ])
    error_message = "Every custom_advertised_ip_ranges key must be a valid CIDR."
  }
}

variable "name_prefix" {
  description = "Prefix for HA VPN gateway, router, and tunnel resource names."
  type        = string
  default     = "ha-vpn"
  nullable    = false

  validation {
    condition = can(regex(
      "^[a-z]([a-z0-9-]{0,29}[a-z0-9])?$",
      var.name_prefix
    ))
    error_message = "name_prefix must be 1 to 31 RFC1035 lowercase label characters."
  }
}

variable "network" {
  description = "Self-link or name of the VPC network hosting the VPN gateways."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.network)) > 0
    error_message = "network must be a non-empty VPC name or self-link."
  }
}

variable "peers" {
  description = "External multi-cloud or on-premises VPN peers keyed by peer ID."
  type = map(object({
    cipher_suite = optional(object({
      phase1 = optional(object({
        dh         = optional(list(string))
        encryption = optional(list(string))
        integrity  = optional(list(string))
        prf        = optional(list(string))
      }))
      phase2 = optional(object({
        encryption = optional(list(string))
        integrity  = optional(list(string))
        pfs        = optional(list(string))
      }))
    }))
    description         = optional(string)
    external_interfaces = list(string)
    redundancy_type     = string
    router_asn          = optional(number)
    router_keepalive    = optional(number)
    tunnels = map(object({
      bgp_peer_address                = string
      bgp_peer_asn                    = number
      bgp_route_priority              = optional(number, 1000)
      bgp_session_range               = string
      peer_external_gateway_interface = number
      psk_secret_id                   = string
      psk_secret_location             = optional(string)
      psk_secret_project_id           = optional(string)
      psk_secret_version              = optional(string, "latest")
      vpn_gateway_interface           = number
    }))
  }))
  default  = {}
  nullable = false

  validation {
    condition = alltrue([
      for k in keys(var.peers) :
      can(regex("^[a-z]([a-z0-9-]{0,19}[a-z0-9])?$", k))
    ])
    error_message = "Peer keys must be 1 to 21 RFC1035 lowercase label characters."
  }

  validation {
    condition = alltrue(flatten([
      for peer_key, peer in var.peers : [
        for tun_key in keys(peer.tunnels) : (
          can(regex("^[a-z]([a-z0-9-]*[a-z0-9])?$", tun_key)) &&
          length("${var.name_prefix}-${peer_key}-${tun_key}") <= 63
        )
      ]
    ]))
    error_message = "Tunnel keys must be RFC1035 lowercase labels with full names <= 63 chars."
  }

  validation {
    condition = alltrue([
      for _, peer in var.peers : contains([
        "FOUR_IPS_REDUNDANCY",
        "TWO_IPS_REDUNDANCY",
        "SINGLE_IP_INTERNALLY_REDUNDANT",
      ], peer.redundancy_type)
    ])
    error_message = "redundancy_type must be FOUR_IPS_REDUNDANCY, TWO_IPS_REDUNDANCY, or SINGLE_IP_INTERNALLY_REDUNDANT."
  }

  validation {
    condition = alltrue([
      for _, peer in var.peers : (
        (
          peer.redundancy_type == "FOUR_IPS_REDUNDANCY" &&
          length(peer.external_interfaces) == 4
        ) ||
        (
          peer.redundancy_type == "TWO_IPS_REDUNDANCY" &&
          length(peer.external_interfaces) == 2
        ) ||
        (
          peer.redundancy_type == "SINGLE_IP_INTERNALLY_REDUNDANT" &&
          length(peer.external_interfaces) == 1
        )
      )
    ])
    error_message = "external_interfaces count must match redundancy_type (4, 2, or 1)."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for ip in peer.external_interfaces :
        can(cidrhost("${ip}/32", 0)) || can(cidrhost("${ip}/128", 0))
      ]
    ]))
    error_message = "Every external_interfaces entry must be a valid IPv4 or IPv6 IP."
  }

  validation {
    condition = alltrue([
      for _, peer in var.peers : (
        peer.cipher_suite == null ? true : (
          (
            peer.cipher_suite.phase1 != null ||
            try(var.cipher_suite.phase1, null) != null
          ) &&
          (
            peer.cipher_suite.phase2 != null ||
            try(var.cipher_suite.phase2, null) != null
          )
        )
      )
    ])
    error_message = "Effective peer cipher_suite must resolve non-null phase1 and phase2."
  }

  validation {
    condition = alltrue([
      for _, peer in var.peers : (
        peer.router_asn == null ? true : (
          (peer.router_asn >= 64512 && peer.router_asn <= 65534) ||
          (peer.router_asn >= 4200000000 && peer.router_asn <= 4294967294)
        )
      )
    ])
    error_message = "Per-peer router_asn must be in 64512-65534 or 4200000000-4294967294."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : contains([0, 1], t.vpn_gateway_interface)
      ]
    ]))
    error_message = "Each tunnel vpn_gateway_interface must be 0 or 1."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : (
          t.peer_external_gateway_interface >= 0 &&
          t.peer_external_gateway_interface < length(peer.external_interfaces)
        )
      ]
    ]))
    error_message = "peer_external_gateway_interface must index into external_interfaces."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : (
          can(cidrnetmask(t.bgp_session_range)) ? (
            split("/", t.bgp_session_range)[1] == "30" &&
            startswith(t.bgp_session_range, "169.254.") &&
            contains([
              cidrhost(t.bgp_session_range, 1),
              cidrhost(t.bgp_session_range, 2),
            ], split("/", t.bgp_session_range)[0])
          ) : false
        )
      ]
    ]))
    error_message = "bgp_session_range must be a host /30 CIDR in 169.254.0.0/16."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : (
          can(cidrhost(t.bgp_session_range, 0))
          ? cidrhost(t.bgp_session_range, 0) != "169.254.169.252"
          : true
        )
      ]
    ]))
    error_message = "bgp_session_range cannot use metadata range 169.254.169.252/30."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : (
          can(cidrnetmask(t.bgp_session_range)) ? (
            contains([
              cidrhost(t.bgp_session_range, 1),
              cidrhost(t.bgp_session_range, 2),
            ], t.bgp_peer_address) &&
            t.bgp_peer_address != split("/", t.bgp_session_range)[0]
          ) : false
        )
      ]
    ]))
    error_message = "bgp_peer_address must be the peer host IP in bgp_session_range."
  }

  validation {
    condition = length(distinct(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : (
          can(cidrhost(t.bgp_session_range, 0))
          ? cidrhost(t.bgp_session_range, 0)
          : t.bgp_session_range
        )
      ]
      ]))) == length(flatten([
      for _, peer in var.peers : keys(peer.tunnels)
    ]))
    error_message = "Every tunnel bgp_session_range /30 must be unique across all peers."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels :
        t.bgp_peer_asn >= 1 && t.bgp_peer_asn <= 4294967294
      ]
    ]))
    error_message = "Each tunnel bgp_peer_asn must be between 1 and 4294967294."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : (
          t.psk_secret_location == null
          ? true
          : can(regex("^[a-z]+-[a-z]+[0-9]+$", t.psk_secret_location))
        )
      ]
    ]))
    error_message = "psk_secret_location must be a valid GCP region such as us-east4."
  }

  validation {
    condition = alltrue(flatten([
      for _, peer in var.peers : [
        for _, t in peer.tunnels : (
          can(regex("^(latest|[1-9][0-9]*)$", t.psk_secret_version)) &&
          (
            t.psk_secret_location == null
            ? (
              can(regex("^[a-zA-Z0-9_-]{1,255}$", t.psk_secret_id)) ||
              can(regex(
                "^projects/[a-zA-Z0-9-]+/secrets/[a-zA-Z0-9_-]{1,255}$",
                t.psk_secret_id
              )) ||
              can(regex(
                "^projects/[a-zA-Z0-9-]+/locations/[a-z]+-[a-z]+[0-9]+/secrets/[a-zA-Z0-9_-]{1,255}$",
                t.psk_secret_id
              ))
            )
            : (
              can(regex("^[a-zA-Z0-9_-]{1,255}$", t.psk_secret_id)) ||
              (
                can(regex(
                  "^projects/[a-zA-Z0-9-]+/locations/[a-z]+-[a-z]+[0-9]+/secrets/[a-zA-Z0-9_-]{1,255}$",
                  t.psk_secret_id
                )) &&
                split("/", t.psk_secret_id)[3] == t.psk_secret_location
              )
            )
          )
        )
      ]
    ]))
    error_message = "Each tunnel requires valid Secret Manager psk_secret_id and version."
  }
}

variable "project_id" {
  description = "GCP project ID hosting HA VPN gateways, external gateways, and routers."
  type        = string
  nullable    = false

  validation {
    condition = can(regex(
      "^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
      var.project_id
    ))
    error_message = "project_id must be a valid 6 to 30 character GCP project ID."
  }
}

variable "region" {
  description = "GCP region where HA VPN gateways, tunnels, and routers are created."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.region)) > 0
    error_message = "region must be non-empty."
  }
}

variable "router_asn" {
  description = "Default private BGP ASN for Cloud Routers created by this blueprint."
  type        = number
  default     = 64514
  nullable    = false

  validation {
    condition = (
      (var.router_asn >= 64512 && var.router_asn <= 65534) ||
      (var.router_asn >= 4200000000 && var.router_asn <= 4294967294)
    )
    error_message = "router_asn must be in 64512-65534 or 4200000000-4294967294."
  }
}

variable "stack_type" {
  description = "Gateway IP stack type (IPV4_ONLY or IPV4_IPV6). IPV4_IPV6 uses IPv4 BGP sessions carrying IPv6 routes, not IPv6-only BGP over 2600:2d00:0:2::/63."
  type        = string
  default     = "IPV4_ONLY"
  nullable    = false

  validation {
    condition     = contains(["IPV4_ONLY", "IPV4_IPV6"], var.stack_type)
    error_message = "stack_type must be IPV4_ONLY or IPV4_IPV6."
  }
}
