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
  bucket   = module.automation-tf-output-gcs.name
  # provider suffix allows excluding via .gitignore when linked from stages
  name    = "providers/${each.key}-providers.tf"
  content = each.value
  # kms_key_name = module.gcs-kms.keys.gcs.id # may need to add back in
}

resource "google_storage_bucket_object" "stage_1_folder_outputs" {
  bucket = module.automation-tf-output-gcs.name
  name   = "tfvars/1-folder-ids.auto.tfvars.json"
  content = jsonencode({
    # Creates 'dev' -> Dev (il5 AW) '
    root_folder_id             = "folders/${local.consumer_folder_id}"
    tenant_container_id        = module.tenants-container-folders.folder.id
    shdsvc_folder_id           = module.branch-common-services-folder.folder.id
    shared_services_project_id = module.netsec-shared-project.project_id
  })
}

resource "google_storage_bucket_object" "tenant_outputs" {
  bucket = module.automation-tf-output-gcs.name
  name   = "stage_1_tenant_outputs.json"
  content = jsonencode({
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
    billing_account = var.billing_account
    groups          = var.groups
    locations       = local.locations
    logging = {
      project_id        = module.log-export-project.project_id
      project_number    = module.log-export-project.number
      writer_identities = module.organization.sink_writer_identities
      pubsub_topics     = { for k, v in module.pubsub-topics : k => v.id }
      service_accounts = {
        c5isr-pubsub = module.logging-c5isr-pubsub-sa.email
      }
    }
    organization = var.organization
    prefix       = var.prefix
    regions = {
      primary   = element(var.locations.kms, 0)
      secondary = slice(var.locations.kms, 1, length(var.locations.kms))
    }
    tenants_folder_id = module.tenants-container-folders.folder.id
  })
}

resource "google_storage_bucket_object" "tenant_config_vars" {
  bucket = module.automation-tf-output-gcs.name
  name   = "tfvars/1-tenant-names.auto.tfvars.json"
  content = jsonencode({
    tenant_envs = local.tenant_envs
  })
}

resource "google_storage_bucket_object" "tfvars" {
  bucket  = module.automation-tf-output-gcs.name
  name    = "tfvars/1-assured-workload.auto.tfvars.json"
  content = jsonencode(local.tfvars)
  # kms_key_name = module.gcs-kms.keys.gcs.id # may need to add back in
}

resource "google_storage_bucket_object" "tfvars_globals" {
  bucket  = module.automation-tf-output-gcs.name
  name    = "tfvars/1-globals.auto.tfvars.json"
  content = jsonencode(local.tfvars_globals)
  # kms_key_name = module.gcs-kms.keys.gcs.id # may need to add back in
}

resource "google_storage_bucket_object" "workflows" {
  for_each = local.cicd_workflows
  bucket   = module.automation-tf-output-gcs.name
  name     = "workflows/${each.key}-workflow.yaml"
  content  = each.value
  # kms_key_name = module.gcs-kms.keys.gcs.id # may need to add back in
}

resource "google_storage_bucket_object" "input_tfvars" {
  bucket  = module.automation-tf-inputs-gcs.name
  name    = "stage-1/stage-1-inputs.auto.tfvars.json"
  content = local.tfvars_content
}

resource "google_storage_bucket_object" "config_env" {
  for_each = local.config_env_bucket
  bucket   = each.value.bucket_name
  name     = each.value.object_name
  source   = each.value.source_path
}