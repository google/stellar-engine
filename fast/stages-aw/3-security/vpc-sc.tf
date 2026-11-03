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
  vpc_sc_perimeter = (
    var.vpc_sc.perimeter_default == null
    ? null
    : merge(var.vpc_sc.perimeter_default, {
      access_levels = [
        for a in var.vpc_sc.perimeter_default.access_levels : (
          contains(local._vpc_sc_access_level_names, a)
          ? "$access_levels:${a}"
          : a
        )
      ]
      # the module expects policy keys in context format and keeps list order,
      # sorting preserves the previous key-ordered policy blocks
      egress_policies = [
        for p in sort(distinct(var.vpc_sc.perimeter_default.egress_policies)) :
        "$egress_policies:${p}"
      ]
      ingress_policies = [
        for p in sort(distinct(concat(
          var.vpc_sc.perimeter_default.ingress_policies,
          var.logging == null ? [] : ["fast-org-log-sinks"]
        ))) : "$ingress_policies:${p}"
      ]
      restricted_services = yamldecode(file(
        var.factories_config.vpc_sc.restricted_services
      ))
      resources = distinct(concat(
        var.vpc_sc.perimeter_default.resources,
        var.vpc_sc.resource_discovery.enabled != true ? [] : [
          for v in module.vpc-sc-discovery[0].project_numbers :
          "projects/${v}"
        ]
      ))
    })
  )
}

module "vpc-sc-discovery" {
  source           = "../../../modules/projects-data-source"
  count            = var.vpc_sc.resource_discovery.enabled == true ? 1 : 0
  parent           = "organizations/${var.organization.id}"
  ignore_folders   = var.vpc_sc.resource_discovery.ignore_folders
  ignore_projects  = var.vpc_sc.resource_discovery.ignore_projects
  include_projects = var.vpc_sc.resource_discovery.include_projects
}


module "vpc-sc" {
  source = "../../../modules/vpc-sc"
  # only enable if the default perimeter is defined
  count         = var.vpc_sc.perimeter_default == null ? 0 : 1
  access_policy = null
  access_policy_create = {
    parent = "organizations/${var.organization.id}"
    title  = "default"
  }
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
  perimeters = {
    default = {
      spec = (
        var.vpc_sc.perimeter_default.dry_run ? local.vpc_sc_perimeter : null
      )
      status = (
        !var.vpc_sc.perimeter_default.dry_run ? local.vpc_sc_perimeter : null
      )
      use_explicit_dry_run_spec = var.vpc_sc.perimeter_default.dry_run
    }
  }
}
