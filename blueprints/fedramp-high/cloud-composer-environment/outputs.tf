output "airflow_uri" {
  value       = google_composer_environment.main.config[0].airflow_uri
  description = "URI for Airflow."
}

output "composer_id" {
  value       = google_composer_environment.main.id
  description = "Cloud composer id."
}