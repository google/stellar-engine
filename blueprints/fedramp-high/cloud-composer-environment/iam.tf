resource "google_project_iam_member" "composer_worker" {
  project = var.main_project_id
  role    = "roles/composer.worker"
  member  = google_service_account.composer.member
}

resource "google_project_iam_member" "composer_service_agent" {
  project = var.main_project_id
  role    = var.service_agent_version
  member  = google_project_service_identity.composer_agent.member
}

resource "google_project_iam_member" "composer_network_user" {
  project = var.network_project_id
  role    = "roles/compute.networkUser"
  member  = google_project_service_identity.composer_agent.member
}

resource "google_project_iam_member" "composer_vpc_agent" {
  project = var.network_project_id
  role    = "roles/composer.sharedVpcAgent"
  member  = google_project_service_identity.composer_agent.member
}