# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

output "gke_cluster" {
  description = "Deployed GKE cluster."
  value       = module.cluster
  sensitive   = true
}

output "lb" {
  description = "Application Load Balancer."
  value       = module.application-lb
  sensitive   = true
}

output "tls_private_key_secret_id" {
  description = "Secret Manager ID storing the generated self-signed TLS private key, or null when using a custom certificate."
  value = (
    local.use_self_signed_cert
    ? nonsensitive(module.tls-private-key-secret[0].ids["${var.lb_name}-tls-key"])
    : null
  )
}

output "umig" {
  description = "Unmanaged instance group."
  value       = google_compute_instance_group.umig
  sensitive   = true
}

output "vm" {
  description = "Deployed VM."
  value       = module.compute-vm
  sensitive   = true
}