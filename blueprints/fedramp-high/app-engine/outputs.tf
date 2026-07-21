output "app_id" {
  value       = module.app-engine.app_id
  description = "Identifier of the app."
}

output "code_bucket" {
  value       = module.app-engine.code_bucket
  description = "GCS bucket where the app code is stored."
}

output "default_bucket" {
  value       = module.app-engine.default_bucket
  description = "GCS bucket where the app content is stored."
}

output "default_hostname" {
  value       = module.app-engine.default_hostname
  description = "Default hostname for the app."
}

output "gcr_domain" {
  value       = module.app-engine.gcr_domain
  description = "GCR domain used for storing managed Docker images."
}

output "id" {
  description = "An identifier for the resource."
  value       = module.app-engine.id
}

output "name" {
  value       = module.app-engine.name
  description = "Unique name of the app."
}
