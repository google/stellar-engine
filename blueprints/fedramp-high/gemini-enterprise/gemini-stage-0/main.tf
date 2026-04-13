# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


## Data Variables + Enabling APIs ##

data "google_project" "project" {
  project_id = var.main_project_id
}

locals {
  base_services = [
    "aiplatform.googleapis.com",
    "discoveryengine.googleapis.com",
    "compute.googleapis.com",
    "cloudkms.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "accesscontextmanager.googleapis.com",
    "iam.googleapis.com",
    "iap.googleapis.com",
    "orgpolicy.googleapis.com",
    "serviceusage.googleapis.com",
    "secretmanager.googleapis.com"
  ]

  restricted_services = [
    "beyondcorp.googleapis.com",
    "certificatemanager.googleapis.com"
  ]

  enabled_services = concat(
    local.base_services,
    var.compliance_regime == "FEDRAMP_HIGH" || var.compliance_regime == "NONE" ? local.restricted_services : []
  )
}

resource "google_project_service" "services" {
  project  = var.main_project_id
  for_each = toset(local.enabled_services)
  service  = each.value
  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_on_destroy = false
}

# Create all project-level discoveryengine.googleapis.com service agents
resource "google_project_service_identity" "discoveryengine" {
  provider = google-beta
  project  = data.google_project.project.project_id
  service  = "discoveryengine.googleapis.com"

  depends_on = [
    google_project_service.services,
    time_sleep.wait_for_services
  ]
}

# Create all project-level storage.googleapis.com service agents
resource "google_project_service_identity" "storage" {
  provider = google-beta
  project  = data.google_project.project.project_id
  service  = "storage.googleapis.com"

  depends_on = [
    google_project_service.services,
    time_sleep.wait_for_services
  ]
}

# Create all project-level bigquery.googleapis.com service agents
resource "google_project_service_identity" "bigquery" {
  provider = google-beta
  project  = var.main_project_id
  service  = "bigquery.googleapis.com"

  depends_on = [
    google_project_service.services,
    time_sleep.wait_for_services
  ]
}

# Create all project-level iap.googleapis.com service agents
resource "google_project_service_identity" "iap" {
  provider = google-beta
  project  = var.main_project_id
  service  = "iap.googleapis.com"

  depends_on = [
    google_project_service.services,
    time_sleep.wait_for_services
  ]
}

# service-projectid@gs-project-accounts.iam.gserviceaccount.com
# service-projectid@gcp-sa-discoveryengine.iam.gserviceaccount.com
# This wait time is needed to give time to the API enablement and to create the google service-agents above, which are required to utilize the cloud KMS key.
resource "time_sleep" "wait_for_services" {
  create_duration = "180s" #Wait for APIs, particularly to avoid the "Discovery Engine API has not been used in project" error.

  depends_on = [
    google_project_service.services
  ]
}