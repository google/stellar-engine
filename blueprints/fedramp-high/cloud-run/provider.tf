terraform {
  required_version = ">=1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.0.1, < 8.0.0"
    }
  }
}

provider "google" {
  project = var.main_project_id
  region  = var.region
}
