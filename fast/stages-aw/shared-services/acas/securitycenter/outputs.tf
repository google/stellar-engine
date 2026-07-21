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

output "internal_ip" {
  description = "Internal IP of the ACAS SecurityCenter instance."
  value       = module.sc-vm.internal_ip
}

output "service_account_email" {
  description = "Service account email attached to SecurityCenter."
  value       = google_service_account.sc.email
}

resource "google_storage_bucket_object" "tfvars" {
  bucket = var.automation.outputs_bucket
  name   = "tfvars/shared-services-acas-sc.auto.tfvars.json"
  content = jsonencode({
    acas_securitycenter_ip = module.sc-vm.internal_ip
  })
}

