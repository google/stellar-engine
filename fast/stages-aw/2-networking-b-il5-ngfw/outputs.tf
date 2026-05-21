/**
 * Copyright 2022 Google LLC
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

locals {
  envs = { for name, v in var.envs_folders : name => {
    folder = v
    vpc    = module.env-spoke-vpc[name].id
    region = var.regions.primary
    shared_subnet = module.env-spoke-vpc[name].subnet_self_links[
      "${var.regions.primary}/${[for s in try(var.subnets[lower(name)], []) : s.name if s.tenant != null][0]}"
    ]
    host_project = module.env-spoke-projects[name].project_id
    proxy_only   = module.env-spoke-vpc[name].subnets_proxy_only[lower("${var.regions.primary}/proxy-${var.regions.primary}")].self_link
  } }
  vdss = {
    landing_host = module.vdss-host-project.project_id
    dmz_vpc      = module.dmz-vpc.id
    landing_vpc  = module.vdss-vpc.id
  }
  host_project_ids = module.env-spoke-vpc
  host_project_numbers = {
    prod-landing = module.vdss-host-project.number
  }
  tfvars = {
    host_project_ids     = local.host_project_ids
    host_project_numbers = local.host_project_numbers
    envs                 = local.envs
    vdss                 = local.vdss
  }
}

# generate tfvars file for subsequent stages

resource "local_file" "tfvars" {
  for_each        = var.outputs_location == null ? {} : { 1 = 1 }
  file_permission = "0644"
  filename        = "${try(pathexpand(var.outputs_location), "")}/tfvars/2-networking.auto.tfvars.json"
  content         = jsonencode(local.tfvars)
}

resource "google_storage_bucket_object" "tfvars" {
  bucket  = var.automation.outputs_bucket
  name    = "tfvars/2-networking.auto.tfvars.json"
  content = jsonencode(local.tfvars)
}

# outputs

output "host_project_ids" {
  description = "Network project ids."
  value       = local.host_project_ids
}

output "host_project_numbers" {
  description = "Network project numbers."
  value       = local.host_project_numbers
}

resource "local_file" "rsa-out" {
  content  = nonsensitive(tls_private_key.ngfw-ssh.private_key_openssh)
  filename = "${path.module}/id_rsa"
}

resource "local_file" "rsa-pub-out" {
  content  = nonsensitive(tls_private_key.ngfw-ssh.public_key_openssh)
  filename = "${path.module}/id_rsa.pub"
}

output "ngfw_password" {
  description = "Password for authenticating to the NGFW."
  sensitive   = true
  value       = random_password.password
}

output "tfvars" {
  description = "Terraform variables file for the following stages."
  sensitive   = true
  value       = local.tfvars
}
