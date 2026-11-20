/**
 * Copyright 2023 Google LLC
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

output "connection_internal_ip" {
  value       = module.postgres.ip
  description = "Conntection internal IP address."
}

output "psc_dns_name" {
  value       = var.psc_config == null ? null : module.postgres.dns_name
  description = "DNS name of the instance, for the DNS record of the Private Service Connect endpoint. Null unless psc_config is set."
}

output "psc_service_attachment_link" {
  value       = var.psc_config == null ? null : module.postgres.psc_service_attachment_link
  description = "Service attachment that a Private Service Connect endpoint targets. Null unless psc_config is set."
}
