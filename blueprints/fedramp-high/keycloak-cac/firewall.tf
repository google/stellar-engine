provider "google" {
  alias   = "host_network"
  project = var.network_project_id
}

resource "google_compute_firewall" "keycloak_health_checks" {
  provider = google.host_network

  name    = "allow-keycloak-health-checks"
  network = var.network
  project = var.network_project_id

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

  target_service_accounts = [google_service_account.keycloak-service-account.email]
}

resource "google_compute_firewall" "allow_keycloak_external_access" {
  provider = google.host_network

  name    = "allow-keycloak-external-access"
  network = var.network
  project = var.network_project_id

  priority  = 1000
  direction = "INGRESS"

  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  target_service_accounts = [google_service_account.keycloak-service-account.email]
}