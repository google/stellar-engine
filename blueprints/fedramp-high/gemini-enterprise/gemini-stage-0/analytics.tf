# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

resource "google_project_iam_audit_config" "discovery_engine_audit" {
  count   = var.enable_analytics ? 1 : 0
  project = var.main_project_id
  service = "discoveryengine.googleapis.com"
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
  audit_log_config {
    log_type = "ADMIN_READ"
  }
}

resource "google_bigquery_dataset" "analytics_dataset" {
  count       = var.enable_analytics ? 1 : 0
  dataset_id  = "${replace(var.prefix, "-", "_")}_gemini_analytics"
  project     = var.main_project_id
  location    = var.geolocation
  description = "Dataset for Gemini Enterprise Discovery Engine audit logs"
}

resource "google_logging_project_sink" "discovery_engine_sink" {
  count       = var.enable_analytics ? 1 : 0
  name        = "${var.prefix}-discovery-engine-analytics-sink"
  project     = var.main_project_id
  destination = "bigquery.googleapis.com/${google_bigquery_dataset.analytics_dataset[0].id}"
  filter      = "protoPayload.serviceName=\"discoveryengine.googleapis.com\""
  bigquery_options {
    use_partitioned_tables = true
  }
  unique_writer_identity = true
}

resource "google_bigquery_dataset_iam_member" "sink_bq_editor" {
  count      = var.enable_analytics ? 1 : 0
  dataset_id = google_bigquery_dataset.analytics_dataset[0].dataset_id
  project    = var.main_project_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.discovery_engine_sink[0].writer_identity
}

resource "google_artifact_registry_repository" "analytics_repo" {
  count         = var.enable_analytics ? 1 : 0
  location      = var.region
  repository_id = "${var.prefix}-gemini-analytics"
  description   = "Docker repository for Gemini Analytics"
  format        = "DOCKER"
  project       = var.main_project_id
}

resource "google_service_account" "analytics_sa" {
  count        = var.enable_analytics ? 1 : 0
  account_id   = "${var.prefix}-analytics-sa"
  display_name = "Gemini Analytics Service Account"
  project      = var.main_project_id
}

resource "google_project_iam_member" "analytics_sa_bq_user" {
  count   = var.enable_analytics ? 1 : 0
  project = var.main_project_id
  role    = "roles/bigquery.user"
  member  = "serviceAccount:${google_service_account.analytics_sa[0].email}"
}

resource "google_bigquery_dataset_iam_member" "analytics_sa_dataset_viewer" {
  count      = var.enable_analytics ? 1 : 0
  dataset_id = google_bigquery_dataset.analytics_dataset[0].dataset_id
  project    = var.main_project_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.analytics_sa[0].email}"
}

resource "google_artifact_registry_repository_iam_member" "analytics_sa_repo_reader" {
  count      = var.enable_analytics ? 1 : 0
  project    = var.main_project_id
  location   = google_artifact_registry_repository.analytics_repo[0].location
  repository = google_artifact_registry_repository.analytics_repo[0].name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.analytics_sa[0].email}"
}

resource "google_project_iam_member" "compute_sa_storage_viewer" {
  count   = var.enable_analytics ? 1 : 0
  project = var.main_project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "compute_sa_log_writer" {
  count   = var.enable_analytics ? 1 : 0
  project = var.main_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_artifact_registry_repository_iam_member" "compute_sa_repo_writer" {
  count      = var.enable_analytics ? 1 : 0
  project    = var.main_project_id
  location   = google_artifact_registry_repository.analytics_repo[0].location
  repository = google_artifact_registry_repository.analytics_repo[0].name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}




