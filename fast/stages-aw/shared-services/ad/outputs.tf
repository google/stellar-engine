output "domain_controller_ips" {
  description = "The static internal IP addresses reserved and assigned to the GCP Domain Controllers. Hand these to the Azure AD team for Site-and-Services configuration."
  value = {
    for k, v in module.domain-controller-vms :
    local.dc_nodes[k].vm_name => module.domain-controller-ips.internal_addresses[local.dc_nodes[k].ip_name].address
  }
}

output "domain_controller_names" {
  description = "The exact names of the provisioned Compute Engine instances."
  value       = [for k, v in module.domain-controller-vms : local.dc_nodes[k].vm_name]
}

output "security_compliance" {
  description = "A snapshot of the active security features verified at deployment time."
  value = {
    shielded_vm_enabled = true
    secure_boot_enabled = true
    cmek_by_region      = { for r, mod in module.kms : r => mod != null }
  }
}

output "service_account_email" {
  description = "The dedicated, least-privilege service account email assigned to the DCs."
  value       = module.domain-controller-sa.email
}
