output "ids" {
  description = "Secret IDs."
  value       = module.secret-manager.ids
}

output "secrets" {
  description = "Secret resources."
  value       = module.secret-manager.secrets
}
