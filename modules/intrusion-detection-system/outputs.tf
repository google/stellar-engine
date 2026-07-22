#/**
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



output "ids_endpoint_severity" {
  description = "IDS Endpoint severity"
  value       = google_cloud_ids_endpoint.ids_endpoint.severity
}

output "ids_name" {
  value = var.ids_name
}

output "ids_private_ip_range_name" {
  value = var.ids_private_ip_range_name
}

output "packet_mirroring_policy_name" {
  value = var.packet_mirroring_policy_name
}