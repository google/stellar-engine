/**
 * Copyright 2024 Google LLC
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

# Forwarding zones — authorized for CSP Landing VPC (direct VPN connectivity).
# Cloud DNS forwarding cannot use NCC transitive routing, so the forwarding
# zone must be in the VPC where VPN tunnels terminate.
module "dns-forwarding-zones" {
  source     = "../../../../modules/dns"
  for_each   = var.forwarding_zones
  project_id = var.host_project_id
  name       = "${var.prefix}-fwd-${each.key}"
  zone_config = {
    domain = each.value.domain
    forwarding = {
      forwarders      = each.value.forwarders
      client_networks = [var.vpc_self_links.csp_landing]
    }
  }
}

# DNS peering: Landing VPC → CSP Landing VPC (1st hop).
# Allows the hub VPC to resolve forwarded domains through the CSP
# Landing VPC where the forwarding zone is authoritative.
module "dns-peering-landing" {
  source     = "../../../../modules/dns"
  for_each   = var.forwarding_zones
  project_id = var.host_project_id
  name       = "${var.prefix}-peer-landing-${each.key}"
  zone_config = {
    domain = each.value.domain
    peering = {
      client_networks = [var.vpc_self_links.landing]
      peer_network    = var.vpc_self_links.csp_landing
    }
  }
}

# DNS peering: spoke VPCs → Landing VPC (transitive hop).
# Shared-services and tenant-transit VPCs peer through Landing to reach
# the CSP Landing forwarding zone. This is within the 3-VPC / 1-transitive-hop
# limit for Cloud DNS peering.
module "dns-peering-spokes" {
  source     = "../../../../modules/dns"
  for_each   = var.forwarding_zones
  project_id = var.host_project_id
  name       = "${var.prefix}-peer-spokes-${each.key}"
  zone_config = {
    domain = each.value.domain
    peering = {
      client_networks = [
        var.vpc_self_links.shared_services,
        var.vpc_self_links.tenant_transit,
      ]
      peer_network = var.vpc_self_links.landing
    }
  }
}

# DNS peering: spoke VPCs → Landing VPC for the org private zone.
# The private zone is defined in stage 3-networking and authorized for the
# landing VPC only. This peering zone lets shared-services and tenant-transit
# VPCs resolve records in it without modifying stage 3.
module "dns-peering-private-zone" {
  source     = "../../../../modules/dns"
  count      = var.private_zone_domain != null ? 1 : 0
  project_id = var.host_project_id
  name       = "${var.prefix}-peer-spokes-private"
  zone_config = {
    domain = var.private_zone_domain
    peering = {
      client_networks = [
        var.vpc_self_links.shared_services,
        var.vpc_self_links.tenant_transit,
      ]
      peer_network = var.vpc_self_links.landing
    }
  }
}

# DNS response policy for Private Google Access on the shared-services VPC.
# Redirects googleapis.com, gcr.io, etc. to the PSC endpoint so traffic
# stays on the Google network. Mirrors the policy in stage 3-networking
# which covers only the landing VPC.
module "dns-policy-googleapis" {
  source     = "../../../../modules/dns-response-policy"
  count      = var.dns_policy_rules_file != null ? 1 : 0
  project_id = var.host_project_id
  name       = "googleapis-shared-services"
  factories_config = {
    rules = var.dns_policy_rules_file
  }
  networks = {
    shared-services = var.vpc_self_links.shared_services
  }
}

resource "google_storage_bucket_object" "tfvars" {
  bucket = var.automation.outputs_bucket
  name   = "tfvars/shared-services-dns.auto.tfvars.json"
  content = jsonencode({
    dns_forwarding_zones = {
      for k, v in module.dns-forwarding-zones : k => {
        name   = v.name
        domain = v.domain
      }
    }
  })
}
