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
output "compute-engine-vm-instance" {
  description = "Instance resource."
  sensitive   = true
  value       = try(module.compute-engine-vm.instance)
}

output "compute-engine-vm-instance-id" {
  description = "Fully qualified instance id."
  value       = module.compute-engine-vm.id
}

output "compute-engine-vm-internal_ip" {
  description = "Instance main interface internal IP address."
  value       = module.compute-engine-vm.internal_ip
}

output "compute-engine-vm-internal_ips" {
  description = "Instance interfaces internal IP addresses."
  value       = module.compute-engine-vm.internal_ips
}

output "compute-engine-vm-service_account" {
  description = "Service account resource."
  value       = module.compute-engine-vm.service_account
}

output "compute-engine-vm-service_account_email" {
  description = "Service account email."
  value       = module.compute-engine-vm.service_account_email
}
