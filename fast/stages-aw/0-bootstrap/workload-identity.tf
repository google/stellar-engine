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
# tfdoc:file:description Workload Identity Federation configurations.

locals {
  workload_identity_providers = {
    for k, v in coalesce(var.federated_identity_providers, {}) : k => v
    if v.issuer != null
  }
  workload_identity_providers_defs = {
    github = {
      issuer           = "https://token.actions.githubusercontent.com"
      principal_branch = "principal://iam.googleapis.com/%s/subject/repo:%s:ref:refs/heads/%s"
      principal_repo   = "principal://iam.googleapis.com/%s/subject/repo:%s:pull_request"
    }
    gitlab = {
      issuer           = "https://gitlab.com"
      principal_branch = "principal://iam.googleapis.com/%s/subject/project_path:%s:ref_type:branch:ref:%s"
      principal_repo   = "principal://iam.googleapis.com/%s/subject/project_path:%s:ref_type:branch:ref:main"
    }
  }
}

resource "google_iam_workload_identity_pool" "default" {
  count                     = length(local.workload_identity_providers) > 0 ? 1 : 0
  provider                  = google-beta
  project                   = module.automation-project.project_id
  workload_identity_pool_id = "${local.prefix}-bootstrap"
  display_name              = "Bootstrap workload identity pool."
}

resource "google_iam_workload_identity_pool_provider" "default" {
  for_each                           = local.workload_identity_providers
  provider                           = google-beta
  project                            = module.automation-project.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.default[0].workload_identity_pool_id
  workload_identity_pool_provider_id = each.key
  display_name                       = "Bootstrap workload identity provider ${each.key}."
  attribute_mapping                  = each.value.attribute_mapping
  attribute_condition                = each.value.attribute_condition
  oidc {
    allowed_audiences = each.value.audiences
    issuer_uri        = each.value.issuer
  }
}

resource "google_iam_workforce_pool" "default" {
  count             = var.workforce_identity_pool != null ? 1 : 0
  provider          = google-beta
  parent            = "organizations/${var.organization.id}"
  workforce_pool_id = "${local.prefix}-bootstrap"
  location          = "global"
  display_name      = "Bootstrap workforce identity pool."
  description       = "Bootstrap workforce identity pool."
  disabled          = false
}
