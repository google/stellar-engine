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
  _tpl_providers = "${path.module}/templates/providers.tf.tpl"
  # render CI/CD workflow templates
  cicd_workflows = {
    for k, v in local.cicd_repositories : k => templatefile(
      "${path.module}/templates/workflow-${v.type}.yaml", {
        # If users give a list of custom audiences we set by default the first element.
        # If no audiences are given, we set https://iam.googleapis.com/{PROVIDER_NAME}
        audiences = try(
          local.cicd_providers[v["identity_provider"]].audiences, ""
        )
        identity_provider = try(
          local.cicd_providers[v["identity_provider"]].name, ""
        )
        outputs_bucket = module.automation-tf-output-gcs.name
        service_accounts = {
          apply = try(module.automation-tf-cicd-sa[k].email, "")
          plan  = try(module.automation-tf-cicd-r-sa[k].email, "")
        }
        stage_name = k
        tf_providers_files = {
          apply = local.cicd_workflow_providers[k]
          plan  = local.cicd_workflow_providers["${k}_r"]
        }
        tf_var_files = local.cicd_workflow_var_files[k]
      }
    )
  }
  custom_roles_map = {
    for id, role in data.google_iam_role.custom_iam_roles :
    lower(replace(id, "/([A-Z])/", "_$1")) => role.name
  }
  providers = {
    "1-assured-workload" = templatefile(local._tpl_providers, {
      backend_extra = null
      bucket        = module.automation-tf-bootstrap-gcs.name
      name          = "assured workload bootstrap"
      sa            = module.automation-tf-bootstrap-sa.email
    })
    "1-assured-workload-r" = templatefile(local._tpl_providers, {
      backend_extra = null
      bucket        = module.automation-tf-bootstrap-gcs.name
      name          = "assured workload bootstrap"
      sa            = module.automation-tf-bootstrap-r-sa.email
    })
    "2-resman" = templatefile(local._tpl_providers, {
      backend_extra = null
      bucket        = module.automation-tf-resman-gcs.name
      name          = "resman"
      sa            = module.automation-tf-resman-sa.email
    })
    "2-resman-r" = templatefile(local._tpl_providers, {
      backend_extra = null
      bucket        = module.automation-tf-resman-gcs.name
      name          = "resman"
      sa            = module.automation-tf-resman-r-sa.email
    })
    "1-assured-workload-tenant" = templatefile(local._tpl_providers, {
      backend_extra = join("\n", [
        "# remove the newline between quotes and set the tenant name as prefix",
        "prefix = \"",
        "\""
      ])
      bucket = module.automation-tf-resman-gcs.name
      name   = "bootstrap-tenant"
      sa     = module.automation-tf-resman-sa.email
    })
  }
  tfvars = {
    alert_email = var.alert_email
    automation = {
      config_bucket = length(google_storage_bucket_object.config_env) > 0 ? google_storage_bucket_object.config_env["config_env_object"].bucket : null
      federated_identity_pool = try(
        google_iam_workload_identity_pool.default[0].name, null
      )
      federated_identity_providers = local.cicd_providers
      inputs_bucket                = module.automation-tf-inputs-gcs.name
      outputs_bucket               = module.automation-tf-output-gcs.name
      project_id                   = module.automation-project.project_id
      project_number               = module.automation-project.number
      tenant_bucket                = module.automation-tf-tenant-gcs.name
      service_accounts = {
        bootstrap   = module.automation-tf-bootstrap-sa.email
        bootstrap-r = module.automation-tf-bootstrap-r-sa.email
        resman      = module.automation-tf-resman-sa.email
        resman-r    = module.automation-tf-resman-r-sa.email
        tenant      = module.automation-tf-tenants-sa.email
        tenant-r    = module.automation-tf-tenants-r-sa.email
      }
    }
    custom_roles = local.custom_roles_map
    regime_label = replace(var.assured_workloads.regime, "_", " ")

    logging = {
      project_id        = module.log-export-project.project_id
      project_number    = module.log-export-project.number
      writer_identities = module.organization.sink_writer_identities
      pubsub_topics     = { for k, v in module.pubsub-topics : k => v.id }
      service_accounts = {
        c5isr-pubsub = module.logging-c5isr-pubsub-sa.email
      }
    }
    assured_workloads          = merge(var.assured_workloads, { "folder" = "folders/${local.consumer_folder_id}" })
    tenants_folder_id          = module.tenants-container-folders.folder.id
    common_services_folder     = module.branch-common-services-folder.folder.name
    shared_services_project_id = module.netsec-shared-project.project_id
    regions = {
      primary   = element(var.locations.kms, 0)
      secondary = slice(var.locations.kms, 1, length(var.locations.kms))
    }
  }

  tfvars_globals = {
    billing_account  = var.billing_account
    fast_features    = var.fast_features
    groups           = local.principals
    locations        = local.locations
    organization     = var.organization
    prefix           = var.prefix
    regime_mapping   = var.regime_mapping
    top_level_folder = var.top_level_folder
  }

  inputs_tfvars = {
    billing_account   = var.billing_account
    locations         = var.locations
    organization      = var.organization
    outputs_location  = var.outputs_location
    prefix            = var.prefix
    fast_features     = var.fast_features
    assured_workloads = var.assured_workloads
    bootstrap_project = var.bootstrap_project
    alert_email       = var.alert_email
    top_level_folder  = var.top_level_folder
  }
  tfvars_content = jsonencode(local.inputs_tfvars)
}

