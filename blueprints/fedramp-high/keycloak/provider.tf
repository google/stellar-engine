terraform {
  required_version = ">= 1.11.4"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.0.1, < 8.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 7.0.1, < 8.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
