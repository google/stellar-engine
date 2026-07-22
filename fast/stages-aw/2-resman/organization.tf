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
# tfdoc:file:description Organization policies.

locals {
  _org_only_roles = [
    "roles/billing.user",
    "roles/cloudasset.viewer",
    "roles/compute.orgFirewallPolicyAdmin",
    "roles/orgpolicy.policyAdmin"
  ]
  folder_iam_bindings_additive = {
    for k, v in local.iam_bindings_additive : k => v
    if !contains(local._org_only_roles, v.role)
  }
  org_iam_bindings_additive = {
    for k, v in local.iam_bindings_additive : k => v
    if contains(local._org_only_roles, v.role)
  }
}

module "organization" {
  source          = "../../../modules/organization-se"
  organization_id = "organizations/${var.organization.id}"
  # additive bindings via delegated IAM grant set in stage 0
  iam_bindings_additive = local.org_iam_bindings_additive
}

module "top-level-folder" {
  source        = "../../../modules/folder"
  folder_create = false
  id            = "folders/${var.top_level_folder.id}"
  parent        = "organizations/${var.organization.id}"
  # additive bindings, used for roles co-managed by different stages
  iam_bindings_additive = local.folder_iam_bindings_additive
}