output "ids_name" {
  description = "The name of the Cloud IDS instance."
  value       = module.cloud_ids.ids_name
}

output "ids_private_ip_range_name" {
  description = "The private IP range name for the IDS."
  value       = module.cloud_ids.ids_private_ip_range_name
}

output "packet_mirroring_policy_name" {
  description = "The name of the packet mirroring policy."
  value       = module.cloud_ids.packet_mirroring_policy_name
}