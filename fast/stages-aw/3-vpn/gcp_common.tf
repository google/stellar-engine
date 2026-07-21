data "google_compute_network" "existing" {
  name    = var.gcp_network_name
  project = var.project_id
}

resource "google_compute_router" "gcp_router" {
  project = var.project_id
  region  = var.region
  name    = coalesce(var.gcp_router_name, "${var.name_prefix}-router")
  network = data.google_compute_network.existing.self_link
  bgp {
    asn               = var.gcp_bgp_asn
    identifier_range  = var.gcp_bgp_identifier_range
    advertise_mode    = "CUSTOM"
    advertised_groups = ["ALL_SUBNETS"]
    # 35.199.192.0/19 is the source IP range Cloud DNS uses for forwarding
    # queries. Without this advertisement, DNS responses from Azure cannot
    # route back through the VPN tunnel, causing silent SERVFAIL.
    # https://cloud.google.com/dns/docs/zones/forwarding-zones
    advertised_ip_ranges {
      range       = "35.199.192.0/19"
      description = "Cloud DNS forwarding range"
    }
  }
}
