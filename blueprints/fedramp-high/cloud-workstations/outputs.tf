output "workstation_cluster" {
  description = "The cluster that was created to host the workstations."
  value       = module.workstations.id
}

output "workstation_config" {
  description = "The workstation config that is used to create workstation instances."
  value       = module.workstations.workstation_configs
}

output "workstation_key_sa" {
  description = "The service account that was created to use the KMS key."
  value       = google_service_account.workstation_config_key_user
}

output "workstations" {
  description = "The created workstation instances."
  value       = module.workstations.workstations
}