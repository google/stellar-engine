provider "google" {
  alias   = "host_network"
  project = var.net_project
}

resource "google_compute_firewall" "gitlab_health_checks" {
  provider = google.host_network

  name    = "allow-gitlab-health-checks"
  network = var.network
  project = var.net_project

  priority  = 1000
  direction = "INGRESS"

  source_ranges = [
    "35.191.0.0/16",   # Google LB Health Checks (Global)
    "130.211.0.0/22",  # Google LB Health Checks (Regional)
    "209.85.152.0/22", # Google Cloud Uptime Checks (Monitoring)
    "209.85.204.0/22"  # Google Cloud Uptime Checks (Monitoring)
  ]

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8443", "10256"]
  }

  target_service_accounts = [google_service_account.gitlab-sa.email]
}

resource "google_compute_firewall" "allow_gitlab_external_access" {
  provider = google.host_network

  name    = "allow-gitlab-external-access"
  network = var.network
  project = var.net_project

  priority  = 1000
  direction = "INGRESS"

  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  target_service_accounts = [google_service_account.gitlab-sa.email]
}
