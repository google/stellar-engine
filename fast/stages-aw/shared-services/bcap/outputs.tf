output "attachment_names" {
  description = "Names of the created VLAN attachments."
  value = {
    for k, attachment in google_compute_interconnect_attachment.attachments : k => attachment.name
  }
}

output "cloud_routers" {
  description = "Details of the created Cloud Routers (map keyed by 'router1', 'router2')."
  value       = google_compute_router.routers
}

output "pairing_keys" {
  description = "Pairing keys for each VLAN attachment. Provide these to the BCAP/DISA team."
  value = {
    for k, attachment in google_compute_interconnect_attachment.attachments : k => attachment.pairing_key
  }
  sensitive = true
}

output "vlan_attachments" {
  description = "Details of the created VLAN attachments."
  value       = google_compute_interconnect_attachment.attachments
}
