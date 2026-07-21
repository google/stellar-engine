module "app-engine" {
  source      = "../../../modules/app-engine"
  project     = var.main_project_id
  location_id = var.region
}