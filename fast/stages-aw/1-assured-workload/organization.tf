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
# tfdoc:file:description Organization-level IAM.

locals {
  # reassemble logical bindings into the formats expected by the module
  _iam_bindings = merge(
    local.iam_sa_bindings,
    local.iam_user_bootstrap_bindings
  )
  _iam_bindings_add = flatten([
    for member, data in local._iam_bindings : [
      for role in data.additive : {
        member = member
        role   = role
      }
    ]
  ])
  _iam_bindings_additive = {
    for b in local._iam_bindings_add : "${b.role}-${b.member}" => {
      member = b.member
      role   = b.role
    }
  }
  _org_only_roles = [
    "roles/billing.admin",
    "roles/billing.creator",
    "roles/billing.user",
    "roles/orgpolicy.policyAdmin",
    "roles/iam.organizationRoleAdmin",
    "roles/cloudsupport.admin",
    "roles/assuredworkloads.admin",
    "roles/compute.osLoginExternalUser",
    "roles/resourcemanager.organizationAdmin",
    "roles/billing.viewer",
    "roles/iam.organizationRoleViewer",
    "roles/logging.admin"
  ]
  consumer_folder_id = try(one([
    for r in google_assured_workloads_workload.primary[0].resources : r.resource_id if r.resource_type == "CONSUMER_FOLDER"
  ]), null)

  custom_role_ids = [
    "gcveNetworkAdmin",
    "organizationAdminViewer",
    "organizationIamAdmin",
    "serviceProjectNetworkAdmin",
    "storageViewer",
    "tagEditor",
    "tagViewer",
    "tenantNetworkAdmin"
  ]

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
  compliance_api_baseline = yamldecode(file("${path.module}/data/allowed_apis.yaml")).allowed_apis
}

data "google_iam_role" "custom_iam_roles" {
  for_each = toset(local.custom_role_ids)
  name     = "organizations/${var.organization.id}/roles/${each.key}"
}

# TODO: add a check block to ensure our custom roles exist in the factory files

