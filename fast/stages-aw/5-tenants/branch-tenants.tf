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

# /**
#  * Copyright 2024 Google LLC
#  *
#  * Licensed under the Apache License, Version 2.0 (the "License");
#  * you may not use this file except in compliance with the License.
#  * You may obtain a copy of the License at
#  *
#  *      http://www.apache.org/licenses/LICENSE-2.0
#  *
#  * Unless required by applicable law or agreed to in writing, software
#  * distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.
#  */

# # tfdoc:file:description Lightweight tenant resources.

# # TODO(ludo): add support for CI/CD

locals {

  tenant_env_list = [
    for ten_env in var.tenant.tenant_specific_envs : {
      key         = "${var.tenant.name}-${ten_env}"
      tenant      = var.tenant.name
      tenant_info = var.tenant
      parent_id   = var.tenants_folder_id
      env         = ten_env
    }
  ]

  tenant_envs = {
    for item in local.tenant_env_list : item.key => item
  }

  tenant_iam = {
    for k, v in local.tenant_envs : k => [
      v.tenant_info.admin_principal,
      module.tenant-self-iac-sa[k].iam_email
    ]
  }

  tenant_iam_members = flatten([
    for k, v in local.tenant_iam : v
  ])

  tenant_projects = {
    for env_key, env_data in local.tenant_envs : env_key => {
      tenant_key   = env_key
      display_name = "${local.project_map["tenant-projects"]}-${substr(env_data.env, 0, 1)}"
      tenant_info  = env_data.tenant_info
    }
  }

  flat_tenant_groups = flatten([
    for name, data in var.tenant.tenant_groups : [
      for role in data.roles : {
        role      = startswith(role, "roles/") ? role : "roles/${role}"
        principal = strcontains(name, "@") ? "group:${name}" : "group:${name}@${var.organization.domain}"
      }
    ]
  ])

  tenant_role_map = {
    for obj in local.flat_tenant_groups : obj.role => obj.principal...
  }
}

# Tenant folders (top, core, self)
module "tenant-top-folders" {
  source = "../../../modules/folder"
  parent = var.tenants_folder_id
  name   = local.project_map["tenant-projects"]
  iam_by_principals = {
    (var.tenant.admin_principal) = ["roles/browser"]
  }
  logging_sinks = {
    for sink, sink_config in local.tenant_log_sinks : sink => {
      bq_partitioned_table = sink_config.bq_partitioned_table
      destination          = sink_config.destination
      description          = "Tier 1 ${var.tenant.name} logging sink for C5ISR logging."
      filter               = sink_config.filter
      include_children     = sink_config.include_children
      type                 = sink_config.type
    }
  }
}

# Tenant Projects (Target: D, T, P, and IaC Core)
module "tenant-projects" {
  source   = "../../../modules/project"
  for_each = local.tenant_projects
  # Name matches: "Fake Tenant X Proj D"
  name   = lower(each.value.display_name)
  parent = module.tenant-top-folders.id

  iam_by_principals_additive = {
    (var.tenant.admin_principal) = [
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountTokenCreator",
      "roles/iam.workloadIdentityPoolAdmin"
    ]
    "serviceAccount:${var.automation.service_accounts.resman-r}" = [
      "organizations/${var.organization.id}/roles/storageViewer",
      "roles/viewer"
    ]
  }
  compute_metadata = {
    google-compute-default-region = local.primary_location_gcs
    google-compute-default-zone   = "${local.primary_location_gcs}-b" # There always seems to be a -b zone
  }
  services = [
    "accesscontextmanager.googleapis.com",
    "bigquery.googleapis.com",
    "bigqueryreservation.googleapis.com",
    "bigquerystorage.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudbilling.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "container.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "essentialcontacts.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "orgpolicy.googleapis.com",
    "pubsub.googleapis.com",
    "servicenetworking.googleapis.com",
    "serviceusage.googleapis.com",
    "stackdriver.googleapis.com",
    "storage-component.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com"
  ]
}

module "network-project" {
  source = "../../../modules/project"
  count  = var.tenant.deploy_network_project != null && var.tenant.deploy_network_project ? 1 : 0
  name   = "${var.tenant.macom}-${var.tenant.name}-prod-networking"
  parent = module.tenant-top-folders.id

