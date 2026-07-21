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
    tls = {
      source  = "hashicorp/tls"
      version = "4.0.6"
    }
  }
}

provider "google" {
  project               = var.network_project_id
  region                = var.region
  billing_project       = var.main_project_id
  user_project_override = true
}

provider "google-beta" {
  project               = var.network_project_id
  region                = var.region
  billing_project       = var.main_project_id
  user_project_override = true
}