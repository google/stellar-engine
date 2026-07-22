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
output "gke_cluster_endpoint" {
  description = "The endpoint of the GKE cluster."
  value       = module.cluster.endpoint
}

output "gke_cluster_name" {
  description = "The name of the GKE cluster."
  value       = module.cluster.name
}

output "cluster_master_version" {
  description = "The master version of the GKE cluster."
  value       = module.cluster.master_version
}

output "nodepool_name" {
  description = "The name of the additional GKE nodepool."
  value       = module.cluster_nodepool.name
}

output "nodepool_id" {
  description = "The fully qualified ID of the additional GKE nodepool."
  value       = module.cluster_nodepool.id
}

output "nodepool_service_account_email" {
  description = "The service account email used by the additional GKE nodepool."
  value       = module.cluster_nodepool.service_account_email
}

output "gke_cluster_sa_email" {
  description = "The email address of the custom service account created for the GKE cluster."
  value       = google_service_account.gke_cluster_sa.email
}

# --- Outputs for Consumed Existing Infrastructure ---
output "consumed_kms_key_id" {
  description = "The ID of the existing KMS CryptoKey used by the GKE cluster for boot disk encryption."
  value       = data.google_kms_crypto_key.existing_kms_key.id
}

output "consumed_network_self_link" {
  description = "The self-link of the existing VPC network used by the GKE cluster."
  value       = data.google_compute_network.existing_network.self_link
}

output "consumed_subnetwork_self_link" {
  description = "The self-link of the existing subnetwork used by the GKE cluster."
  value       = data.google_compute_subnetwork.existing_subnetwork.self_link
}

# --- Bastion VM Outputs ---
output "bastion_vm_name" {
  description = "The name of the created bastion Compute Engine VM."
  value       = var.bastion_vm_name
}

output "bastion_vm_public_ip" {
  description = "The public IP address of the bastion Compute Engine VM (if ephemeral public IP is enabled)."
  value       = try(module.bastion_vm.network_interfaces[0].access_config[0].nat_ip, null)
}