  iam_by_principals_additive = {
    (var.tenant.admin_principal) = [
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountTokenCreator",
      "roles/iam.workloadIdentityPoolAdmin"
    ]
    "serviceAccount:${var.automation.service_accounts.resman-r}" = [
      "organizations/${var.organization.id}/roles/storageViewer",
      "roles/viewer"
    ]
  }
  compute_metadata = {
    google-compute-default-region = local.primary_location_gcs
    google-compute-default-zone   = "${local.primary_location_gcs}-b"
  }
  services = [
    "accesscontextmanager.googleapis.com",
    "bigquery.googleapis.com",
    "bigqueryreservation.googleapis.com",
    "bigquerystorage.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudbilling.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "container.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "essentialcontacts.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "orgpolicy.googleapis.com",
    "pubsub.googleapis.com",
    "servicenetworking.googleapis.com",
    "serviceusage.googleapis.com",
    "stackdriver.googleapis.com",
    "storage-component.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com"
  ]
}

resource "google_project_organization_policy" "trusted_image_projects" {
  for_each   = local.tenant_projects
  project    = module.tenant-projects[each.key].project_id
  constraint = "compute.trustedImageProjects"

  list_policy {
    inherit_from_parent = true
    allow {
      values = ["projects/cis-public"]
    }
  }
}

# Automation Service Accounts (One per Tenant-Env)
module "tenant-sa" {
  source      = "../../../modules/iam-service-account"
  for_each    = local.tenant_projects
  project_id  = module.tenant-projects[each.key].project_id
  name        = lower("tn-${each.value.display_name}-sa")
  description = "Terraform service account for tenant ${each.value.display_name}"
  prefix      = null
}

module "tenant-top-folders-iam" {
  source        = "../../../modules/folder"
  id            = module.tenant-top-folders.id
  folder_create = false
  tag_bindings  = null
  iam = merge(
    {
      "roles/cloudasset.owner"               = [module.tenant-core-sa.iam_email]
      "roles/compute.xpnAdmin"               = [module.tenant-core-sa.iam_email]
      "roles/logging.admin"                  = [module.tenant-core-sa.iam_email]
      "roles/resourcemanager.folderAdmin"    = [module.tenant-core-sa.iam_email]
      "roles/resourcemanager.projectCreator" = [module.tenant-core-sa.iam_email]
      "roles/resourcemanager.tagUser"        = [module.tenant-core-sa.iam_email]
    },
    {
      for k in var.tenant_config.top_folder_roles :
      k => local.tenant_iam_members
    },
    local.tenant_role_map
  )
}

module "tenant-core-folders-iam" {
  source        = "../../../modules/folder"
  id            = module.tenant-top-folders.id
  folder_create = false
  iam = merge(
    {
      "roles/owner" = [
        module.tenant-core-sa.iam_email
      ]
      "roles/viewer" = local.tenant_iam_members
    },
    {
      for k in var.tenant_config.core_folder_roles :
      k => local.tenant_iam_members
    }
  )
}

module "tenant-self-folders-iam" {
  source        = "../../../modules/folder"
  id            = module.tenant-top-folders.id
  folder_create = false
  iam = merge(
    {
      "roles/cloudasset.owner"               = [module.tenant-core-sa.iam_email]
      "roles/compute.xpnAdmin"               = [module.tenant-core-sa.iam_email]
      "roles/resourcemanager.folderAdmin"    = [module.tenant-core-sa.iam_email]
      "roles/resourcemanager.projectCreator" = [module.tenant-core-sa.iam_email]
      "roles/resourcemanager.tagUser"        = [module.tenant-core-sa.iam_email]
      "roles/owner"                          = [module.tenant-core-sa.iam_email]
    },
    {
      for k in var.tenant_config.tenant_folder_roles :
      k => local.tenant_iam_members
    }
  )
}

# Deny folicy for crypokeys on each project
resource "google_iam_deny_policy" "tenant_folder_kms_lockdown" {
  provider = google-beta

  parent = urlencode("cloudresourcemanager.googleapis.com/${module.tenant-top-folders.id}")

  name         = "lockdown-kms-administration"
  display_name = "Prevent Tenant Modification of KMS"

  rules {
    deny_rule {
      # Block everyone...
      denied_principals = ["principalSet://goog/public:all"]

      # When we need to create an exception add them here (maybe make this part of tenants.yml)
      exception_principals = [
        "principal://iam.googleapis.com/projects/-/serviceAccounts/${var.automation.service_accounts.tenant}"
      ]

      # From doing these specific KMS actions
      denied_permissions = [
        "cloudkms.googleapis.com/cryptoKeys.setIamPolicy",
        "cloudkms.googleapis.com/keyRings.setIamPolicy",
        "cloudkms.googleapis.com/cryptoKeyVersions.destroy",
        "cloudkms.googleapis.com/cryptoKeys.update"
      ]
    }
  }
}

