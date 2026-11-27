/**
 * Copyright 2022 Google LLC
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

output "dns_zone_gcr_name" {
  description = "Name for Managed DNS zone for GCR."
  value       = module.gcr.name
}

output "dns_zone_googleapis_name" {
  description = "Name for Managed DNS zone for GoogleAPIs."
  value       = module.googleapis.name
}

output "dns_zone_pkg_dev_name" {
  description = "Name for Managed DNS zone for PKG_DEV."
  value       = module.pkg-dev.name
}

output "forwarding_rule_name" {
  description = "Forwarding rule resource name."
  value       = google_compute_global_forwarding_rule.forwarding_rule_private_service_connect.name
}

output "forwarding_rule_target" {
  description = "Target resource to receive the matched traffic. Only `all-apis` and `vpc-sc` are valid."
  value       = google_compute_global_forwarding_rule.forwarding_rule_private_service_connect.target
}

output "global_address_id" {
  description = "An identifier for the global address created for the private service connect with format `projects/{{project}}/global/addresses/{{name}}`."
  value       = google_compute_global_address.private_service_connect.id
}

output "private_service_connect_ip" {
  description = "Private service connect IP."
  value       = google_compute_global_address.private_service_connect.address

  depends_on = [
    google_compute_global_forwarding_rule.forwarding_rule_private_service_connect
  ]
}

output "private_service_connect_name" {
  description = "Private service connect name."
  value       = google_compute_global_address.private_service_connect.name

  depends_on = [
    google_compute_global_forwarding_rule.forwarding_rule_private_service_connect
  ]
}