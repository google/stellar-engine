output "access_levels" {
  description = "The list of created access levels with their details."
  value       = module.access_context_manager.access_levels
}

output "service_perimeters" {
  description = "The list of created service perimeters with their details."
  value       = module.access_context_manager.service_perimeters
}

