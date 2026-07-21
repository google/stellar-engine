resource "google_project_service" "datastore_api" {
  project            = var.main_project_id
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}
module "firestore" {
  source     = "../../../modules/firestore"
  project_id = var.main_project_id
  database = {
    name            = var.firestore_database_name
    location_id     = var.region
    type            = "FIRESTORE_NATIVE"
    deletion_policy = "DELETE"
  }

  backup_schedule = var.backup_schedule

  depends_on = [google_project_service.datastore_api]
}