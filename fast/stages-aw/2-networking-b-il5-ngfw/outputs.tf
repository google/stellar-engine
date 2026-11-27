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
  dns_forwarding_zones = {
    for k, v in module.landing-dns-forwarding-zones : k => {
      domain = v.domain
      name   = v.name
    }
  }
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
  host_project_ids = {
    for k, v in module.env-spoke-projects : lower(k) => v.id
  }
  host_project_numbers = {
    prod-landing = module.vdss-host-project.number
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
  psc_google_apis_endpoints = !var.psc_google_apis.enabled ? {} : merge(
    {
      hub = {
        address       = var.psc_google_apis.hub_ip
        address_id    = module.hub-psc-addresses[0].psc["pschub0"].address.id
        endpoint_name = "pschub0"
        forwarding_rule_id = (
          module.hub-psc-addresses[0].psc["pschub0"].forwarding_rule.id
        )
        psc_connection_id = (
          module.hub-psc-addresses[0].psc["pschub0"].forwarding_rule.psc_connection_id
        )
      }
    },
    {
      for k, v in module.env-psc-addresses :
      lower(k) => {
        address       = local._psc_spoke_ips[k]
        address_id    = v.psc[local._psc_spoke_fr_names[k]].address.id
        endpoint_name = local._psc_spoke_fr_names[k]
        forwarding_rule_id = (
          v.psc[local._psc_spoke_fr_names[k]].forwarding_rule.id
        )
        psc_connection_id = (
          v.psc[local._psc_spoke_fr_names[k]].forwarding_rule.psc_connection_id
        )
      }
    }
  )
  tfvars = merge(
    {
      host_project_ids     = local.host_project_ids
      host_project_numbers = local.host_project_numbers
      envs                 = local.envs
      vdss                 = local.vdss
    },
    local._ncc_enabled ? { ncc_groups = local._ctx_ncc_groups } : {},
    local._ncc_enabled ? { ncc_hubs = local._ctx_ncc_hubs } : {},
    local._ncc_enabled ? { ncc_spokes = local.ncc_spokes_output } : {},
    (
      var.psc_google_apis.enabled
      ? { psc_google_apis_endpoints = local.psc_google_apis_endpoints }
      : {}
    )
  )
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

output "dns_forwarding_zones" {
  description = "Optional hybrid Cloud DNS forwarding zones created in the VDSS host project."
  value       = local.dns_forwarding_zones
}

output "host_project_ids" {
  description = "Network project ids."
  value       = local.host_project_ids
}

output "host_project_numbers" {
  description = "Network project numbers."
  value       = local.host_project_numbers
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

output "ngfw_admin_password_secret_id" {
  description = "Regional Secret Manager secret ID storing the NGFW administrator password when ngfw_admin_password_secret.enabled is true."
  value = try(
    module.ngfw-admin-password-secret[0].ids[var.ngfw_admin_password_secret.secret_id],
    null
  )
}

output "ngfw_password" {
  description = "Password for authenticating to the NGFW. Returns null when ngfw_admin_password_secret.enabled is true."
  sensitive   = true
  value       = var.ngfw_admin_password_secret.enabled ? null : random_password.password
}

output "ngfw_ssh_private_key_secret_id" {
  description = "Secret Manager secret ID storing the NGFW SSH private key."
  value       = module.ngfw-ssh-secrets.ids["ngfw-ssh-private-key"]
}

output "psc_google_apis_endpoints" {
  description = "Per-VPC Private Service Connect Google APIs endpoint addresses and forwarding rules."
  value       = local.psc_google_apis_endpoints
}

output "tfvars" {
  description = "Terraform variables file for the following stages."
  sensitive   = true
  value       = local.tfvars
}
