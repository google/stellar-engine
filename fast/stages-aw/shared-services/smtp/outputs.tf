output "relay_ip" {
  description = "Internal IP address of the SMTP relay VM."
  value       = module.smtp-relay.internal_ip
}

output "relay_self_link" {
  description = "Self-link of the SMTP relay VM instance."
  value       = module.smtp-relay.self_link
}

output "service_account" {
  description = "Service account email used by the SMTP relay VM."
  value       = module.smtp-relay-sa.email
}
