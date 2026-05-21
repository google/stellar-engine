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


locals {
  tenant_iam = {
    for k, v in local.tenant_envs : k => [
      v.tenant_info.admin_principal,
      module.tenant-self-iac-sa[k].iam_email
    ]
  }
  gcs_locations = { for k, v in var.tenants : k => try(v.locations.gcs != "", false) ? v.locations.gcs : var.regions.primary }
  tenant_envs = merge([for e, _ in var.envs_folders : {
    for t, v in var.tenants : "${e}-${t}" => {
      env         = e
      tenant      = t
      tenant_info = v
    }
    }
  ]...)
}

# Tenant folders (top, core, self)
module "tenant-top-folders" {
  source   = "../../../modules/folder"
  for_each = local.tenant_envs
  parent   = module.branch-envs-folders[each.value.env].id
  name     = "Project ${each.value.tenant} ${each.value.env}"
  iam_by_principals = {
    (each.value.tenant_info.admin_principal) = ["roles/browser"]
  }
}

module "tenant-top-folders-iam" {
  source        = "../../../modules/folder"
  for_each      = local.tenant_envs
  id            = module.tenant-top-folders[each.key].id
  folder_create = false
  tag_bindings  = null
  iam = merge(
    {
      "roles/cloudasset.owner"               = [module.tenant-core-sa[each.key].iam_email]
      "roles/compute.xpnAdmin"               = [module.tenant-core-sa[each.key].iam_email]
      "roles/logging.admin"                  = [module.tenant-core-sa[each.key].iam_email]
      "roles/resourcemanager.folderAdmin"    = [module.tenant-core-sa[each.key].iam_email]
      "roles/resourcemanager.projectCreator" = [module.tenant-core-sa[each.key].iam_email]
      "roles/resourcemanager.tagUser"        = [module.tenant-core-sa[each.key].iam_email]
    },
    {
      for k in var.tenants_config.top_folder_roles :
      k => local.tenant_iam[each.value.tenant.name]
    }
  )
}

module "tenant-core-folders-iam" {
  source        = "../../../modules/folder"
  for_each      = local.tenant_envs
  id            = module.tenant-top-folders[each.key].id
  folder_create = false
  iam = merge(
    {
      "roles/owner" = [
        module.tenant-core-sa[each.key].iam_email
      ]
      "roles/viewer" = local.tenant_iam[each.key]
    },
    {
      for k in var.tenants_config.core_folder_roles :
      k => local.tenant_iam[each.key]
    }
  )
}

module "tenant-self-folders-iam" {
  source        = "../../../modules/folder"
  for_each      = local.tenant_envs
  id            = module.tenant-top-folders[each.key].id
  folder_create = false
  iam = merge(
    {
      "roles/cloudasset.owner"               = [module.tenant-core-sa[each.key].iam_email]
      "roles/compute.xpnAdmin"               = [module.tenant-core-sa[each.key].iam_email]
      "roles/resourcemanager.folderAdmin"    = [module.tenant-core-sa[each.key].iam_email]
      "roles/resourcemanager.projectCreator" = [module.tenant-core-sa[each.key].iam_email]
      "roles/resourcemanager.tagUser"        = [module.tenant-core-sa[each.key].iam_email]
      "roles/owner"                          = [module.tenant-core-sa[each.key].iam_email]
    },
    {
      for k in var.tenants_config.tenant_folder_roles :
      k => local.tenant_iam[each.key]
    }
  )
}

# Tenant IaC resources (core)

module "tenant-core-sa" {
  source      = "../../../modules/iam-service-account"
  for_each    = local.tenant_envs
  project_id  = var.automation.project_id
  name        = lower("tn-${each.key}-prod-0")
  description = "Terraform service account for tenant ${each.key}."
  prefix      = var.prefix
  iam_project_roles = {
    (var.automation.project_id) = ["roles/serviceusage.serviceUsageConsumer"]
  }
}

module "tenant-core-gcs" {
  source        = "../../../modules/gcs"
  for_each      = local.tenant_envs
  project_id    = var.automation.project_id
  name          = lower("tn-${each.key}-0")
  prefix        = var.prefix
  versioning    = true
  force_destroy = true
  location      = local.gcs_locations[each.value.tenant]
  storage_class = (
    length(split("-", local.gcs_locations[each.value.tenant])) < 2
    ? "MULTI_REGIONAL"
    : "REGIONAL"
  )
  encryption_key = module.tenant-project-keys[each.key].key_ids["gcs"]
  depends_on     = [module.tenant-project-keys, google_kms_crypto_key_iam_member.tenant_kms]
  iam = {
    "roles/storage.objectAdmin" = [module.tenant-core-sa[each.key].iam_email]
  }
}

