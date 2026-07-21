output "hub" {
  description = "The NCC hub ID."
  value       = google_network_connectivity_hub.hub.id
}

output "spokes" {
  description = "The NCC spokes."
  value       = google_network_connectivity_spoke.spokes
}