output "input_bucket" {
  description = "Bucket that takes documents as input."
  value       = module.input_bucket
}

output "output_bucket" {
  description = "Bucket that stores translated output."
  value       = module.output_bucket
}

output "workflow" {
  description = "Workflow that runs the batch processing."
  value       = module.workflows.workflow
}