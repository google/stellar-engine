output "id" {
  description = "Job ID."
  value       = module.pubsub_job.id
}

output "state" {
  description = "Job state."
  value       = module.pubsub_job.state
}