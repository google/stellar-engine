module "access_context_manager" {
  source = "../../../modules/access-context-manager"

  project_id          = var.main_project_id
  domain              = var.domain
  region              = var.region
  access_policy_title = var.access_policy_title
  access_levels       = var.access_levels
  service_perimeters  = var.service_perimeters
  organization_id     = var.organization_id
}

