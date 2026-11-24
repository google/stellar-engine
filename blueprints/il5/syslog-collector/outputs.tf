# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

output "ilb_ip_address" {
  description = "Internal load balancer IPv4 address for TLS syslog ingestion."
  value       = module.syslog-ilb.forwarding_rule_addresses[""]
}

output "instance_group_manager_id" {
  description = "Fully qualified ID of the regional managed instance group."
  value       = module.syslog-mig.id
}

output "service_account_email" {
  description = "Email of the dedicated syslog collector service account."
  value       = module.syslog-sa.email
}
