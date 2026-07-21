output "cloud_run" {
  description = "Cloud Run Service that was created."
  value       = module.cloud_run
}

output "service-account" {
  description = "Service account that was created to run the Cloud Run Service."
  value       = google_service_account.cloud_run_service_account.email
}