output "alert_email" {
  description = "Email to receive log alerts."
  value       = var.alert_email
}

output "assured_workload" {
  description = "Assured Workload folder for the deployment."
  value       = "folders/${local.consumer_folder_id}"
}

output "automation" {
  description = "Automation resources."
  value       = local.tfvars.automation
}

output "automation_project_id" {
  description = "The ID of the IaC Core project."
  value       = module.automation-project.project_id
}

output "billing_dataset" {
  description = "BigQuery dataset prepared for billing export."
  value       = try(module.billing-export-dataset[0].id, null)
}

output "cicd_repositories" {
  description = "CI/CD repository configurations."
  value = {
    for k, v in local.cicd_repositories : k => {
      branch          = v.branch
      name            = v.name
      provider        = try(local.cicd_providers[v.identity_provider].name, null)
      service_account = try(module.automation-tf-cicd-sa[k].email, null)
    }
  }
}

output "common_services_folder" {
  description = "Common services folder where non-tenant related resources should be kept."
  value       = module.branch-common-services-folder.folder.name
}

output "custom_roles" {
  description = "Organization-level custom roles."
  value       = local.custom_roles_map
}

output "folder_ids" {
  description = "The Assured Workloads Folder i.e. DEV (IL5 AW)."
  value       = "folders/${local.consumer_folder_id}"
}

output "outputs_bucket" {
  description = "GCS bucket where generated output files are stored."
  value       = module.automation-tf-output-gcs.name
}

output "project_ids" {
  description = "Projects created by this stage."
  value = {
    automation     = module.automation-project.project_id
    billing-export = try(module.billing-export-project[0].project_id, null)
    log-export     = module.log-export-project.project_id
  }
}

# ready to use provider configurations for subsequent stages when not using files
output "providers" {
  # tfdoc:output:consumers stage-01
  description = "Terraform provider files for this stage and dependent stages."
  sensitive   = true
  value       = local.providers
}

output "pubsub-topics-id" {
  description = "Pubsub topics used for C5ISR logging."
  value = {
    for k, v in module.pubsub-topics : k => v.id
  }
}

output "service_accounts" {
  description = "Automation service accounts created by this stage."
  value = {
    bootstrap = module.automation-tf-bootstrap-sa.email
    resman    = module.automation-tf-resman-sa.email
    tenant    = module.automation-tf-tenants-sa.email
  }
}

output "shared_services_project_id" {
  description = "Project ID for NetSec Shared Services."
  value       = module.netsec-shared-project.project_id
}

# output "test" {
#   value = {
#     checklist               = local.checklist
#     iam_roles_authoritative = local.iam_roles_authoritative
#     iam_roles_additive      = local.iam_roles_additive
#     test                    = local.checklist
#   }
# }

output "tenants_container_ids" {
  description = "Folder IDs for the 'Tenants' sub-folders where tenant projects will live."
  value       = module.tenants-container-folders.folder.id
}

output "tfvars" {
  description = "Terraform variable files for the following stages."
  sensitive   = true
  value       = local.tfvars
}

output "workload_identity_pool" {
  description = "Workload Identity Federation pool and providers."
  value = {
    pool = try(
      google_iam_workload_identity_pool.default[0].name, null
    )
    providers = local.cicd_providers
  }
}
