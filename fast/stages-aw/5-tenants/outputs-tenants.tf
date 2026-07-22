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
  tenant_accounts = {
    for k, v in local.tenant_envs : k => {
      main_project    = module.tenant-projects[k].project_id
      env             = v.env
      tenant          = v.tenant
      admin_principal = var.tenant.admin_principal
    }
  }
  # tenant_core_providers = {
  #   for k, v in local.tenant_envs :
  #   k => templatefile("${path.module}/templates/providers.tf.tpl", {
  #     bucket        = module.tenant-core-gcs.name
  #     name          = k
  #     sa            = module.tenant-core-sa.email
  #     prefix        = null
  #     backend_extra = null
  #   })
  # }
  tenant_self_providers = {
    for k, v in local.tenant_envs :
    k => templatefile("${path.module}/templates/providers.tf.tpl", {
      bucket        = module.tenant-self-iac-gcs-states[k].name
      name          = k
      sa            = module.tenant-self-iac-sa[k].email
      prefix        = null
      backend_extra = null
    })
  }
  tenant_tfvars = {
    for k, v in local.tenant_envs : k => merge(v, {
      automation = {
        # core_bucket    = module.tenant-core-gcs.name
        core_sa        = module.tenant-core-sa.email
        outputs_bucket = module.tenant-self-iac-gcs-outputs[k].name
        sa             = module.tenant-self-iac-sa[k].email
        state_bucket   = module.tenant-self-iac-gcs-states[k].name
      }
      core = {
        organization = var.organization
        # main_project    = module.tenant-self-main-projects.id
      }
      folder_ids = {
        self = module.tenant-top-folders.id
      }
      shortname = k
      prefix    = "${var.prefix}-${k}"
    })
  }
}

# core tfvars and providers
resource "local_file" "tenant-core-tfvars" {
  for_each        = var.outputs_location == null ? {} : local.tenant_tfvars
  file_permission = "0644"
  filename = (
    "${pathexpand(var.outputs_location)}/tfvars/tenant/${each.key}.auto.tfvars.json"
  )
  content = jsonencode(each.value)
}

# resource "local_file" "tenant-core-providers" {
#   for_each = (
#     var.outputs_location == null ? {} : local.tenant_core_providers
#   )
#   file_permission = "0644"
#   filename = (
#     "${pathexpand(var.outputs_location)}/providers/tenant/${each.key}-providers.tf"
#   )
#   content = each.value
# }

resource "google_storage_bucket_object" "tenant-core-tfvars" {
  for_each = local.tenant_tfvars
  bucket   = var.automation.outputs_bucket
  name     = "tfvars/tenant/${each.key}.auto.tfvars.json"
  content  = jsonencode(each.value)
}

# resource "google_storage_bucket_object" "tenant-core-providers" {
#   for_each = local.tenant_core_providers
#   bucket   = var.automation.outputs_bucket
#   name     = "providers/tenant/${each.key}-providers.tf"
#   content  = each.value
# }

# tenant tfvars and providers
resource "local_file" "tenant-self-providers" {
  for_each = (
    var.outputs_location == null ? {} : local.tenant_self_providers
  )
  file_permission = "0644"
  filename = (
    "${pathexpand(var.outputs_location)}/providers/tenant/${each.key}-self-providers.tf"
  )
  content = each.value
}

resource "google_storage_bucket_object" "tenant-self-tfvars" {
  for_each = module.tenant-projects
  bucket   = module.tenant-self-iac-gcs-outputs[each.key].id
  name     = "tfvars/${each.key}.auto.tfvars.json"
  content  = jsonencode(each.value)
}

# resource "google_storage_bucket_object" "tenant-self-providers" {
#   for_each = local.tenant_self_providers
#   bucket   = module.tenant-self-iac-gcs-outputs.name
#   name     = "providers/${each.key}-providers.tf"
#   content  = each.value
# }