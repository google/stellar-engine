resource "google_compute_global_address" "flash_ip" {
  project = var.main_project_id
  name    = "flash-app-ip"
}

resource "google_certificate_manager_dns_authorization" "flash-dns-auth" {
  project = var.main_project_id
  name    = "flash-dns-auth"
  domain  = var.domain
}
resource "google_certificate_manager_certificate" "flash-cert" {
  project = var.main_project_id
  name    = "flash-cert"
  scope   = "DEFAULT"
  managed {
    domains            = [var.domain]
    dns_authorizations = [google_certificate_manager_dns_authorization.flash-dns-auth.id]
  }
  depends_on = [google_certificate_manager_dns_authorization.flash-dns-auth]
}

resource "google_certificate_manager_certificate_map" "flash-map" {
  project = var.main_project_id
  name    = "flash-cert-map"
}

resource "google_certificate_manager_certificate_map_entry" "flash-entry" {
  project      = var.main_project_id
  name         = "flash-entry"
  map          = google_certificate_manager_certificate_map.flash-map.name
  hostname     = var.domain
  certificates = [google_certificate_manager_certificate.flash-cert.id]
}