# Tenant IaC resources (core)

module "tenant-core-sa" {
  source = "../../../modules/iam-service-account"
  # for_each    = local.tenant_envs
  project_id  = var.automation.project_id
  name        = lower("tn-${var.tenant.name}-prod-0")
  description = "Terraform service account for tenant ${var.tenant.name}."
  prefix      = var.prefix
  iam_project_roles = {
    (var.automation.project_id) = ["roles/serviceusage.serviceUsageConsumer"]
  }
}

# module "tenant-core-gcs" {
#   source     = "../../../modules/gcs"
#   project_id = var.automation.project_id
#   name       = lower("tn-${var.tenant.name}")
#   prefix     = null
#   versioning = true
#   location   = local.primary_location_gcs
#   storage_class = (
#     length(split("-", local.primary_location_gcs)) < 2
#     ? "MULTI_REGIONAL"
#     : "REGIONAL"
#   )
#   # encryption_key = module.tenant-project-keys["${var.tenant.name}-${local.primary_location_kms}"].key_ids["gcs"]
#   depends_on     = [module.tenant-project-keys, google_kms_crypto_key_iam_member.tenant_kms]
#   iam = {
#     "roles/storage.objectAdmin" = [module.tenant-core-sa.iam_email]
#   }
# }

module "tenant-self-iac-gcs-outputs" {
  source     = "../../../modules/gcs"
  for_each   = local.tenant_projects
  project_id = module.tenant-projects[each.key].project_id
  location   = local.primary_location_gcs
  storage_class = (
    length(split("-", local.primary_location_gcs)) < 2
    ? "MULTI_REGIONAL"
    : "REGIONAL"
  )
  name       = lower("${each.value.display_name}-iac-outputs")
  prefix     = var.prefix
  versioning = true
  iam = {
    "roles/storage.objectAdmin" = [module.tenant-core-sa.iam_email]
  }
  encryption_key = module.tenant-project-keys["${each.value.tenant_key}-${local.primary_location_kms}"].key_ids["gcs"]
  depends_on     = [module.tenant-project-keys, google_kms_crypto_key_iam_member.tenant_kms]

}

module "tenant-self-iac-gcs-states" {
  source     = "../../../modules/gcs"
  for_each   = local.tenant_projects
  project_id = module.tenant-projects[each.key].project_id
  location   = local.primary_location_gcs
  storage_class = (
    length(split("-", local.primary_location_gcs)) < 2
    ? "MULTI_REGIONAL"
    : "REGIONAL"
  )
  name           = lower("${each.value.display_name}-iac")
  prefix         = var.prefix
  versioning     = true
  encryption_key = module.tenant-project-keys["${each.key}-${local.primary_location_kms}"].key_ids["gcs"]
  depends_on     = [module.tenant-project-keys, google_kms_crypto_key_iam_member.tenant_kms]

  iam = {
    "roles/storage.objectAdmin" = [
      module.tenant-core-sa.iam_email,
      module.tenant-sa[each.key].iam_email
    ]
  }
}

module "tenant-self-iac-sa" {
  source      = "../../../modules/iam-service-account"
  for_each    = local.tenant_projects
  project_id  = module.tenant-projects[each.key].project_id
  name        = lower("${each.value.display_name}-iac")
  description = "Terraform automation service account."
  prefix      = null
  iam = {
    "roles/iam.serviceAccountTokenCreator" = compact([
      try(module.automation-tf-cicd-sa[each.key].iam_email, null)
    ])
  }
  iam_project_roles = {
    (module.tenant-projects[each.key].project_id) = [
      "roles/cloudkms.admin",
      "roles/iam.serviceAccountCreator",
      "roles/iam.serviceAccountUser",
      "roles/serviceusage.serviceUsageConsumer",
      "roles/browser",
      "roles/owner",
      "roles/cloudbuild.builds.editor",
      "roles/cloudbuild.builds.viewer",
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountViewer",
      "roles/iam.workloadIdentityPoolAdmin",
      "roles/iam.workloadIdentityPoolViewer",
      "roles/source.admin",
      "roles/source.reader",
      "roles/storage.admin",
      "roles/viewer"
    ]
  }
  iam_storage_roles = {
    (module.tenant-self-iac-gcs-outputs[each.value.tenant_key].name) = [
      "roles/storage.admin"
    ]
    (module.tenant-self-iac-gcs-states[each.value.tenant_key].name) = [
      "roles/storage.admin"
    ]
  }
}
