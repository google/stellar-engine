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
  description = "Fully qualified instance id."
  value       = module.datafusion.id
}

output "resource" {
  description = "DataFusion resource."
  value       = module.datafusion.resource
}

output "service_endpoint" {
  description = "DataFusion Service Endpoint."
  value       = module.datafusion.service_account
}

output "version" {
  description = "DataFusion version."
  value       = module.datafusion.version
}
