/**
 * Copyright 2024 Google LLC
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

output "scanner_internal_ips" {
  description = "Map of Nessus Scanner instance names to internal IP addresses."
  value       = { for k, v in module.scanner-vms : k => v.internal_ip }
}

output "service_account_email" {
  description = "Service account email attached to the Nessus Scanner VMs."
  value       = google_service_account.scanner.email
}

resource "google_storage_bucket_object" "tfvars" {
  bucket = var.automation.outputs_bucket
  name   = "tfvars/shared-services-acas-scanner.auto.tfvars.json"
  content = jsonencode({
    acas_scanner_ips = [for k, v in module.scanner-vms : v.internal_ip]
  })
}

