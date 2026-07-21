resource "google_project_service" "datastore_api" {
  project            = var.main_project_id
  service            = "datastore.googleapis.com"
  disable_on_destroy = false
}
resource "time_sleep" "wait_for_datastore_db_ready" {
  depends_on      = [google_project_service.datastore_api]
  create_duration = "180s"
}
module "datastore" {
  source  = "terraform-google-modules/cloud-datastore/google"
  version = "~> 2.0"
  project = var.main_project_id
  indexes = file("index.yaml")

  depends_on = [
    google_project_service.datastore_api,
    time_sleep.wait_for_datastore_db_ready
  ]
}