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
# tfdoc:file:description Networking folder and hierarchical policy.

locals {
  service_accounts = {
    for k, v in coalesce(var.service_accounts, {}) :
    k => "serviceAccount:${v}" if v != null
  }
  proxy_subnets = yamldecode(file("./data/subnets/proxy-subnets.yaml")).tenant_environments_proxy_subnets

  # The following section maps project names for stage 3 using the projects-config.yml inside of the root directory
  formatted_regime    = lower(replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " "))
  project_config_yaml = yamldecode(file("../../../project-config.yml"))
  project_map = {
    for p in local.project_config_yaml.projects : p.name =>
    replace(replace(p.project_name, "<PREFIX>", var.prefix), "<REGIME>", local.formatted_regime)
  }
  allowed_api_data = yamldecode(file("./data/allowed_apis.yaml"))
  lz_data   = yamldecode(file("./data/lz_exceptions.yaml"))

  coa2_allowed_apis = concat(
    local.allowed_api_data.allowed_apis,
    local.lz_data.COA2
  )

}
module "folder" {
  source        = "../../../modules/folder"
  parent        = "organizations/${var.organization.id}"
  name          = "Networking"
  folder_create = var.folder_ids.networking == null
  id            = var.folder_ids.networking
  contacts = (
    var.essential_contacts == null
    ? {}
    : { (var.essential_contacts) = ["ALL"] }
  )
  firewall_policy = {
    name   = "default"
    policy = module.firewall-policy-default.id
  }
}

resource "local_file" "generated_ingress_rule" {
  content = templatefile("${var.factories_config.data_dir}/hierarchical-ingress-rules.yaml.tmpl", {
    vdss-project-id = local.project_map["vdss-host-project"]
  })

  filename = "${var.factories_config.data_dir}/hierarchical-ingress-rules.yaml"
}

module "firewall-policy-default" {
  source    = "../../../modules/net-firewall-policy"
  name      = "${var.prefix}-${var.factories_config.firewall_policy_name}-${replace(lower(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime)), "_", "-")}"
  parent_id = module.folder.id
  factories_config = {
    cidr_file_path          = "${var.factories_config.data_dir}/cidrs.yaml"
    ingress_rules_file_path = "${var.factories_config.data_dir}/hierarchical-ingress-rules.yaml"
  }
}

resource "google_project_organization_policy" "net_vdss_host_policy" {
  project    = module.vdss-host-project.project_id
  constraint = "constraints/gcp.restrictServiceUsage"

  list_policy {
    allow {
      values = local.coa2_allowed_apis
    }
  }
}

resource "google_project_organization_policy" "shared_svcs_project_policy" {
  project    = var.shared_services_project_id
  constraint = "constraints/gcp.restrictServiceUsage"

  list_policy {
    allow {
      values = local.coa2_allowed_apis
    }
  }
}