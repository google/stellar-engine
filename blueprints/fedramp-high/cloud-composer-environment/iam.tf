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

resource "google_project_iam_member" "composer_worker" {
  project = var.main_project_id
  role    = "roles/composer.worker"
  member  = google_service_account.composer.member
}

resource "google_project_iam_member" "composer_service_agent" {
  project = var.main_project_id
  role    = var.service_agent_version
  member  = google_project_service_identity.composer_agent.member
}

resource "google_project_iam_member" "composer_network_user" {
  project = var.network_project_id
  role    = "roles/compute.networkUser"
  member  = google_project_service_identity.composer_agent.member
}

resource "google_project_iam_member" "composer_vpc_agent" {
  project = var.network_project_id
  role    = "roles/composer.sharedVpcAgent"
  member  = google_project_service_identity.composer_agent.member
}