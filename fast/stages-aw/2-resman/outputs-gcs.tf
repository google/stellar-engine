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
# tfdoc:file:description Output files persistence to automation GCS bucket.

resource "google_storage_bucket_object" "providers" {
  for_each = local.providers
  bucket   = var.automation.outputs_bucket
  name     = "providers/${each.key}-providers.tf"
  content  = each.value
}

resource "google_storage_bucket_object" "tenant-providers" {
  bucket  = var.automation.outputs_bucket
  name    = "providers/5-tenant-providers.tf"
  content = local.tenant_resman_providers
}

resource "google_storage_bucket_object" "tenant_outputs" {
  bucket = var.automation.outputs_bucket
  name   = "stage_2_tenant_outputs.json"
  content = jsonencode({
    tenant_environments = var.tenant_environments
  })
}

resource "google_storage_bucket_object" "tfvars" {
  bucket  = var.automation.outputs_bucket
  name    = "tfvars/2-resman.auto.tfvars.json"
  content = jsonencode(local.tfvars)
}

resource "google_storage_bucket_object" "workflows" {
  for_each = merge(local.cicd_workflows, local.team_cicd_workflows)
  bucket   = var.automation.outputs_bucket
  name     = "workflows/${replace(each.key, "_", "-")}-workflow.yaml"
  content  = each.value
}

resource "google_storage_bucket_object" "tfvars_user_definitions" {
  bucket  = var.automation.inputs_bucket
  name    = "stage-2/stage-2-inputs.auto.tfvars.json"
  content = local.tfvars_content
}
