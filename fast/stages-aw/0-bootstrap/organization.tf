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
    local.iam_sa_bindings,
    local.iam_user_bootstrap_bindings,
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
  # compute authoritative and additive roles for use by add-ons (checklist, etc.)
  iam_roles_authoritative = distinct(concat(
    flatten(values(local._iam_principals)),
    keys(local._iam)
  ))

  # Some of the org policies require templating to construct, they have been moved to data/custom-org-policies
  # load org policy yaml files from a subdirectory
  _org_policies_raw = merge(concat(
    [
      for f in try(fileset("./data/org-policies/", "*_policy.yaml"), []) :
      yamldecode(file("./data/org-policies/${f}"))
    ],
    [
      for f in try(fileset("./data/custom-org-policies/", "*_policy.yaml"), []) :
      yamldecode(templatefile("./data/custom-org-policies/${f}", {
        # NOTE:
        # If there are more variables need to be substituted, put them
        # into a separate yaml file or map, use the following line to
        # loop throught them. For list values use yamlencode() function.
        # for k, v in local.common_settings : k => v
        organization_id : var.organization.id
        domain_name : var.organization.domain
        customer_id : var.organization.customer_id
        drs_tag_name : local.drs_tag_name
        allowed_domains : var.org_policies_config.constraints.allowed_policy_member_domains
      }))
    ]
  )...)
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
}

# TODO: add a check block to ensure our custom roles exist in the factory files

# import org policy constraints enabled by default in new orgs since February 2024
import {
  for_each = (
    var.org_policies_config.import_defaults && var.bootstrap_user == null
    ? toset([
      # source: https://cloud.google.com/resource-manager/docs/secure-by-default-organizations#organization_policies_enforced_on_organization_resources
      # listed in the order as on page
      "iam.managed.disableServiceAccountKeyCreation",
      "iam.managed.disableServiceAccountKeyUpload",
      "iam.managed.preventPrivilegedBasicRolesForDefaultServiceAccounts",
      # "iam.automaticIamGrantsForDefaultServiceAccounts",
      "iam.allowedPolicyMemberDomains",
      "essentialcontacts.managed.allowedContactDomains",
      "storage.uniformBucketLevelAccess",
      # "compute.setNewProjectDefaultToZonalDNSOnly",
      "compute.managed.restrictProtocolForwardingCreationForTypes", # not confirmed that this is live, but listed on webpage
    ]) : toset([])
  )
  id = "organizations/${var.organization.id}/policies/${each.key}"
  to = module.organization.google_org_policy_policy.default[each.key]
}

module "organization-logging" {
  # Preconfigure organization-wide logging settings to ensure project
  # log buckets (_Default, _Required) are created in the location
  # specified by local.locations.logging. This separate
  # organization-block prevents circular dependencies with later
  # project creation.
  source          = "../../../modules/organization"
  organization_id = "organizations/${var.organization.id}"
  logging_settings = {
    storage_location = local.locations.logging
  }
}

resource "google_assured_workloads_workload" "primary" {
  count                        = var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED" ? 1 : 0
  compliance_regime            = var.assured_workloads.regime
  display_name                 = "StellarEngine-${var.prefix}"
  location                     = var.assured_workloads.location
  organization                 = var.organization.id
  billing_account              = var.billing_account.id != null && var.billing_account.id != "" ? "billingAccounts/${var.billing_account.id}" : null
  provisioned_resources_parent = ""
  resource_settings {
    display_name  = "StellarEngine-${var.prefix}"
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
  name   = "StellarEngine-${var.prefix}"
}

module "branch-common-services-folder" {
  source = "../../../modules/folder"
  parent = var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED" ? "folders/${google_assured_workloads_workload.primary[0].resources[0].resource_id}" : "${module.no-compliance-folder[0].folder.id}"
  name   = "${lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime)} Common Services"
}


module "organization" {
  source          = "../../../modules/organization-se"
  organization_id = module.organization-logging.id
  prefix          = var.prefix
  iam_by_principals = {
    for k in distinct(concat(keys(local.iam_principals), keys(var.iam_by_principals))) :
    k => distinct(concat(
      try(local.iam_principals[k], []),
      try(var.iam_by_principals[k], [])
    ))
  }
  # machine (service accounts) IAM bindings
  iam = merge(
    {
      for k, v in local.iam : k => distinct(concat(v, lookup(var.iam, k, [])))
    },
    {
      for k, v in var.iam : k => v if lookup(local.iam, k, null) == null
    }
  )
  # additive bindings, used for roles co-managed by different stages
  iam_bindings_additive = merge(
    local.iam_bindings_additive,
    var.iam_bindings_additive
  )
  # delegated role grant for resource manager service account
  iam_bindings = merge(
    {
      organization_iam_admin_conditional = {
        members = [module.automation-tf-resman-sa.iam_email]
        role    = module.organization.custom_role_id["organization_iam_admin"]
        condition = {
          expression = format(
            "api.getAttribute('iam.googleapis.com/modifiedGrantsByRole', []).hasOnly([%s])",
            join(",", formatlist("'%s'", [
              "roles/accesscontextmanager.policyAdmin",
              "roles/cloudasset.viewer",
              "roles/compute.orgFirewallPolicyAdmin",
              "roles/compute.xpnAdmin",
              "roles/orgpolicy.policyAdmin",
              "roles/orgpolicy.policyViewer",
              "roles/resourcemanager.organizationViewer",
              module.organization.custom_role_id["tenant_network_admin"]
            ]))
          )
          title       = "automation_sa_delegated_grants"
          description = "Automation service account delegated grants."
        }
      }
    },
    local.billing_mode != "org" ? {} : {
      organization_billing_conditional = {
        members = [module.automation-tf-resman-sa.iam_email]
        role    = module.organization.custom_role_id["organization_iam_admin"]
        condition = {
          expression = format(
            "api.getAttribute('iam.googleapis.com/modifiedGrantsByRole', []).hasOnly([%s])",
            join(",", formatlist("'%s'", [
              "roles/billing.admin",
              "roles/billing.costsManager",
              "roles/billing.user",
            ]))
          )
          title       = "automation_sa_delegated_grants"
          description = "Automation service account delegated grants."
        }
      }
    }
  )
  custom_roles = var.custom_roles
  factories_config = {
    custom_roles = var.factories_config.custom_roles
    org_policies = (
      var.bootstrap_user != null ? null : var.factories_config.org_policy
    )
    org_policy_custom_constraints = "./data/custom-constraint-policies/"
    context = {
      org_policies = {
        root_node = var.organization.id
      }
    }
  }
  logging_sinks = {
    for name, attrs in var.log_sinks : name => {
      bq_partitioned_table = attrs.type == "bigquery"
      destination          = local.log_sink_destinations[name].id
      filter               = attrs.filter
      type                 = attrs.type
    }
  }
  org_policies = var.bootstrap_user != null ? null : local.org_policies

}
