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
  primary_location_gcs    = element(var.locations.gcs, 0)
  primary_location_kms    = element(var.locations.kms, 0)
  primary_location_pubsub = try(element(var.locations.pubsub, 0), null)

  project_config_yaml = yamldecode(file("../../../project-config.yml"))
  project_map = {
    for p in local.project_config_yaml.projects : p.name =>
    replace(replace(replace(p.project_name, "<TENANT_NAME>", lower(var.tenant.name)), "<ORG_SUBDOMAIN>", lower(substr(split(".", var.organization.domain)[0], 0, 7))), "<MACOM>", lower(var.tenant.macom))
  }

  tenant_subnets_map_of_maps = {
    for pairing in setproduct(values(local.tenant_accounts), [var.regions.primary]) : "${pairing[0].main_project}-${pairing[1]}" => {
      "project"         = pairing[0].main_project,
      "tenant"          = pairing[0].tenant,
      "admin_principal" = pairing[0].admin_principal
      "region"          = pairing[1],
      "env"             = pairing[0].env
      "tenant_key"      = "${pairing[0].env}-${pairing[0].tenant}"
    }
  }

  allowed_api_data = yamldecode(file("./data/allowed_apis.yaml"))
  lz_data   = yamldecode(file("./data/lz_exceptions.yaml"))

  coa2_allowed_apis = concat(
    local.allowed_api_data.allowed_apis,
    local.lz_data.COA2
  )
}

resource "google_project_organization_policy" "shared_svcs_project_policy" {
  for_each   = local.tenant_subnets_map_of_maps
  project    = each.value.project
  constraint = "constraints/gcp.restrictServiceUsage"

  list_policy {
    allow {
      values = local.coa2_allowed_apis
    }
  }
}