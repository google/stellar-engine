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

# tfdoc:file:description Organization policies.

module "organization" {
  source          = "../../../modules/organization-se"
  organization_id = "organizations/${var.organization.id}"
  # additive bindings via delegated IAM grant set in stage 0
  iam_bindings_additive = var.deploy_org_resources.iam ? local.iam_bindings_additive : {}
}

module "root-folder-iam" {
  count         = var.deploy_org_resources.iam ? 0 : 1
  source        = "../../../modules/folder"
  folder_create = false
  id            = var.assured_workloads.folder
  iam_bindings_additive = {
    for k, v in local.iam_bindings_additive : k => v
    if !contains(["roles/billing.costsManager", "roles/billing.user"], v.role)
  }
}
