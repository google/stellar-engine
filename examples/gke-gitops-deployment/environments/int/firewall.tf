
resource "google_compute_firewall" "allow_lb_health_check" {
  name        = "allow-lb-health-check"
  project     = var.main_project_id
  network     = module.gke-deployment.vpc-network.self_link
  target_tags = ["[GKENODE POOL TAG]"]
  direction   = "INGRESS"

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = [
    "130.211.0.0/22",
    "35.191.0.0/16",
  ]
}