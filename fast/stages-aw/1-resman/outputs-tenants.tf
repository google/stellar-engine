/**
 * Copyright 2023 Google LLC
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
  tenant_core_providers = {
    for k, v in local.tenant_envs :
    k => templatefile("${path.module}/templates/providers.tf.tpl", {
      bucket            = module.tenant-core-gcs[k].name
      name              = k
      sa                = module.tenant-core-sa[k].email
      backend_extra     = null
      bootstrap_project = null
    })
  }
  tenant_self_providers = {
    for k, v in local.tenant_envs :
    k => templatefile("${path.module}/templates/providers.tf.tpl", {
      bucket            = module.tenant-self-iac-gcs-states[k].name
      name              = k
      sa                = module.tenant-self-iac-sa[k].email
      backend_extra     = null
      bootstrap_project = null
    })
  }
  tenant_tfvars = {
    for k, v in local.tenant_envs : k => merge(v, {
      automation = {
        core_bucket    = module.tenant-core-gcs[k].name
        core_sa        = module.tenant-core-sa[k].email
        outputs_bucket = module.tenant-self-iac-gcs-outputs[k].name
        project_id     = module.tenant-self-iac-projects[k].project_id
        sa             = module.tenant-self-iac-sa[k].email
        state_bucket   = module.tenant-self-iac-gcs-states[k].name
      }
      core = {
        billing_account = var.billing_account
        organization    = var.organization
        main_project    = module.tenant-self-main-projects[k].id
      }
      folder_ids = {
        self = module.tenant-top-folders[k].id
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

resource "local_file" "tenant-core-providers" {
  for_each = (
    var.outputs_location == null ? {} : local.tenant_core_providers
  )
  file_permission = "0644"
  filename = (
    "${pathexpand(var.outputs_location)}/providers/tenant/${each.key}-providers.tf"
  )
  content = each.value
}

resource "google_storage_bucket_object" "tenant-core-tfvars" {
  for_each = local.tenant_tfvars
  bucket   = var.automation.outputs_bucket
  name     = "tfvars/tenant/${each.key}.auto.tfvars.json"
  content  = jsonencode(each.value)
}

resource "google_storage_bucket_object" "tenant-core-providers" {
  for_each = local.tenant_core_providers
  bucket   = var.automation.outputs_bucket
  name     = "providers/tenant/${each.key}-providers.tf"
  content  = each.value
}

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
  for_each = local.tenant_tfvars
  bucket   = module.tenant-self-iac-gcs-outputs[each.key].name
  name     = "tfvars/${each.key}.auto.tfvars.json"
  content  = jsonencode(each.value)
}

resource "google_storage_bucket_object" "tenant-self-providers" {
  for_each = local.tenant_self_providers
  bucket   = module.tenant-self-iac-gcs-outputs[each.key].name
  name     = "providers/${each.key}-providers.tf"
  content  = each.value
}