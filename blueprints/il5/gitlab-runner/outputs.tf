# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

output "instance_id" {
  description = "Fully qualified ID of the GitLab Runner VM instance."
  value       = module.runner-vm.id
}

output "instance_internal_ip" {
  description = "Internal IP address of the GitLab Runner VM instance."
  value       = module.runner-vm.internal_ip
}

output "service_account_email" {
  description = "Email address of the dedicated GitLab Runner service account."
  value       = module.runner-sa.email
}
