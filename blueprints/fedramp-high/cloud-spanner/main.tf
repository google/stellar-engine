resource "google_project_service" "spanner_api" {
  project            = var.main_project_id
  service            = "spanner.googleapis.com"
  disable_on_destroy = false
}

module "cloud_spanner" {
  source     = "../../../modules/spanner-instance-se"
  project_id = var.main_project_id
  edition    = var.edition
  instance = {
    name         = var.instance_name
    display_name = var.display_name
    config = {
      name = var.config_name
    }
    autoscaling = {
      limits = {
        min_processing_units = var.min_processing_units
        max_processing_units = var.max_processing_units
      }
      targets = {
        high_priority_cpu_utilization_percent = var.high_priority_cpu_utilization_percent
        storage_utilization_percent           = var.storage_utilization_percent
      }
    }
  }

  databases = {
    (var.database_name) = {
      iam = {
        "roles/spanner.databaseUser" = [
          var.database_user
        ]
      }
      enable_drop_protection = var.database_drop_protection
    }
  }

  depends_on = [google_project_service.spanner_api]
}