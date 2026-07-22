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
# tfdoc:file:description Automation project and resources.

locals {
  cicd_resman_sa   = try(module.automation-tf-cicd-sa["resman"].iam_email, "")
  cicd_resman_r_sa = try(module.automation-tf-cicd-r-sa["resman"].iam_email, "")
  config_env_file  = "${path.module}/../../../automation/config.env"

  config_env_vars = {
    for l in split("\n", fileexists(local.config_env_file) ? file(local.config_env_file) : "") :
    split("=", l)[0] => split("=", l)[1] if length(split("=", l)) == 2
  }

  tenant_envs = split(",", lookup(local.config_env_vars, "TENANT_ENVIRONMENTS", ""))

  config_env_bucket = length(module.automation-tf-config-gcs) > 0 ? {
    "config_env_object" = {
      bucket_name = module.automation-tf-config-gcs[0].name
      object_name = "config.env"
      source_path = local.config_env_file
    }
  } : {}

  allowed_api_data = yamldecode(file("${path.module}/data/allowed_apis.yaml"))
  lz_data   = yamldecode(file("${path.module}/data/compliance_exceptions.yaml"))
  compliance_list = local.allowed_api_data.allowed_apis
  coa2_list = local.lz_data.COA2

  billing_admins = [
    "serviceAccount:${module.automation-tf-bootstrap-sa.email}",
    "serviceAccount:${module.automation-tf-tenants-sa.email}",
    "serviceAccount:${module.automation-tf-resman-sa.email}"
  ]
}

module "automation-project" {
  source          = "../../../modules/project"
  billing_account = var.billing_account.id
  name            = local.project_map["automation-project"]
  parent = coalesce(
    var.project_parent_ids.automation, module.branch-common-services-folder.folder.name
  )
  contacts = (
    var.bootstrap_user != null || var.essential_contacts == null
    ? {}
    : { (var.essential_contacts) = ["ALL"] }
  )
  # human (groups) IAM bindings
  iam_by_principals = {
    (local.principals.gcp-devops) = [
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountTokenCreator",
    ]
    (local.principals.gcp-organization-admins) = [
      "roles/iam.serviceAccountTokenCreator",
      "roles/iam.workloadIdentityPoolAdmin"
    ]
  }
  # machine (service accounts) IAM bindings
  iam = {
    "roles/browser" = [
      module.automation-tf-resman-r-sa.iam_email
    ]
    "roles/owner" = [
      module.automation-tf-bootstrap-sa.iam_email
    ]
    "roles/cloudbuild.builds.editor" = [
      module.automation-tf-resman-sa.iam_email
    ]
    "roles/cloudbuild.builds.viewer" = [
      module.automation-tf-resman-r-sa.iam_email
    ]
    "roles/iam.serviceAccountAdmin" = [
      module.automation-tf-resman-sa.iam_email,
      module.automation-tf-tenants-sa.iam_email
    ]
    "roles/iam.serviceAccountViewer" = [
      module.automation-tf-resman-r-sa.iam_email
    ]
    "roles/iam.workloadIdentityPoolAdmin" = [
      module.automation-tf-resman-sa.iam_email
    ]
    "roles/iam.workloadIdentityPoolViewer" = [
      module.automation-tf-resman-r-sa.iam_email
    ]
    "roles/source.admin" = [
      module.automation-tf-resman-sa.iam_email
    ]
    "roles/source.reader" = [
      module.automation-tf-resman-r-sa.iam_email
    ]
    "roles/storage.admin" = [
      module.automation-tf-resman-sa.iam_email,
      module.automation-tf-tenants-sa.iam_email
    ]
    ("organizations/${var.organization.id}/roles/storageViewer") = [
      module.automation-tf-bootstrap-r-sa.iam_email,
      module.automation-tf-resman-r-sa.iam_email,
      module.automation-tf-tenants-r-sa.iam_email
    ]
    "roles/viewer" = [
      module.automation-tf-bootstrap-r-sa.iam_email,
      module.automation-tf-resman-r-sa.iam_email,
      module.automation-tf-tenants-r-sa.iam_email
    ]
  }
  iam_bindings = {
    delegated_grants_resman = {
      members = [module.automation-tf-resman-sa.iam_email]
      role    = "roles/resourcemanager.projectIamAdmin"
      condition = {
        title       = "resman_delegated_grant"
        description = "Resource manager service account delegated grant."
        expression = format(
          "api.getAttribute('iam.googleapis.com/modifiedGrantsByRole', []).hasOnly(['%s'])",
          "roles/serviceusage.serviceUsageConsumer"
        )
      }
    }
  }
  iam_bindings_additive = {
    serviceusage_resman = {
      member = module.automation-tf-resman-sa.iam_email
      role   = "roles/serviceusage.serviceUsageConsumer"
    }
    serviceusage_resman_r = {
      member = module.automation-tf-resman-r-sa.iam_email
      role   = "roles/serviceusage.serviceUsageViewer"
    }
    serviceusage_tenant = {
      member = module.automation-tf-tenants-sa.iam_email
      role   = "roles/serviceusage.serviceUsageConsumer"
    }
    serviceusage_tenant_r = {
      member = module.automation-tf-tenants-r-sa.iam_email
      role   = "roles/serviceusage.serviceUsageViewer"
    }
  }
  org_policies = var.bootstrap_user != null ? {} : {
    "compute.skipDefaultNetworkCreation" = {
      rules = [{ enforce = true }]
    }
    "iam.automaticIamGrantsForDefaultServiceAccounts" = {
      rules = [{ enforce = true }]
    }
    "iam.disableServiceAccountKeyCreation" = {
      rules = [{ enforce = true }]
    }
  }
  services = concat(
    [
      "accesscontextmanager.googleapis.com",
      "assuredworkloads.googleapis.com",
      "bigquery.googleapis.com",
      "bigqueryreservation.googleapis.com",
      "bigquerystorage.googleapis.com",
      "billingbudgets.googleapis.com",
      "cloudasset.googleapis.com",
      "cloudbilling.googleapis.com",
      "cloudidentity.googleapis.com",
      "cloudkms.googleapis.com",
      "cloudquotas.googleapis.com",
      "cloudresourcemanager.googleapis.com",
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
      "sts.googleapis.com",
      "networksecurity.googleapis.com"
    ],
    # enable specific service only after org policies have been applied
    var.bootstrap_user != null ? [] : [
      "cloudbuild.googleapis.com",
      "compute.googleapis.com",
      "container.googleapis.com",
    ]
  )
}

