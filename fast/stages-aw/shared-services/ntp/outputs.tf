output "relay_ip" {
  description = "Internal IP address of the NTP relay VM."
  value       = module.ntp-relay.internal_ip
}

output "relay_self_link" {
  description = "Self-link of the NTP relay VM instance."
  value       = module.ntp-relay.self_link
}

output "service_account" {
  description = "Service account email used by the NTP relay VM."
  value       = module.ntp-relay-sa.email
}
