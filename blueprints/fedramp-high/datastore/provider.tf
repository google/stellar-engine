terraform {
  required_version = ">= 1.11.4"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 3.53, < 6"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2.3"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.11"
    }
  }
}

provider "google" {
  project = var.main_project_id
  region  = var.region
}