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

output "external_gateway_ids" {
  description = "External VPN gateway resource IDs keyed by peer identifier."
  value = {
    for k, m in module.vpn-ha :
    k => try(m.external_gateway["default"].id, null)
  }
}

output "router_names" {
  description = "Cloud Router names keyed by peer identifier."
  value = {
    for k, m in module.vpn-ha : k => m.router_name
  }
}

output "tunnel_names" {
  description = "VPN tunnel names keyed by peer identifier and tunnel key."
  value = {
    for k, m in module.vpn-ha : k => m.tunnel_names
  }
}

output "tunnel_self_links" {
  description = "VPN tunnel self-links keyed by peer and tunnel key."
  value = {
    for k, m in module.vpn-ha : k => m.tunnel_self_links
  }
}

output "vpn_gateway_ids" {
  description = "HA VPN gateway resource IDs keyed by peer identifier."
  value = {
    for k, m in module.vpn-ha : k => m.id
  }
}

output "vpn_gateway_interfaces" {
  description = "HA VPN gateway interface IP configs keyed by peer."
  value = {
    for k, m in module.vpn-ha : k => try(m.gateway.vpn_interfaces, [])
  }
}

output "vpn_gateway_self_links" {
  description = "HA VPN gateway self-links keyed by peer identifier."
  value = {
    for k, m in module.vpn-ha : k => m.self_link
  }
}
