terraform {
  required_version = ">= 1.11.4"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.0.1, < 8.0.0" # tftest
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 7.0.1, < 8.0.0" # tftest
    }
  }
}


provider "google" {
  project = var.main_project_id
  region  = var.region
  # impersonate_service_account = "XXXXX-iac-0@XXXX-iac-core-0.iam.gserviceaccount.com"
}

