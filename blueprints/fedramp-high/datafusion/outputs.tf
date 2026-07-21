output "id" {
  description = "Fully qualified instance id."
  value       = module.datafusion.id
}

output "resource" {
  description = "DataFusion resource."
  value       = module.datafusion.resource
}

output "service_endpoint" {
  description = "DataFusion Service Endpoint."
  value       = module.datafusion.service_account
}

output "version" {
  description = "DataFusion version."
  value       = module.datafusion.version
}
