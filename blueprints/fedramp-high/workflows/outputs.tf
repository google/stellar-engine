output "service_account" {
  description = "The workflow service account."
  value       = module.workflows.service_account
}

output "workflow" {
  description = "The newly created workflow."
  value       = module.workflows.workflow
}