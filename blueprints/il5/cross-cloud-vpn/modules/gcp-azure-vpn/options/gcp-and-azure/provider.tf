terraform {
  required_version = ">=1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  # Regional configuration is deferred to the resources/modules explicitly.
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}
