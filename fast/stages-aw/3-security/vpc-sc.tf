/**
 * Copyright 2024 Google LLC
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
  # access levels defined in code or via the factory, which the vpc-sc module
  # only resolves when referenced as "$access_levels:<name>"
  _vpc_sc_access_level_names = toset(concat(
    keys(var.vpc_sc.access_levels),
    [
      for f in try(fileset(
        pathexpand(var.factories_config.vpc_sc.access_levels), "**/*.yaml"
      ), []) : trimsuffix(f, ".yaml")
    ]
  ))
  _vpc_sc_dry_run_spec = try(var.vpc_sc.perimeter_default.dry_run_spec, null)
  # map bare access level names to context references so existing
  # configurations keep resolving to the access levels created here, and pass
  # an omitted to.resources as an empty list because the module iterates on it
  _vpc_sc_egress_policies = {
    for k, v in var.vpc_sc.egress_policies : k => merge(v, {
      from = merge(v.from, {
        access_levels = [
          for a in try(v.from.access_levels, []) : (
            contains(local._vpc_sc_access_level_names, a)
            ? "$access_levels:${a}"
            : a
          )
        ]
      })
      to = merge(v.to, {
        resources = try(v.to.resources, null) == null ? [] : v.to.resources
      })
    })
  }
  _vpc_sc_ingress_policies = {
    for k, v in var.vpc_sc.ingress_policies : k => merge(v, {
      from = merge(v.from, {
        access_levels = [
          for a in try(v.from.access_levels, []) : (
            contains(local._vpc_sc_access_level_names, a)
            ? "$access_levels:${a}"
            : a
          )
        ]
      })
      to = merge(v.to, {
        resources = try(v.to.resources, null) == null ? [] : v.to.resources
      })
    })
  }
  # a dry-run spec applies in dry run mode or when dry_run_spec is set
  _vpc_sc_use_dry_run_spec = (
    try(var.vpc_sc.perimeter_default.dry_run, false) ||
    local._vpc_sc_dry_run_spec != null
  )
  vpc_sc_ingress_policies = var.logging == null ? {} : {
    fast-org-log-sinks = {
      from = {
        access_levels = ["*"]
        identities    = values(var.logging.writer_identities)
      }
      to = {
        operations = [
          { service_name = "bigquery.googleapis.com" },
          { service_name = "logging.googleapis.com" },
          { service_name = "pubsub.googleapis.com" },
          { service_name = "storage.googleapis.com" },
        ]
        resources = ["projects/${var.logging.project_number}"]
      }
    }
  }
  # perimeter inputs before normalization, where the dry-run spec replaces
  # only the attributes that dry_run_spec sets and inherits the null ones, so
  # the enforced status never picks up a candidate value
  _vpc_sc_perimeter_inputs = (
    var.vpc_sc.perimeter_default == null
    ? null
    : {
      for k, v in {
        spec = (
          local._vpc_sc_dry_run_spec == null
          ? {}
          : { for a, l in local._vpc_sc_dry_run_spec : a => l if l != null }
        )
        status = {}
      } :
      k => merge({
        access_levels    = var.vpc_sc.perimeter_default.access_levels
        egress_policies  = var.vpc_sc.perimeter_default.egress_policies
        ingress_policies = var.vpc_sc.perimeter_default.ingress_policies
        resources        = var.vpc_sc.perimeter_default.resources
        restricted_services = yamldecode(file(
          var.factories_config.vpc_sc.restricted_services
        ))
      }, v)
    }
  )
  vpc_sc_perimeters = (
    local._vpc_sc_perimeter_inputs == null
    ? null
    : {
      for k, v in local._vpc_sc_perimeter_inputs : k => {
        access_levels = [
          for a in v.access_levels : (
            contains(local._vpc_sc_access_level_names, a)
            ? "$access_levels:${a}"
            : a
          )
        ]
        # the module expects policy keys in context format and keeps list
        # order, sorting preserves the previous key-ordered policy blocks
        egress_policies = [
          for p in sort(distinct(v.egress_policies)) :
          "$egress_policies:${p}"
        ]
        ingress_policies = [
          for p in sort(distinct(concat(
            v.ingress_policies,
            var.logging == null ? [] : ["fast-org-log-sinks"]
          ))) : "$ingress_policies:${p}"
        ]
        restricted_services = v.restricted_services
        resources = distinct(concat(
          v.resources,
          !local._vpc_sc_discovery_enabled ? [] : [
            for n in module.vpc-sc-discovery[0].project_numbers :
            "projects/${n}"
          ]
        ))
      }
    }
  )
  _vpc_sc_discovery_enabled = (
    try(var.vpc_sc.resource_discovery.enabled, false) == true
  )
  _vpc_sc_discovery_parent = coalesce(
    try(var.vpc_sc.resource_discovery.parent, null),
    "organizations/${var.organization.id}"
  )
}

module "vpc-sc-discovery" {
  source           = "../../../modules/projects-data-source"
  count            = local._vpc_sc_discovery_enabled ? 1 : 0
  parent           = local._vpc_sc_discovery_parent
  ignore_folders   = try(var.vpc_sc.resource_discovery.ignore_folders, [])
  ignore_projects  = try(var.vpc_sc.resource_discovery.ignore_projects, [])
  include_projects = try(var.vpc_sc.resource_discovery.include_projects, [])
}


module "vpc-sc" {
  source = "../../../modules/vpc-sc"
  # only enable if the default perimeter is defined
  count         = var.vpc_sc.perimeter_default == null ? 0 : 1
  access_policy = var.vpc_sc.access_policy
  access_policy_create = (
    var.vpc_sc.access_policy != null ? null : {
      parent = "organizations/${var.organization.id}"
      title  = "default"
    }
  )
  access_levels   = var.vpc_sc.access_levels
  egress_policies = local._vpc_sc_egress_policies
  ingress_policies = merge(
    local._vpc_sc_ingress_policies,
    local.vpc_sc_ingress_policies
  )
  factories_config = {
    access_levels    = var.factories_config.vpc_sc.access_levels
    egress_policies  = var.factories_config.vpc_sc.egress_policies
    ingress_policies = var.factories_config.vpc_sc.ingress_policies
  }
  project_id_search_scope = var.vpc_sc.project_id_search_scope
  perimeters = {
    default = {
      spec = (
        local._vpc_sc_use_dry_run_spec ? local.vpc_sc_perimeters.spec : null
      )
      # dry run alone drops the enforced configuration, while dry_run_spec
      # keeps it and trials the candidate in the dry-run spec
      status = (
        !var.vpc_sc.perimeter_default.dry_run
        ? local.vpc_sc_perimeters.status
        : null
      )
      use_explicit_dry_run_spec = local._vpc_sc_use_dry_run_spec
    }
  }
}
