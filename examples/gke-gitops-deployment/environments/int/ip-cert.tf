/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
