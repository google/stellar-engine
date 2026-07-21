output "bigtable_service_identity_email" {
  description = "The email of the Bigtable Service Identity."
  value       = google_project_service_identity.bigtable_sa.email
}

output "bigtable_service_identity_uid" {
  description = "The ID of the Bigtable Service Identity."
  value       = google_project_service_identity.bigtable_sa.id
}

output "cluster_info" {
  description = "Information about the created Bigtable cluster."
  value = {
    cluster_id   = var.cluster_id
    zone         = var.zone
    num_nodes    = var.num_nodes
    storage_type = var.storage_type
  }
}

output "instance_name" {
  value       = var.instance_name
  description = "Bigtable instance name."
}

output "table_info" {
  description = "Information about the tables created (if any)."
  value       = module.bigtable-instance.tables
}
