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

# tfdoc:file:description Organization-level IAM.

locals {
  # reassemble logical bindings into the formats expected by the module
  _iam_bindings = merge(
    local.iam_domain_bindings,
    {
      for k, v in local.iam_principal_bindings : k => {
        authoritative = []
        additive      = v.additive
      }
    }
  )
  _iam_bindings_auth = flatten([
    for member, data in local._iam_bindings : [
      for role in data.authoritative : {
        member = member
        role   = role
      }
    ]
  ])
  _iam_bindings_add = flatten([
    for member, data in local._iam_bindings : [
      for role in data.additive : {
        member = member
        role   = role
      }
    ]
  ])
  _org_only_roles = [
    "roles/billing.admin",
    "roles/billing.creator",
    "roles/orgpolicy.policyAdmin",
    "roles/iam.organizationRoleAdmin",
    "roles/cloudsupport.admin",
    "roles/assuredworkloads.admin",
    "roles/compute.osLoginExternalUser",
    "roles/resourcemanager.organizationAdmin",
  ]
  # tflint-ignore: terraform_unused_declarations
  drs_domains = concat(var.organization.customer_id == null ? [] : [var.organization.customer_id],
    var.org_policies_config.constraints.allowed_policy_member_domains
  )
  drs_tag_name = "${var.organization.id}/${var.org_policies_config.tag_name}"

  # intermediate values before we merge in what comes from the checklist
  _iam_principals = {
    for k, v in local.iam_principal_bindings : k => v.authoritative
  }
  _iam = merge(
    {
      for r in local.iam_delete_roles : r => []
    },
    {
      for b in local._iam_bindings_auth : b.role => b.member...
    }
  )
  _iam_bindings_additive = {
    for b in local._iam_bindings_add : "${b.role}-${b.member}" => {
      member = b.member
      role   = b.role
    }
  }

  # final values combining all sources
  iam_principals = {
    for k, v in local._iam_principals : k => distinct(concat(
      v,
      try(local.checklist.iam_principals[k], [])
    ))
  }
  folder_iam_principals = {
    for principal, roles in local.iam_principals :
    principal => [
      for role in roles : role if !contains(local._org_only_roles, role)
    ]
    if length([for role in roles : role if !contains(local._org_only_roles, role)]) > 0
  }
  org_iam_principals = {
    for principal, roles in local.iam_principals :
    principal => [
      for role in roles : role if contains(local._org_only_roles, role)
    ]
    if length([for role in roles : role if contains(local._org_only_roles, role)]) > 0
  }
  iam = {
    for k, v in local._iam : k => distinct(concat(
      v,
      try(local.checklist.iam[k].authoritative, [])
    ))
  }
  iam_bindings_additive = merge(
    local._iam_bindings_additive,
    {
      for k, v in try(local.checklist.iam_bindings, {}) :
      v.key => v if lookup(local._iam_bindings_additive, v.key, null) == null
    }
  )
  folder_iam_bindings_additive = {
    for k, v in local.iam_bindings_additive : k => v
    if !contains(local._org_only_roles, v.role)
  }
  org_iam_bindings_additive = {
    for k, v in local.iam_bindings_additive : k => v
    if contains(local._org_only_roles, v.role)
  }
  # compute authoritative and additive roles for use by add-ons (checklist, etc.)
  iam_roles_authoritative = distinct(concat(
    flatten(values(local._iam_principals)),
    keys(local._iam)
  ))

  # Some of the org policies require templating to construct, they have been moved to data/custom-org-policies
  # load org policy yaml files from a subdirectory
  _org_policies_raw = merge([
    for f in try(fileset("./data/custom-org-policies/", "*_policy.yaml"), []) :
    yamldecode(templatefile("./data/custom-org-policies/${f}", {
      # NOTE:
      # If there are more variables need to be substituted, put them
      # into a separate yaml file or map, use the following line to
      # loop through them. For list values use yamlencode() function.
      # for k, v in local.common_settings : k => v
      organization_id : var.organization.id
      domain_name : var.organization.domain
      customer_id : var.organization.customer_id
      drs_tag_name : local.drs_tag_name
      allowed_policy_member_domains : var.org_policies_config.constraints.allowed_policy_member_domains
      allowed_access_boundaries : var.org_policies_config.constraints.allowed_access_boundaries
      }
  ))]...)
  # formalize the policies
  org_policies = {
    for k, v in local._org_policies_raw :
    k => {
      inherit_from_parent = try(v.inherit_from_parent, null)
      reset               = try(v.reset, null)
      rules = [
        for r in try(v.rules, []) : {
          allow = can(r.allow) ? {
            all    = try(r.allow.all, null)
            values = try(r.allow.values, null)
          } : null
          deny = can(r.deny) ? {
            all    = try(r.deny.all, null)
            values = try(r.deny.values, null)
          } : null
          enforce = try(r.enforce, null)
          condition = {
            description = try(r.condition.description, null)
            expression  = try(r.condition.expression, null)
            location    = try(r.condition.location, null)
            title       = try(r.condition.title, null)
          }
        }
      ]
    }
  }
  folder_org_policies = {
    for k, v in local.org_policies : k => v
    if k != "resourcemanager.accessBoundaries"
  }
  org_only_policies = {
    for k, v in local.org_policies : k => v
    if k == "resourcemanager.accessBoundaries"
  }
  consumer_folder_id = try(one([
    for r in google_assured_workloads_workload.organization[0].resources : r.resource_id if r.resource_type == "CONSUMER_FOLDER"
  ]), null)
}

