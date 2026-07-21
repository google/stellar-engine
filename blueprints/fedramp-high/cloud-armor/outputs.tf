output "policies" {
  description = "All created policy resources."
  value       = google_compute_region_security_policy.policy
}

output "policy_names" {
  description = "All created policy names."
  value = { for k, v in google_compute_region_security_policy.policy :
    k => v.name
  }
}

output "policy_rules" {
  description = "All created policy rule resources."
  value       = google_compute_region_security_policy_rule.policy_rule
}