resource "google_assured_workloads_workload" "primary" {
  count                        = var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED" ? 1 : 0
  compliance_regime            = var.assured_workloads.regime
  display_name                 = "${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-${var.prefix}"
  location                     = lower(var.assured_workloads.location)
  organization                 = var.organization.id
  billing_account              = var.billing_account.id != null ? "billingAccounts/${var.billing_account.id}" : null
  provisioned_resources_parent = "folders/${var.top_level_folder.id}"
  resource_settings {
    display_name  = "${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-${var.prefix}"
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
  name   = "${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-${var.prefix}"
}

module "tenants-container-folders" {
  source = "../../../modules/folder"
  parent = "folders/${local.consumer_folder_id}"
  name   = "Tenants"
}

module "branch-common-services-folder" {
  source = "../../../modules/folder"
  parent = var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED" ? "folders/${local.consumer_folder_id}" : module.no-compliance-folder[0].folder.id
  name   = "${lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime)} NetSec Services"
}

module "shared-services-subfolder" {
  source = "../../../modules/folder"
  parent = module.branch-common-services-folder.folder.id
  name   = "Shared Services"
}

module "netsec-shared-project" {
  source          = "../../../modules/project"
  name            = "${var.prefix}-shared-svc"
  parent          = module.shared-services-subfolder.id
  billing_account = var.billing_account.id

  iam = {
    "roles/serviceusage.serviceUsageAdmin" = [
      module.automation-tf-resman-sa.iam_email,
      module.automation-tf-bootstrap-sa.iam_email
    ]
    "roles/owner" = [
      module.automation-tf-resman-sa.iam_email
    ]
  }

  services = [
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "servicenetworking.googleapis.com",
    "networkconnectivity.googleapis.com"
  ]

  org_policies = {
    "compute.trustedImageProjects" = {
      inherit_from_parent = true
      rules = [
        {
          allow = {
            values = ["projects/cis-public"]
          }
        }
      ]
    }
  }
}

resource "google_folder_organization_policy" "il5_folder_compliance_enforcement" {
  folder     = local.consumer_folder_id
  constraint = "constraints/gcp.restrictServiceUsage"

  list_policy {
    allow {
      values = local.compliance_api_baseline
    }
  }
}

# Common Services folder with logging sink
module "common-services-folder-logging" {
  count  = length(local.all_log_buckets) > 0 ? 1 : 0
  source = "../../../modules/folder"

  # Use existing common services folder
  folder_create = false
  id            = module.branch-common-services-folder.folder.id

  logging_sinks = {
    for loc in local.locations.logging :
    "${var.prefix}-common-services-logs-${loc}" => {
      bq_partitioned_table = false
      destination          = module.aw-log-buckets["${var.prefix}-common-services-logs-${loc}"].id
      filter = join(" OR ", [
        # The common services folder itself
        "(resource.type=\"folder\" AND resource.labels.folder_id=\"${replace(module.branch-common-services-folder.folder.id, "folders/", "")}\")",

        # All projects under this folder (by parent relationship)
        "(resource.type=\"project\" AND resource.labels.parent_id=\"${replace(module.branch-common-services-folder.folder.id, "folders/", "")}\")",

        # All resources within the common services folder hierarchy
        "(protoPayload.resourceName:\"${module.branch-common-services-folder.folder.id}\" OR protoPayload.resourceName:\"${module.branch-common-services-folder.folder.id}/*\")"
      ])
      type = "logging"
    }
  }

  depends_on = [
    module.branch-common-services-folder,
    module.aw-log-buckets
  ]
}

module "organization" {
  source          = "../../../modules/organization-se"
  organization_id = "organizations/${var.organization.id}"
  prefix          = var.prefix
  # additive bindings, used for roles co-managed by different stages
  iam_bindings_additive = merge(
    local.org_iam_bindings_additive,
    {
      organization_iam_admin_conditional = {
        member = module.automation-tf-resman-sa.iam_email
        role   = "organizations/${var.organization.id}/roles/organizationIamAdmin"
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
            "organizations/${var.organization.id}/roles/tenantNetworkAdmin"]))
          )
          title       = "automation_sa_delegated_grants"
          description = "Automation service account delegated grants."
        }
      }
    },
    local.billing_mode != "org" ? {} : {
      organization_billing_conditional = {
        member = module.automation-tf-resman-sa.iam_email
        role   = "organizations/${var.organization.id}/roles/organizationIamAdmin"
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
  logging_sinks = merge({
    for name, attrs in var.log_sinks :
    name => {
      for loc in local.locations.logging :
      "${name}-${loc}" => {
        bq_partitioned_table = attrs.type == "bigquery"
        destination          = local.log_sink_destinations_all["${name}-${loc}"].id
        filter               = attrs.filter
        type                 = attrs.type
      }
    }
    } == {} ? {} : merge([
      for name, attrs in var.log_sinks : {
        for loc in local.locations.logging :
        "${name}-${loc}" => {
          bq_partitioned_table = attrs.type == "bigquery"
          destination          = local.log_sink_destinations_all["${name}-${loc}"].id
          filter               = attrs.filter
          type                 = attrs.type
        }
      }
    ]...),
    var.apply_tier_1_pubsub_sink ? {
      "tier-1-audit-logs-sink" = {
        bq_partitioned_table = false
        destination          = module.pubsub-topics.tier-1.id
        description          = "Tier 1 landing zone Audit logs logging sink for C5ISR logging."
        filter               = local.tier_1_audit_filter
        exclusions           = local.tenant_exclusions_map
        include_children     = true
        type                 = "pubsub"
      }
    } : {}
  )
}

module "top-level-folder" {
  source        = "../../../modules/folder"
  folder_create = false
  id            = "folders/${var.top_level_folder.id}"
  parent        = "organizations/${var.organization.id}"
  # additive bindings, used for roles co-managed by different stages
  iam_bindings_additive = merge(
    local.folder_iam_bindings_additive,
  )
}

module "assured-workload-folder-log-sink" {
  source        = "../../../modules/folder"
  folder_create = false
  id            = "folders/${local.consumer_folder_id}"
  logging_sinks = {
    "tier-1-vpc-flow-logs-sink" = {
      bq_partitioned_table = false
      destination          = module.pubsub-topics.tier-1.id
      description          = "Tier 1 landing zone VPC Flow logs logging sink for C5ISR logging."
      filter               = local.tier_1_vpc_filter
      exclusions           = local.tenant_exclusions_map
      include_children     = true
      type                 = "pubsub"
    }
    "tier-2-pubsub-logs-sink" = {
      bq_partitioned_table = false
      destination          = module.pubsub-topics.tier-2.id
      description          = "Tier 2 landing zone logging sink for C5ISR logging."
      filter               = local.tier_2_filter
      exclusions           = local.tenant_exclusions_map
      include_children     = true
      type                 = "pubsub"
    },
    "tier-3-pubsub-logs-sink" = {
      bq_partitioned_table = false
      destination          = module.pubsub-topics.tier-3.id
      description          = "Tier 3 landing zone logging sink for C5ISR logging."
      filter               = local.tier_3_filter
      exclusions           = local.tenant_exclusions_map
      include_children     = true
      type                 = "pubsub"
    }
  }
}