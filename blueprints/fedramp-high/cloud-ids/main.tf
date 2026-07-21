resource "google_project_service" "net-host-services" {
  project = var.network_project_id
  for_each = toset([
    "accesscontextmanager.googleapis.com",
    "beyondcorp.googleapis.com",
    "binaryauthorization.googleapis.com",
    "compute.googleapis.com",
    "ids.googleapis.com",
    "iam.googleapis.com",
    "iap.googleapis.com",
    "orgpolicy.googleapis.com",
    "run.googleapis.com",
    "serviceusage.googleapis.com"
  ])
  service = each.value
  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_on_destroy = false

}

data "google_project" "project" {
}

data "google_compute_zones" "available" {
  region  = var.region
  project = data.google_project.project.project_id
  status  = "UP"
}

module "cloud_ids" {
  source                       = "../../../modules/intrusion-detection-system"
  project                      = var.network_project_id
  landing_vpc_network          = var.network_name
  network_region               = var.region
  network_zone                 = data.google_compute_zones.available.names[0]
  landing_network              = var.network_name
  subnet                       = var.subnetwork_name
  subnet_list                  = var.subnetwork_list
  ids_private_ip_range_name    = "${var.prefix}-ids-private-address"
  ids_private_ip_prefix_length = var.ids_private_ip_prefix_length
  ids_name                     = "${var.prefix}-${var.ids_name}"
  severity                     = var.severity
  packet_mirroring_policy_name = "${var.prefix}-${var.packet_mirroring_policy_name}"

  depends_on = [google_project_service.net-host-services]
}