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

resource "google_project_service" "datastore_api" {
  project            = var.main_project_id
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}
module "firestore" {
  source     = "../../../modules/firestore"
  project_id = var.main_project_id
  database = {
    name            = var.firestore_database_name
    location_id     = var.region
    type            = "FIRESTORE_NATIVE"
    deletion_policy = "DELETE"
  }

  backup_schedule = var.backup_schedule

  depends_on = [google_project_service.datastore_api]
}