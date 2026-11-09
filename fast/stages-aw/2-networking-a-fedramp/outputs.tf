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
    proxy_only   = module.env-spoke-vpc[name].subnets_proxy_only["${var.regions.primary}/proxy-${var.regions.primary}"].self_link
  } }
  landing = {
    host_project = module.landing-project.project_id
    vpc          = module.landing-vpc.id
  }
  host_project_ids = module.env-spoke-vpc
  host_project_numbers = {
    prod-landing = module.landing-project.number
  }
  ncc_spokes_output = {
    router_appliances = {
      for k, v in google_network_connectivity_spoke.router_appliances : k => v.id
    }
    tunnels = {
      for k, v in google_network_connectivity_spoke.tunnels : k => v.id
    }
    vlan_attachments = {
      for k, v in google_network_connectivity_spoke.vlan_attachments : k => v.id
    }
    vpcs = {
      for k, v in google_network_connectivity_spoke.vpcs : k => v.id
    }
  }
  tfvars = {
    host_project_ids     = local.host_project_ids
    host_project_numbers = local.host_project_numbers
    envs                 = local.envs
    landing              = local.landing
    ncc_groups           = local._ctx_ncc_groups
    ncc_hubs             = local._ctx_ncc_hubs
    ncc_spokes           = local.ncc_spokes_output
  }
}

# generate tfvars file for subsequent stages

resource "local_file" "tfvars" {
  for_each        = var.outputs_location == null ? {} : { 1 = 1 }
  file_permission = "0600"
  filename        = "${try(pathexpand(var.outputs_location), "")}/tfvars/2-networking.auto.tfvars.json"
  content         = jsonencode(local.tfvars)
}

resource "google_storage_bucket_object" "tfvars" {
  bucket  = var.automation.outputs_bucket
  name    = "tfvars/2-networking.auto.tfvars.json"
  content = sensitive(jsonencode(local.tfvars))
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

output "landing" {
  description = "Landing host project and VPC identifiers."
  value       = local.landing
}

output "ncc_groups" {
  description = "Network Connectivity Center group IDs keyed by hub/group."
  value       = local._ctx_ncc_groups
}

output "ncc_hubs" {
  description = "Network Connectivity Center hub IDs keyed by hub name."
  value       = local._ctx_ncc_hubs
}

output "ncc_spokes" {
  description = "Network Connectivity Center spoke IDs grouped by spoke type."
  value       = local.ncc_spokes_output
}

output "tfvars" {
  description = "Terraform variables file for the following stages."
  sensitive   = true
  value       = local.tfvars
}
