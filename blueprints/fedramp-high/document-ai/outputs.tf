/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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