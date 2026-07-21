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
  # Map environments to their tenants and their respective networking details
  envs = { for env_name, env_v in var.tenant_environments : env_name => {
    folder = env_v
  } }

  vdss = {
    landing_host   = module.vdss-host-project.project_id
    dmz_vpc        = module.dmz-vpc.id
    landing_vpc    = module.vdss-vpc.id
    external_lb_ip = module.elb-nva-dmz[var.regions.primary].forwarding_rules[""].ip_address
    self_link      = module.vdss-vpc.self_link
  }

  host_project_ids = {}
  host_project_numbers = {
    prod-landing = module.vdss-host-project.number
  }
  env_spoke = {}
  tfvars = {
    host_project_ids     = local.host_project_ids
    host_project_numbers = local.host_project_numbers
    envs                 = local.envs
    vdss                 = local.vdss
    env_spoke            = local.env_spoke
    hub_id               = google_network_connectivity_hub.main.id
    edge_group_id        = google_network_connectivity_group.groups["edge"].id
    ilb_ips = {
      transit = module.ilb-nva-tenant-transit[var.regions.primary].forwarding_rule_addresses[""]
    }
    kms_keys = {
      for region, kms in module.kms : region => kms.key_ids
    }
  }
  tfvars_shared_services = {
    bcap = {
      network_name      = module.bcap-spoke-vpc.name
      subnetwork_name   = module.bcap-spoke-vpc.subnets["${var.regions.primary}/bcap-landing"].name
      subnetwork_region = module.bcap-spoke-vpc.subnets["${var.regions.primary}/bcap-landing"].region
    }
    hub_project_id      = module.vdss-host-project.name,
    host_project_id     = module.vdss-host-project.name,
    network             = module.shared-services-vpc.self_link,
    subnetwork          = module.shared-services-vpc.subnets["${var.regions.primary}/shared-services"].self_link, # TODO swap in actual subnet self_link
    encryption_key      = module.kms[var.regions.primary].keys["ntp"].id
    smtp_encryption_key = module.kms[var.regions.primary].keys["smtp"].id
    vpc_self_links = {
      csp_landing     = module.csp-landing-vpc.self_link
      landing         = module.vdss-vpc.self_link
      shared_services = module.shared-services-vpc.self_link
      tenant_transit  = module.tenant-transit-vpc.self_link
    }
  }
}

# generate tfvars file for subsequent stages

resource "local_file" "tfvars" {
  for_each        = var.outputs_location == null ? {} : { 1 = 1 }
  file_permission = "0644"
  filename        = "${try(pathexpand(var.outputs_location), "")}/tfvars/3-networking.auto.tfvars.json"
  content         = jsonencode(local.tfvars)
}

resource "google_storage_bucket_object" "tfvars" {
  bucket  = var.automation.outputs_bucket
  name    = "tfvars/3-networking.auto.tfvars.json"
  content = jsonencode(local.tfvars)
}

resource "google_storage_bucket_object" "tfvars_shared_services" {
  bucket  = var.automation.outputs_bucket
  name    = "tfvars/3-networking-shared-services.auto.tfvars.json"
  content = jsonencode(local.tfvars_shared_services)
}

resource "local_file" "rsa-out" {
  content  = nonsensitive(tls_private_key.ngfw-ssh.private_key_openssh)
  filename = "${path.module}/id_rsa"
}

resource "local_file" "rsa-pub-out" {
  content  = nonsensitive(tls_private_key.ngfw-ssh.public_key_openssh)
  filename = "${path.module}/id_rsa.pub"
}

# outputs

output "external_lb_ip" {
  description = "The public IP of the external load balancer."
  value       = module.elb-nva-dmz[var.regions.primary].forwarding_rules[""].ip_address
}

# output "host_project_ids" {
#   description = "Network project ids."
#   value       = local.host_project_ids
# }

output "host_project_numbers" {
  description = "Network project numbers."
  value       = local.host_project_numbers
}

output "ngfw_password" {
  description = "Password for authenticating to the NGFW."
  sensitive   = true
  value       = random_password.password
}

# output "test_vm_ips" {
#   description = "Internal IP addresses of the test web servers."
#   value       = { for k, v in module.test-vms : k => v.internal_ip }
# }

output "tfvars" {
  description = "Terraform variables file for the following stages."
  sensitive   = true
  value       = local.tfvars
}