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

output "additional_bastions" {
  description = "Details of additional multi-role bastion hosts keyed by additional_bastions key."
  value = {
    for k, v in var.additional_bastions : k => {
      firewall_name         = google_compute_firewall.additional[k].name
      instance_name         = coalesce(v.instance_name, k)
      internal_ip           = module.additional-bastion-vm[k].internal_ip
      service_account_email = google_service_account.additional[k].email
    }
  }
}

output "compute_service_account_email" {
  description = "The email of the compute service account."
  value       = google_service_account.compute.email
}

output "internal_ip" {
  description = "The internal IP address of the primary bastion VM."
  value       = module.bastion-vm.internal_ip
}

output "subnet_self_link" {
  description = "The self link of the subnet."
  value       = data.google_compute_subnetwork.subnetwork.self_link
}

output "vpc_self_link" {
  description = "The self link of the VPC."
  value       = data.google_compute_network.network.self_link
}
