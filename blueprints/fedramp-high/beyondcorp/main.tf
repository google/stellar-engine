module "beyondcorp" {
  source              = "../../../modules/beyondcorp"
  project_id          = var.main_project_id
  region              = var.region
  organization_id     = var.organization_id
  oauth_client_id     = var.oauth_client_id
  oauth_client_secret = var.oauth_client_secret
  iap_user_email      = var.iap_user_email
  endpoint_name       = var.endpoint_name
  policy_title        = var.policy_title
}