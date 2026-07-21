output "dns_zone_gcr_name" {
  value       = module.psc.dns_zone_gcr_name
  description = "Name for Managed DNS zone for GCR."
}

output "dns_zone_googleapis_name" {
  value       = module.psc.dns_zone_googleapis_name
  description = "Name for Managed DNS zone for GoogleAPIs."
}

output "dns_zone_pkg_dev_name" {
  value       = module.psc.dns_zone_pkg_dev_name
  description = "Name for Managed DNS zone for PKG_DEV."
}

output "global_address_id" {
  value       = module.psc.global_address_id
  description = "An identifier for the global address created for the private service connect with format `projects/{{project}}/global/addresses/{{name}}`."
}

output "private_ip_allocation" {
  description = "The IP that was allocated for this service connection."
  value       = module.psc.private_service_connect_ip
}