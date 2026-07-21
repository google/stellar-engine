output "dataflow-job" {
  description = "Dataflow job."
  value       = google_dataflow_job.job.name
}

output "gcs-bucket" {
  description = "GCS Bucket."
  value       = module.gcs.bucket.name
}
