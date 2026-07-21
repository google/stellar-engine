resource "google_iam_workload_identity_pool" "default" {
  provider                  = google-beta
  for_each                  = var.cicd != null ? local.tenant_projects : {}
  project                   = module.tenant-projects[each.key].project_id
  workload_identity_pool_id = "${each.key}-cicd"
}

resource "google_iam_workload_identity_pool_provider" "default" {
  provider = google-beta
  for_each = var.cicd != null ? local.tenant_projects : {}
  project  = module.tenant-projects[each.key].project_id
  workload_identity_pool_id = (
    google_iam_workload_identity_pool.default[each.key].workload_identity_pool_id
  )
  workload_identity_pool_provider_id = "${each.key}-cicd-gitlab"
  attribute_condition                = "attribute.project_path == '${var.cicd.gitlab_project_path}'"
  attribute_mapping = {
    "attribute.environment"           = "assertion.environment"
    "attribute.environment_protected" = "assertion.environment_protected"
    "attribute.namespace_id"          = "assertion.namespace_id"
    "attribute.namespace_path"        = "assertion.namespace_path"
    "attribute.pipeline_id"           = "assertion.pipeline_id"
    "attribute.pipeline_source"       = "assertion.pipeline_source"
    "attribute.project_id"            = "assertion.project_id"
    "attribute.project_path"          = "assertion.project_path"
    "attribute.ref"                   = "assertion.ref"
    "attribute.ref_protected"         = "assertion.ref_protected"
    "attribute.ref_type"              = "assertion.ref_type"
    "attribute.repository"            = "assertion.project_path"
    "attribute.sub"                   = "assertion.sub"
    "google.subject"                  = "assertion.sub"
  }
  oidc {
    # Setting an empty list configures allowed_audiences to the url of the provider
    allowed_audiences = [var.cicd.gitlab_uri]
    # If users don't provide an issuer_uri, we set the public one for the platform chosen.
    issuer_uri = var.cicd.gitlab_uri
    # OIDC JWKs in JSON String format. If no value is provided, they key is
    # fetched from the `.well-known` path for the issuer_uri
    jwks_json = try(trimspace(var.cicd.jwks_json), "")
  }
}

module "automation-tf-cicd-sa" {
  source       = "../../../modules/iam-service-account"
  for_each     = var.cicd != null ? local.tenant_projects : {}
  project_id   = module.tenant-projects[each.key].project_id
  name         = "${each.key}-acas-cicd"
  display_name = "Terraform CI/CD GitLab service account."
  iam = {
    "roles/iam.workloadIdentityUser" = [
      format(
        "principalSet://iam.googleapis.com/%s/attribute.repository/%s",
        google_iam_workload_identity_pool.default[each.key].name,
        var.cicd.gitlab_project_path
      )
    ]
  }
  iam_project_roles = {
    (module.tenant-projects[each.key].project_id) = ["roles/logging.logWriter"]
  }
}