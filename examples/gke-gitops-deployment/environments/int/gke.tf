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

module "gke-deployment" {
  source                              = "../../../../blueprints/il5/gke-hardened"
  gatekeeper_sa                       = var.gatekeeper_sa
  gke_cluster_enable_private_endpoint = var.gke_cluster_enable_private_endpoint
  gke_cluster_master_global_access    = var.gke_cluster_master_global_access
  gke_cluster_name                    = var.gke_cluster_name
  gke_initial_node_per_zone           = var.gke_initial_node_per_zone
  gke_nodepool_name                   = var.gke_nodepool_name
  gke_vpc_master_ipv4_cidr_block      = var.gke_vpc_master_ipv4_cidr_block

  kms_keyring_name = var.kms_keyring_name
  kms_key_names    = var.kms_key_names

  local_admin_external_ip = var.local_admin_external_ip

  main_project_id                    = var.main_project_id
  master_authorized_ranges_ip_ranges = var.master_authorized_ranges_ip_ranges

  nat_gateway_name    = var.nat_gateway_name
  nat_router_name     = var.nat_router_name
  network_name        = var.network_name
  node_config_tags    = var.node_config_tags
  node_disk_size_gb   = var.node_disk_size_gb
  nodepool_node_count = var.nodepool_node_count

  policy_controller_exemptable_namespaces = var.policy_controller_exemptable_namespaces

  region                   = var.region
  remove_default_node_pool = var.remove_default_node_pool

  source_branch = var.source_branch
  source_dir    = var.source_dir
  source_repo   = var.source_repo

  subnetwork_name                          = var.subnetwork_name
  subnetwork_ip_cidr_range_1               = var.subnetwork_ip_cidr_range_1
  subnetwork_secondary_ip_range_pods_1     = var.subnetwork_secondary_ip_range_pods_1
  subnetwork_secondary_ip_range_services_1 = var.subnetwork_secondary_ip_range_services_1

}

resource "google_project_iam_member" "gke-sa-artifactregistry" {
  project = var.main_project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${module.gke-deployment.gke_cluster_sa.email}"
}
