data "google_compute_network" "network" {
  name    = var.network_name
  project = var.network_project_id
}

data "google_compute_subnetwork" "subnetwork" {
  name    = var.subnetwork_name
  region  = var.region
  project = var.network_project_id
}

resource "google_project_service" "cloud_composer_api" {
  project            = var.main_project_id
  service            = "composer.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service_identity" "composer_agent" {
  provider = google-beta
  project  = var.main_project_id
  service  = "composer.googleapis.com"

  depends_on = [
    google_project_service.cloud_composer_api
  ]
}

resource "google_service_account" "composer" {
  project      = var.main_project_id
  account_id   = var.sa_account_id
  display_name = var.sa_display_name
}

resource "google_composer_environment" "main" {
  provider = google-beta

  project = var.main_project_id
  name    = var.composer_env_name
  region  = var.region

  config {
    enable_private_environment = true
    software_config {
      image_version = var.composer_version
    }

    node_config {
      network         = data.google_compute_network.network.self_link
      subnetwork      = data.google_compute_subnetwork.subnetwork.self_link
      service_account = google_service_account.composer.name
    }
  }

  depends_on = [
    google_project_service.cloud_composer_api,
    google_project_iam_member.composer_worker,
    google_project_iam_member.composer_service_agent,
    google_project_iam_member.composer_network_user,
    google_project_iam_member.composer_vpc_agent
  ]
}