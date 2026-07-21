locals {

  cloud_runs_raw = yamldecode(templatefile("./data/cloudrun.yaml", {
    DOMAIN       = var.domain,
    ACCESSPOLICY = var.access_policy_number
  }))
  cloud_runs = local.cloud_runs_raw != null ? local.cloud_runs_raw : {}
  vms_raw = yamldecode(templatefile("./data/compute-engine.yaml", {
    DOMAIN       = var.domain,
    ACCESSPOLICY = var.access_policy_number
  }))
  vms  = local.vms_raw != null ? local.vms_raw : {}
  apps = merge(local.cloud_runs, local.vms)
}

data "google_project" "project" {
  project_id = var.main_project_id
}

data "google_project" "landing_project" {
  project_id = var.main_project_id
}

resource "google_project_service" "services" {
  project = var.main_project_id
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
    "servicenetworking.googleapis.com",
    "serviceusage.googleapis.com"
  ])
  service = each.value
  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_on_destroy = false

}