resource "google_compute_project_metadata" "metadata-automation" {
  project = module.automation-project.project_id
  metadata = {
    block-project-ssh-keys = "TRUE" # CIS Compliance Benchmark 4.3
    enable-oslogin         = "TRUE" # CIS Compliance Benchmark 4.4
  }
}

# output files bucket

module "automation-tf-output-gcs" {
  source         = "../../../modules/gcs"
  project_id     = module.automation-project.project_id
  name           = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-prod-iac-core-outputs")
  prefix         = local.prefix
  location       = local.primary_location_gcs
  storage_class  = local.gcs_storage_class
  versioning     = true
  depends_on     = [module.organization, module.top-level-folder, module.gcs-kms]
  encryption_key = module.gcs-kms[local.primary_location_gcs].keys.gcs.id
}

# this stage's bucket and service account

module "automation-tf-bootstrap-gcs" {
  source         = "../../../modules/gcs"
  project_id     = module.automation-project.project_id
  name           = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-prod-iac-core-bootstrap")
  prefix         = local.prefix
  location       = local.primary_location_gcs
  storage_class  = local.gcs_storage_class
  versioning     = true
  depends_on     = [module.organization, module.top-level-folder]
  encryption_key = module.gcs-kms[local.primary_location_gcs].keys.gcs.id
}