resource "google_assured_workloads_workload" "organization" {
  count                        = var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED" ? 1 : 0
  compliance_regime            = var.assured_workloads.regime
  display_name                 = "${var.top_level_folder.name} Logging"
  location                     = lower(var.assured_workloads.location)
  organization                 = var.organization.id
  billing_account              = var.billing_account.id != null ? "billingAccounts/${var.billing_account.id}" : null
  provisioned_resources_parent = "folders/${var.top_level_folder.id}"
  resource_settings {
    display_name  = "${var.top_level_folder.name} Logging"
    resource_type = "CONSUMER_FOLDER"
  }

  violation_notifications_enabled = true
  lifecycle {
    create_before_destroy = true
    ignore_changes        = [billing_account]
  }
}

module "no-compliance-folder" {
  count  = var.assured_workloads.regime == "COMPLIANCE_REGIME_UNSPECIFIED" ? 1 : 0
  source = "../../../modules/folder"
  parent = "organizations/${var.organization.id}"
  name   = "${var.top_level_folder.name} Logging"
}

# TODO: add a check block to ensure our custom roles exist in the factory files

module "organization-logging" {
  # Preconfigure organization-wide logging settings to ensure project
  # log buckets (_Default, _Required) are created in the location
  # specified by `var.locations.logging`. This separate
  # organization-block prevents circular dependencies with later
  # project creation.
  count           = 1
  source          = "../../../modules/organization"
  organization_id = "organizations/${var.organization.id}"
  logging_settings = {
    storage_location = "global"
  }
}

module "organization" {
  source          = "../../../modules/organization-se"
  organization_id = "organizations/${var.organization.id}"
  # human (groups) IAM bindings
  iam_by_principals = {
    for k, v in local.org_iam_principals :
    k => distinct(concat(v, lookup(var.iam_by_principals, k, [])))
  }
  # additive bindings, used for roles co-managed by different stages
  iam_bindings_additive = merge(
    local.org_iam_bindings_additive,
    var.iam_bindings_additive
  )
  custom_roles = var.custom_roles
  factories_config = {
    custom_roles                  = var.factories_config.custom_roles
    org_policy_custom_constraints = "./data/custom-constraint-policies/"
  }
  org_policies = local.org_only_policies
}

module "top_level_folder" {
  source        = "../../../modules/folder"
  folder_create = false
  id            = "folders/${var.top_level_folder.id}"
  parent        = "organizations/${var.organization.id}"
  iam_by_principals = {
    for k, v in local.folder_iam_principals : # Use the filtered folder local
    k => distinct(concat(v, lookup(var.iam_by_principals, k, [])))
  }
  # machine (service accounts) IAM bindings
  iam = {
    for k, v in merge(
      {
        for k, v in local.iam : k => distinct(concat(v, lookup(var.iam, k, [])))
      },
      {
        for k, v in var.iam : k => v if lookup(local.iam, k, null) == null
      }
    ) : k => v if !contains(local._org_only_roles, k)
  }
  # additive bindings, used for roles co-managed by different stages
  iam_bindings_additive = merge(
    local.folder_iam_bindings_additive,
    var.iam_bindings_additive
  )
  factories_config = {
    custom_roles = var.factories_config.custom_roles
    org_policies = (
      var.factories_config.org_policy
    )
    org_policy_custom_constraints = "./data/custom-constraint-policies/"
  }
  org_policies = local.folder_org_policies
}
