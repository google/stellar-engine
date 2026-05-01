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

output "admin_group" {
  value       = var.admin_group
  description = "The principal for the Gemini Enterprise administrators group."
}

output "user_groups" {
  value       = var.user_groups
  description = "The principals for the Gemini Enterprise users groups."
}

output "gemini_enterprise_ip" {
  value       = var.deployment_type != "none" ? google_compute_address.gemini_enterprise_ip[0].address : null
  description = "The reserved IP address for the load balancer."
}

output "dns_auth_records" {
  value       = var.deployment_type != "none" && var.cert_management_choice == "google_managed" ? google_certificate_manager_dns_authorization.gemini_enterprise_dns_auth[0].dns_resource_record : null
  description = "DNS Authorization resource records for Google-managed certificate."
}

output "deployment_type" {
  value       = var.deployment_type
  description = "The deployment type of the load balancer (internal or external)."
}

output "compliance_regime" {
  value       = var.compliance_regime
  description = "The compliance regime selected during deployment."
}

output "tf_state_bucket_name" {
  value       = data.google_storage_bucket.terraform_state.name
  description = "The name of the GCS bucket used for Terraform state."
}

output "access_policy_number" {
  value       = var.access_policy_number
  description = "The Access Policy number."
}

output "main_project_id" {
  value       = var.main_project_id
  description = "The GCP Project name."
}

output "prefix" {
  value       = var.prefix
  description = "Prefix for naming resources."
}

output "region" {
  value       = var.region
  description = "GCP Region."
}

output "acl_idp_type" {
  value       = var.acl_idp_type
  description = "The Identity Provider type for Discovery Engine ACLs. Options: 'GSUITE', 'THIRD_PARTY'."
}

output "acl_workforce_pool_name" {
  value       = var.acl_workforce_pool_name
  description = "The resource name of the Workforce Identity Pool (required if acl_idp_type is 'THIRD_PARTY'). Format: locations/global/workforcePools/<pool_id>"
}

output "acl_workforce_provider_id" {
  value       = var.acl_workforce_provider_id
  description = "The ID of the Workforce Identity Pool Provider (required if acl_idp_type is 'THIRD_PARTY'). Format: <provider_id> (without acl_workforce_pool_name prefix)"
}

output "enable_chrome_enterprise_premium" {
  value       = var.enable_chrome_enterprise_premium
  description = "Whether Chrome Enterprise Premium (Zero Trust) is enabled."
}

output "use_shared_vpc" {
  value       = var.use_shared_vpc
  description = "Whether Shared VPC is used."
}

output "network_project_id" {
  value       = var.use_shared_vpc ? var.network_project_id : null
  description = "The Host Project ID."
}

output "shared_vpc_network_name" {
  value       = var.use_shared_vpc ? var.shared_vpc_network_name : null
  description = "The Shared VPC Network Name."
}

output "shared_vpc_subnet_name" {
  value       = var.use_shared_vpc ? var.shared_vpc_subnet_name : null
  description = "The Shared VPC Subnet Name."
}

output "shared_vpc_proxy_subnet_name" {
  value       = var.use_shared_vpc ? var.shared_vpc_proxy_subnet_name : null
  description = "The Shared VPC Proxy Subnet Name."
}

output "gcs_data_stores" {
  description = "A mapping of formatted data store keys to their configuration, ID, and bucket details."
  value = { for k, v in var.gcs_data_store_configs : k => {
    display_name  = v.display_name
    data_store_id = can(google_discovery_engine_data_store.gemini_enterprise_gcs_data_store[k]) ? google_discovery_engine_data_store.gemini_enterprise_gcs_data_store[k].data_store_id : null
    bucket_name   = can(google_storage_bucket.gemini_enterprise_gcs_bucket[k]) ? google_storage_bucket.gemini_enterprise_gcs_bucket[k].name : v.name
  } }
}

output "bq_data_stores" {
  description = "A mapping of formatted data store keys to their configuration, ID, dataset, and table details."
  value = { for k, v in var.bq_data_store_configs : k => {
    display_name  = v.display_name
    data_store_id = can(google_discovery_engine_data_store.gemini_enterprise_bq_data_store[k]) ? google_discovery_engine_data_store.gemini_enterprise_bq_data_store[k].data_store_id : null
    dataset_id    = can(google_bigquery_dataset.gemini_enterprise_bq_dataset[k]) ? google_bigquery_dataset.gemini_enterprise_bq_dataset[k].dataset_id : v.dataset_id
    table_id      = v.table_id
  } }
}

output "analytics_dataset_id" {
  value       = var.enable_analytics ? google_bigquery_dataset.analytics_dataset[0].dataset_id : null
  description = "The BigQuery dataset ID for Gemini Analytics."
}

output "analytics_sa_email" {
  value       = var.enable_analytics ? google_service_account.analytics_sa[0].email : null
  description = "The email of the service account for Gemini Analytics."
}

output "analytics_repo_name" {
  value       = var.enable_analytics ? google_artifact_registry_repository.analytics_repo[0].name : null
  description = "The name of the Artifact Registry repository for Gemini Analytics."
}