module "automation-tf-bootstrap-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = module.automation-project.project_id
  name         = "prod-bootstrap-0"
  display_name = "Terraform organization bootstrap service account."
  prefix       = local.prefix
  # allow SA used by CI/CD workflow to impersonate this SA
  iam = {
    "roles/iam.serviceAccountTokenCreator" = compact([
      try(module.automation-tf-cicd-sa["bootstrap"].iam_email, null)
    ])
  }
  iam_project_roles = {
    (var.bootstrap_project) = ["roles/serviceusage.serviceUsageConsumer"]
  }
  iam_folder_roles = {
    (var.top_level_folder.id) = [
      "roles/serviceusage.serviceUsageConsumer",
      "roles/cloudkms.admin"
    ]
  }
  iam_storage_roles = {
    (module.automation-tf-output-gcs.name)                                            = ["roles/storage.admin"]
    (lower("${element(split(".", var.top_level_folder.name), 0)}-org-iac"))           = ["roles/storage.admin"]
    (lower("${element(split(".", var.top_level_folder.name), 0)}-org-iac-bootstrap")) = ["roles/storage.admin"]
  }
}

module "automation-tf-bootstrap-r-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = module.automation-project.project_id
  name         = "prod-bootstrap-0r"
  display_name = "Terraform organization bootstrap service account (read-only)."
  prefix       = local.prefix
  # allow SA used by CI/CD workflow to impersonate this SA
  iam = {
    "roles/iam.serviceAccountTokenCreator" = compact([
      try(module.automation-tf-cicd-r-sa["bootstrap"].iam_email, null)
    ])
  }
  # we grant organization roles here as IAM bindings have precedence over
  # custom roles in the organization module, so these need to depend on it
  iam_organization_roles = {
    (var.organization.id) = [
      "organizations/${var.organization.id}/roles/organizationAdminViewer",
      "organizations/${var.organization.id}/roles/tagViewer"
    ]
  }
  iam_storage_roles = {
    (module.automation-tf-output-gcs.name) = ["organizations/${var.organization.id}/roles/storageViewer"]
  }
}

# resource hierarchy stage's bucket and service account

module "automation-tf-resman-gcs" {
  source        = "../../../modules/gcs"
  project_id    = module.automation-project.project_id
  name          = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-prod-iac-core-config-0")
  prefix        = local.prefix
  location      = local.primary_location_gcs
  storage_class = local.gcs_storage_class
  versioning    = true
  iam = {
    "roles/storage.objectAdmin"  = [module.automation-tf-resman-sa.iam_email]
    "roles/storage.objectViewer" = [module.automation-tf-resman-r-sa.iam_email]
  }
  depends_on     = [module.organization, module.top-level-folder, module.gcs-kms]
  encryption_key = module.gcs-kms[local.primary_location_gcs].keys.gcs.id
}

module "automation-tf-resman-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = module.automation-project.project_id
  name         = "prod-resman-0"
  display_name = "Terraform stage 1 resman service account."
  prefix       = local.prefix
  # allow SA used by CI/CD workflow to impersonate this SA
  # we use additive IAM to allow tenant CI/CD SAs to impersonate it
  iam_bindings_additive = merge(
    (local.cicd_resman_sa == "" ? {} : {
      cicd_token_creator = {
        member = local.cicd_resman_sa
        role   = "roles/iam.serviceAccountTokenCreator"
      }
    })
  )
  iam_storage_roles = {
    (module.automation-tf-output-gcs.name) = ["roles/storage.admin"]
  }
}

resource "google_billing_account_iam_member" "automation_billing_admins" {
  for_each           = toset(local.billing_admins)
  billing_account_id = var.billing_account.id
  role               = "roles/billing.admin"
  member             = each.value
}

