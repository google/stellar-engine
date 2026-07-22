/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
    }
  }

  depends_on = [google_project_service.spanner_api]
}