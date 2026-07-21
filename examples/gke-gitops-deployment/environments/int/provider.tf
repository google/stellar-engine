terraform {
  backend "gcs" {
    bucket = "[prefix]-prod-cloud-build-state"
  }
}

provider "google" {
  impersonate_service_account = "cloud-builder-terraform-sa@[project].iam.gserviceaccount.com"
  project                     = var.main_project_id
}