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

# tfdoc:file:description Workload Identity Federation configurations.

locals {
  workload_identity_providers = {
    for k, v in var.federated_identity_providers : k => merge(
      lookup(local.workload_identity_providers_defs, v.issuer, {}),
      v,
      {
        attribute_mapping = (
          v.attribute_mapping != null
          ? v.attribute_mapping
          : try(
            local.workload_identity_providers_defs[v.issuer].attribute_mapping,
            null
          )
        )
        audiences = (
          length(coalesce(v.audiences, [])) > 0
          ? v.audiences
          : (
            length(coalesce(try(v.custom_settings.audiences, null), [])) > 0
            ? v.custom_settings.audiences
            : null
          )
        )
        display_name = substr("Bootstrap WIF ${k}", 0, 32)
        issuer_uri = coalesce(
          try(v.custom_settings.issuer_uri, null),
          try(
            local.workload_identity_providers_defs[v.issuer].issuer_uri,
            null
          ),
          v.issuer
        )
        jwks_json = try(v.custom_settings.jwks_json, null)
      }
    )
    if v.issuer != null && v.issuer != ""
  }
  workload_identity_providers_defs = {
    # https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
    github = {
      attribute_mapping = {
        "google.subject"             = "assertion.sub"
        "attribute.sub"              = "assertion.sub"
        "attribute.actor"            = "assertion.actor"
        "attribute.repository"       = "assertion.repository"
        "attribute.repository_owner" = "assertion.repository_owner"
        "attribute.ref"              = "assertion.ref"
        "attribute.fast_sub"         = "\"repo:\" + assertion.repository + \":ref:\" + assertion.ref"
      }
      issuer_uri       = "https://token.actions.githubusercontent.com"
      principal_branch = "principalSet://iam.googleapis.com/%s/attribute.fast_sub/repo:%s:ref:refs/heads/%s"
      principal_repo   = "principalSet://iam.googleapis.com/%s/attribute.repository/%s"
    }
    # https://docs.gitlab.com/ee/ci/secrets/id_token_authentication.html#token-payload
    gitlab = {
      attribute_mapping = {
        "google.subject" = "assertion.sub"
        "attribute.sub"  = "assertion.sub"
        "attribute.environment" = (
          "has(assertion.environment) ? assertion.environment : \"\""
        )
        "attribute.environment_protected" = (
          "has(assertion.environment_protected) ? assertion.environment_protected : \"\""
        )
        "attribute.namespace_id"    = "assertion.namespace_id"
        "attribute.namespace_path"  = "assertion.namespace_path"
        "attribute.pipeline_id"     = "assertion.pipeline_id"
        "attribute.pipeline_source" = "assertion.pipeline_source"
        "attribute.project_id"      = "assertion.project_id"
        "attribute.project_path"    = "assertion.project_path"
        "attribute.repository"      = "assertion.project_path"
        "attribute.ref"             = "assertion.ref"
        "attribute.ref_protected"   = "assertion.ref_protected"
        "attribute.ref_type"        = "assertion.ref_type"
      }
      issuer_uri       = "https://gitlab.com"
      principal_branch = "principalSet://iam.googleapis.com/%s/attribute.sub/project_path:%s:ref_type:branch:ref:%s"
      principal_repo   = "principalSet://iam.googleapis.com/%s/attribute.repository/%s"
    }
  }
}

resource "google_iam_workload_identity_pool" "default" {
  count                     = length(local.workload_identity_providers) > 0 ? 1 : 0
  provider                  = google-beta
  project                   = module.automation-project.project_id
  workload_identity_pool_id = "${local.prefix}-bootstrap"
  display_name              = "Bootstrap workload pool"
}

resource "google_iam_workload_identity_pool_provider" "default" {
  for_each = local.workload_identity_providers
  provider = google-beta
  project  = module.automation-project.project_id
  workload_identity_pool_id = (
    google_iam_workload_identity_pool.default[0].workload_identity_pool_id
  )
  workload_identity_pool_provider_id = each.key
  display_name                       = each.value.display_name
  attribute_mapping                  = each.value.attribute_mapping
  attribute_condition                = each.value.attribute_condition
  oidc {
    allowed_audiences = each.value.audiences
    issuer_uri        = each.value.issuer_uri
    jwks_json         = each.value.jwks_json
  }
}

resource "google_iam_workforce_pool" "default" {
  count = (
    var.deploy_org_resources.workforce_identity_pool &&
    var.workforce_identity_pool != null ? 1 : 0
  )
  provider          = google-beta
  parent            = "organizations/${var.organization.id}"
  workforce_pool_id = "${local.prefix}-bootstrap"
  location          = "global"
  display_name = coalesce(
    var.workforce_identity_pool.display_name,
    "Bootstrap workforce pool"
  )
  description = coalesce(
    var.workforce_identity_pool.description,
    "Bootstrap workforce identity pool."
  )
  disabled         = var.workforce_identity_pool.disabled
  session_duration = var.workforce_identity_pool.session_duration
}
