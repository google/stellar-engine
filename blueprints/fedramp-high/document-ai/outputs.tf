output "id" {
  description = "Document AI processor id."
  value       = google_document_ai_processor.processor.id
}

output "input_bucket" {
  description = "Bucket that takes documents as input."
  value       = module.input_bucket
}

output "output_bucket" {
  description = "Bucket that stores document processor output."
  value       = module.output_bucket
}

output "processor" {
  description = "Document AI processor."
  value       = google_document_ai_processor.processor
}

output "workflow" {
  description = "Workflow that runs the batch processing."
  value       = module.workflows.workflow
}