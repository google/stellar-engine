output "gke-cluster" {
  description = "Deployed GKE cluster."
  value       = module.cluster
  sensitive   = true
}
