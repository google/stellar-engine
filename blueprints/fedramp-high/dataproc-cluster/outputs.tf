output "dataproc_bucket" {
  description = "GCS Bucket for DataProc."
  value       = module.gcs.bucket.name
}

output "dataproc_cluster" {
  description = "Dataproc cluster name."
  value       = module.dataproc_cluster.name
}
