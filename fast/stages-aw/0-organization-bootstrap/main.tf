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
locals {
  gcs_storage_class = {
    for loc in local.locations.gcs : loc => (
      length(split("-", loc)) < 2 ? "MULTI_REGIONAL" : "REGIONAL"
    )
  }
  locations = {
    bq      = var.locations.bq
    gcs     = var.locations.gcs
    logging = compact(concat([try(local.checklist.location, null)], var.locations.logging))
    pubsub  = var.locations.pubsub
    kms     = var.locations.kms
  }
  _gcp_devops_group = coalesce(var.groups.gcp-devops, var.gcp_devops_group)
  _groups = {
    gcp-billing-admins      = coalesce(var.groups.gcp-billing-admins, var.gcp_billing_admins_group)
    gcp-devops              = local._gcp_devops_group
    gcp-vpc-network-admins  = coalesce(var.groups.gcp-vpc-network-admins, var.gcp_vpc_network_admins_group)
    gcp-organization-admins = coalesce(var.groups.gcp-organization-admins, var.gcp_organization_admins_group)
    gcp-security-admins     = coalesce(var.groups.gcp-security-admins, var.gcp_security_admins_group)
    gcp-support             = coalesce(var.groups.gcp-support, var.gcp_support_group, local._gcp_devops_group)
  }
  principals = {
    for k, v in local._groups : k => (
      can(regex("^[a-zA-Z]+:", v))
      ? v
      : "group:${v}@${var.organization.domain}"
    )
  }

  # The following section maps project names for stage 0 using the projects-config.yml inside of the root directory
  project_config_yaml = yamldecode(file("../../../project-config.yml"))
  project_map = {
    for p in local.project_config_yaml.projects : p.name =>
    p.name == "centralized-logging-project" ? replace(p.project_name, "<AW-id>", substr(tostring(google_assured_workloads_workload.organization[0].resources[0].resource_id), -4, 4)) : # lz-audit-<last 4 of assured workload id>
    p.project_name
  }
}