module "automation-tf-resman-r-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = module.automation-project.project_id
  name         = "prod-resman-0r"
  display_name = "Terraform stage 1 resman service account (read-only)."
  prefix       = local.prefix
  # allow SA used by CI/CD workflow to impersonate this SA
  # we use additive IAM to allow tenant CI/CD SAs to impersonate it
  iam_bindings_additive = (
    local.cicd_resman_r_sa == "" ? {} : {
      cicd_token_creator = {
        member = local.cicd_resman_r_sa
        role   = "roles/iam.serviceAccountTokenCreator"
      }
    }
  )
  # we grant organization roles here as IAM bindings have precedence over
  # custom roles in the organization module, so these need to depend on it
  iam_organization_roles = {
    (var.organization.id) = [
      "organizations/${var.organization.id}/roles/organizationAdminViewer",
      "organizations/${var.organization.id}/roles/tagViewer"
    ]
  }
  iam_storage_roles = {
    (module.automation-tf-output-gcs.name) = ["organizations/${var.organization.id}/roles/storageViewer"]
  }
}

module "automation-tf-tenant-gcs" {
  source        = "../../../modules/gcs"
  project_id    = module.automation-project.project_id
  name          = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-prod-iac-core-tenants")
  prefix        = local.prefix
  location      = local.primary_location_gcs
  storage_class = local.gcs_storage_class
  versioning    = true
  iam = {
    "roles/storage.objectAdmin"  = [module.automation-tf-tenants-sa.iam_email]
    "roles/storage.objectViewer" = [module.automation-tf-tenants-r-sa.iam_email]
  }
  depends_on     = [module.organization, module.top-level-folder, module.gcs-kms]
  encryption_key = module.gcs-kms[local.primary_location_gcs].keys.gcs.id
}

# automation service account
module "automation-tf-tenants-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = module.automation-project.project_id
  name         = "prod-tenant-0"
  display_name = "Terraform tenant service account."
  prefix       = var.prefix
  iam_bindings_additive = merge(
    try(module.automation-tf-cicd-sa["tenant"].iam_email, "") == "" ? {} : {
      cicd_token_creator = {
        member = module.automation-tf-cicd-sa["tenant"].iam_email
        role   = "roles/iam.serviceAccountTokenCreator"
      }
    }
  )
  iam_storage_roles = {
    (module.automation-tf-output-gcs.name) = ["roles/storage.admin"]
  }
  iam_organization_roles = {
    (var.organization.id) = ["roles/iam.denyAdmin"]
  }
}

# automation read-only service account

module "automation-tf-tenants-r-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = module.automation-project.project_id
  name         = "prod-tenant-0r"
  display_name = "Terraform tenant service account (read-only)."
  prefix       = var.prefix
  iam_bindings_additive = merge(
    try(module.automation-tf-cicd-r-sa["tenant"].iam_email, "") == "" ? {} : {
      cicd_token_creator = {
        member = module.automation-tf-cicd-r-sa["tenant"].iam_email
        role   = "roles/iam.serviceAccountTokenCreator"
      }
    }
  )
  iam_storage_roles = {
    (module.automation-tf-output-gcs.name) = ["organizations/${var.organization.id}/roles/storageViewer"]
  }
}

module "automation-tf-inputs-gcs" {
  source         = "../../../modules/gcs"
  project_id     = module.automation-project.project_id
  name           = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-prod-iac-core-inputs")
  prefix         = local.prefix
  location       = local.primary_location_gcs
  storage_class  = local.gcs_storage_class
  versioning     = true
  depends_on     = [module.organization, module.top-level-folder]
  encryption_key = module.gcs-kms[local.primary_location_gcs].keys.gcs.id
}

module "automation-tf-config-gcs" {
  count          = fileexists(local.config_env_file) ? 1 : 0
  source         = "../../../modules/gcs"
  project_id     = module.automation-project.project_id
  name           = lower("${replace(lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime), "_", " ")}-prod-iac-core-config")
  prefix         = local.prefix
  location       = local.primary_location_gcs
  storage_class  = local.gcs_storage_class
  versioning     = true
  depends_on     = [module.organization, module.top-level-folder]
  encryption_key = module.gcs-kms[local.primary_location_gcs].keys.gcs.id
  force_destroy  = true
}

resource "google_project_organization_policy" "automation_project_policy" {
  project    = module.automation-project.project_id
  constraint = "constraints/gcp.restrictServiceUsage"

  list_policy {
    allow {
      values = concat(
        local.compliance_list,
        local.coa2_list
      )
    }
  }
}