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
  _tpl_providers = "${path.module}/templates/providers.tf.tpl"
  inputs_tfvars = {
    assured_workloads   = var.assured_workloads
    billing_account     = var.billing_account
    locations           = var.locations
    organization        = var.organization
    org_policies_config = var.org_policies_config
    bootstrap_project   = var.bootstrap_project
    top_level_folder    = var.top_level_folder
  }
  providers = {
    "0-organization-bootstrap" = templatefile(local._tpl_providers, {
      backend_extra = null
      bucket        = module.lz-logs-state-gcs.name
      name          = "organization bootstrap"
      prefix        = "terraform/state"
      project       = module.centralized-logging-project.project_id
    })
  }
  tfvars_content = jsonencode(local.inputs_tfvars)
}

output "workforce_identity_pool" {
  description = "Workforce Identity Federation pool."
  value = {
    pool = try(
      google_iam_workforce_pool.default[0].name, null
    )
  }
}
