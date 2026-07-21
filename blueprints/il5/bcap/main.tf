locals {
  router_configs = var.router_configs

  router_names = {
    router1 = google_compute_router.routers["router1"].name
    router2 = google_compute_router.routers["router2"].name
  }

  router_regions = {
    router1 = var.region1
    router2 = var.region2
  }

  subnet_regions = {
    subnet1 = var.region1
    subnet2 = var.region2
  }

  dod_split_cidr_blocks = {
    subnet1 = cidrsubnet(var.dod_base_cidr_block, 1, 0)
    subnet2 = cidrsubnet(var.dod_base_cidr_block, 1, 1)
  }

  dod_advertised_ip_ranges = {
    for k_subnet_key, v_subnet_config in var.subnet_configs :
    local.dod_split_cidr_blocks[k_subnet_key] => "DoD-Assigned-Subnet-${v_subnet_config.name}"
  }
}

# VPC Network (x1)
resource "google_compute_network" "vpc_network" {
  project                 = var.hub_project_id
  name                    = var.network_name
  auto_create_subnetworks = false
  mtu                     = 1460
  description             = "VPC Network for BCAP deployment"
}

# GCP_18 Fix
# BCAP connectivity: allows inbound ICMP for path discovery and TCP 80/443 for web traffic.

# NOTE: Logging is disabled by default in this blueprint for cost-efficiency during development. 
# For any production implementation, logging must be enabled to comply with FedRAMP High auditing 
# and continuous monitoring requirements.
resource "google_compute_firewall" "bcap_allow_rules" {
  project       = var.hub_project_id
  name          = "${var.network_name}-bcap-allow"
  network       = google_compute_network.vpc_network.self_link
  source_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "icmp"
  }
  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
  priority = 500
}

# VPC Subnets (x2)
resource "google_compute_subnetwork" "bcap_subnets" {
  for_each = var.subnet_configs

  project                  = var.hub_project_id
  name                     = each.value.name
  ip_cidr_range            = local.dod_split_cidr_blocks[each.key]
  network                  = google_compute_network.vpc_network.self_link
  region                   = local.subnet_regions[each.key]
  private_ip_google_access = var.subnet_private_ip_google_access
  description              = each.value.description

  dynamic "log_config" {
    for_each = var.subnet_enable_flow_logs ? [1] : []
    content {
      aggregation_interval = "INTERVAL_5_SEC"
      flow_sampling        = 0.5
      metadata             = "INCLUDE_ALL_METADATA"
      filter_expr          = "true"
    }
  }

  depends_on = [google_compute_network.vpc_network]
}

# Cloud Routers (x2)
resource "google_compute_router" "routers" {
  for_each = local.router_configs

  project = var.hub_project_id
  name    = each.value.name
  network = google_compute_network.vpc_network.self_link
  region  = local.router_regions[each.key]
  bgp {
    asn            = var.router_google_asn
    advertise_mode = "CUSTOM"

    dynamic "advertised_ip_ranges" {
      for_each = local.dod_advertised_ip_ranges
      content {
        range       = advertised_ip_ranges.key
        description = advertised_ip_ranges.value
      }
    }
  }

  description = each.value.description

  depends_on = [google_compute_subnetwork.bcap_subnets]
}

# VLAN Attachments (x4)
resource "google_compute_interconnect_attachment" "attachments" {
  for_each = var.attachment_configs

  project     = var.hub_project_id
  name        = each.value.name
  description = each.value.description
  region      = local.router_regions[each.value.router_key]
  router      = local.router_names[each.value.router_key]

  type                     = "PARTNER"
  edge_availability_domain = each.value.edge_availability_domain
  mtu                      = each.value.mtu
  vlan_tag8021q            = each.value.vlan_id

  admin_enabled = true

  depends_on = [
    google_compute_router.routers
  ]
}