# Tenant IaC project and resources (self)
module "tenant-self-iac-projects" {
  source   = "../../../modules/project"
  for_each = local.tenant_envs
  providers = {
    google      = google.billing
    google-beta = google-beta.billing
  }
  billing_account = (
    each.value.tenant_info.billing_account != null
    ? each.value.tenant_info.billing_account
    : var.billing_account.id
  )
  name   = lower("${each.key}-iac-core-0")
  parent = module.tenant-top-folders[each.key].id
  prefix = var.prefix
  iam_by_principals = {
    (each.value.tenant_info.admin_principal) = [
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountTokenCreator",
      "roles/iam.workloadIdentityPoolAdmin"
    ]
  }
  iam = {
    # Expected that the service account will have owner permissions on the project it
    # creates this role will be removed during stage 3 when sa-lockdown-runs.
    # This iam simply reaffirms the permissions resman should already have.
    "roles/owner" = [
      "serviceAccount:${var.automation.service_accounts.resman}"
    ]
    (var.custom_roles.storage_viewer) = [
      "serviceAccount:${var.automation.service_accounts.resman-r}"
    ]
    "roles/viewer" = [
      "serviceAccount:${var.automation.service_accounts.resman-r}"
    ]
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

module "tenant-self-iac-gcs-outputs" {
  source     = "../../../modules/gcs"
  for_each   = local.tenant_envs
  project_id = module.tenant-self-iac-projects[each.key].project_id
  location   = local.gcs_locations[each.value.tenant]
  storage_class = (
    length(split("-", local.gcs_locations[each.value.tenant])) < 2
    ? "MULTI_REGIONAL"
    : "REGIONAL"
  )
  name          = "${each.key}-iac-outputs-0"
  prefix        = var.prefix
  versioning    = true
  force_destroy = true
  iam = {
    "roles/storage.objectAdmin" = [module.tenant-core-sa[each.key].iam_email]
  }
  encryption_key = module.tenant-project-keys[each.key].key_ids["gcs"]
  depends_on     = [module.tenant-project-keys, google_kms_crypto_key_iam_member.tenant_kms]

}

module "tenant-self-iac-gcs-states" {
  source     = "../../../modules/gcs"
  for_each   = local.tenant_envs
  project_id = module.tenant-self-iac-projects[each.key].project_id
  location   = local.gcs_locations[each.value.tenant]
  storage_class = (
    length(split("-", local.gcs_locations[each.value.tenant])) < 2
    ? "MULTI_REGIONAL"
    : "REGIONAL"
  )
  name           = "${each.key}-iac-0"
  prefix         = var.prefix
  versioning     = true
  force_destroy  = true
  encryption_key = module.tenant-project-keys[each.key].key_ids["gcs"]
  depends_on     = [module.tenant-project-keys, google_kms_crypto_key_iam_member.tenant_kms]
}

module "tenant-self-iac-sa" {
  source      = "../../../modules/iam-service-account"
  for_each    = local.tenant_envs
  project_id  = module.tenant-self-iac-projects[each.key].project_id
  name        = lower("${each.key}-iac-0")
  description = "Terraform automation service account."
  prefix      = var.prefix
  iam_storage_roles = {
    (module.tenant-self-iac-gcs-outputs[each.key].name) = [
      "roles/storage.admin"
    ]
    (module.tenant-self-iac-gcs-states[each.key].name) = [
      "roles/storage.admin"
    ]
  }
}

# Tenant main project and resources (self)
module "tenant-self-main-projects" {
  source   = "../../../modules/project"
  for_each = local.tenant_envs
  providers = {
    google      = google.billing
    google-beta = google-beta.billing
  }
  billing_account = (
    each.value.tenant_info.billing_account != null
    ? each.value.tenant_info.billing_account
    : var.billing_account.id
  )
  name   = lower("${each.key}-main-0")
  parent = module.tenant-top-folders[each.key].id
  prefix = var.prefix
  iam_by_principals = {
    (each.value.tenant_info.admin_principal) = [
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountTokenCreator",
      "roles/iam.workloadIdentityPoolAdmin"
    ]
  }
  iam = {
    # Expected that the service account will have owner permissions on the project it
    # creates this role will be removed during stage 3 when sa-lockdown-runs.
    # This iam simply reaffirms the permissions resman should already have.
    "roles/owner" = [
      "serviceAccount:${var.automation.service_accounts.resman}"
    ]
    (var.custom_roles.storage_viewer) = [
      "serviceAccount:${var.automation.service_accounts.resman-r}"
    ]
    "roles/viewer" = [
      "serviceAccount:${var.automation.service_accounts.resman-r}"
    ]
  }
  compute_metadata = {
    google-compute-default-region = var.regions.primary
    google-compute-default-zone   = "${var.regions.primary}-b" # There always seems to be a -b zone
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

#added for key and bucket provisioning
resource "time_sleep" "tenant_project_iam_propagation_delay" {
  create_duration = "30s"

  depends_on = [
    module.tenant-self-iac-projects,
    module.tenant-self-main-projects
  ]
}

