output "cluster_master_version" {
  description = "Master version."
  value       = module.cluster.master_version
}

output "gke_cluster_endpoint" {
  description = "The endpoint of the GKE cluster."
  value       = module.cluster.endpoint
}

output "gke_cluster_name" {
  description = "The name of the GKE cluster."
  value       = module.cluster.name
}

output "keyring_id" {
  description = "Fully qualified keyring id."
  value       = module.kms.id
}

output "keyring_location" {
  description = "Keyring location."
  value       = module.kms.location
}

output "keyring_name" {
  description = "Keyring name."
  value       = module.kms.name
}

output "keyring_resource" {
  description = "Keyring resource."
  value       = module.kms.keyring
}

output "keyrings_keys" {
  description = "Key resources."
  value       = module.kms.keys
}

output "nodepool_id" {
  description = "Fully qualified nodepool id."
  value       = module.cluster_nodepool.id
}

output "nodepool_name" {
  description = "Nodepool name."
  value       = module.cluster_nodepool.name
}

output "nodepool_service_account_email" {
  description = "Service account email."
  value       = module.cluster_nodepool.service_account_email
}

output "subnet_regions" {
  description = "Map of subnet regions keyed by name."
  value       = module.vpc.subnet_regions
}

output "subnets" {
  description = "Subnet resources."
  value       = module.vpc.subnets
}

output "vpc-network" {
  description = "Network resource."
  value       = module.vpc.network
}

output "vpc-subnet_ids" {
  description = "Map of subnet IDs keyed by name."
  value       = module.vpc.subnet_ids
}

output "vpc-subnet_ips" {
  description = "Map of subnet address ranges keyed by name."
  value       = module.vpc.subnet_ips
}
