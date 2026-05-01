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

locals {
  gcs_lifecycle_age              = 30
  bq_connector_refresh_interval  = "86400s" # Daily
  wait_for_bq_datastore_duration = "120s"

  # Discovery Engine Data Store Configuration
  discovery_engine_industry_vertical = "GENERIC"
  discovery_engine_solution_types    = ["SOLUTION_TYPE_SEARCH"]
  discovery_engine_content_config    = "CONTENT_REQUIRED"

  # Document Processing (digital_parsing_config or ocr_parsing_config)
  discovery_engine_parsing_mode = "digital_parsing_config"
}

# ---------------------------------------------------------------------------- #
#  Gemini Enterprise - Identity Config                                         #
# ---------------------------------------------------------------------------- #

# Discovery Engine ACL Config (Google Identity / Workforce Identity Federation)
resource "google_discovery_engine_acl_config" "gemini_enterprise_acl_config" {
  project  = var.main_project_id
  location = var.geolocation # Must match the connector location
  idp_config {
    idp_type = var.acl_idp_type == "GOOGLE_CLOUD_IDENTITY" ? "GSUITE" : var.acl_idp_type
    dynamic "external_idp_config" {
      for_each = var.acl_idp_type == "THIRD_PARTY" ? [1] : []
      content {
        workforce_pool_name = var.acl_workforce_pool_name
      }
    }
  }
  provider = google-beta

  depends_on = [
    time_sleep.wait_for_services
  ]
}

# ---------------------------------------------------------------------------- #
#  Gemini Enterprise - Google Cloud Storage Data Stores                        #
# ---------------------------------------------------------------------------- #

# GCS Buckets for Discovery Engine Data Sources
resource "google_storage_bucket" "gemini_enterprise_gcs_bucket" {
  for_each = var.create_data_stores ? { for k, v in var.gcs_data_store_configs : k => v if v.create_bucket } : {}

  project                     = var.main_project_id
  name                        = each.value.name
  location                    = var.geolocation
  uniform_bucket_level_access = true
  force_destroy               = true # Set to true only for non-production/demo

  dynamic "encryption" {
    for_each = local.cmek_key_id != null ? [1] : []
    content {
      default_kms_key_name = local.cmek_key_id
    }
  }

  lifecycle_rule {
    condition {
      age = local.gcs_lifecycle_age # Example: delete objects older than 30 days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    service     = "g4g-gcs-data-store"
    data_store  = each.key
  }

  depends_on = [
    google_kms_crypto_key_iam_member.gcs_sa_kms_access
  ]
}

# Random suffix for GCS Data Store IDs
resource "random_string" "gcs_suffix" {
  for_each = var.create_data_stores ? var.gcs_data_store_configs : {}

  length  = 6
  special = false
  upper   = false
  keepers = {
    industry_vertical = local.discovery_engine_industry_vertical
    solution_types    = join(",", local.discovery_engine_solution_types)
    content_config    = local.discovery_engine_content_config
    kms_key_name      = local.cmek_key_id
    parsing_mode      = local.discovery_engine_parsing_mode
  }
}

# Empty GCS Data Store
resource "google_discovery_engine_data_store" "gemini_enterprise_gcs_data_store" {
  for_each = var.create_data_stores ? var.gcs_data_store_configs : {}

  project           = var.main_project_id
  location          = var.geolocation # Must match the Data Store and Engine location
  data_store_id     = "g4g-gcs-data-store-${random_string.gcs_suffix[each.key].result}"
  display_name      = each.value.display_name != null ? each.value.display_name : each.key
  industry_vertical = local.discovery_engine_industry_vertical
  content_config    = local.discovery_engine_content_config
  solution_types    = local.discovery_engine_solution_types
  kms_key_name      = var.enable_data_store_cmek ? local.cmek_key_id : null
  provider          = google-beta

  document_processing_config {
    default_parsing_config {
      dynamic "digital_parsing_config" {
        for_each = local.discovery_engine_parsing_mode == "digital_parsing_config" ? [1] : []
        content {}
      }
    }
  }

  depends_on = [
    google_kms_crypto_key_iam_member.discoveryengine_sa_kms_access,
    google_kms_crypto_key_iam_member.gcs_sa_kms_access,
    google_project_service.services,
    time_sleep.wait_for_services,
  ]
}

# ---------------------------------------------------------------------------- #
#  Gemini Enterprise - BigQuery Data Stores                                    #
# ---------------------------------------------------------------------------- #

# BQ Dataset for Discovery Engine Data Sources
resource "google_bigquery_dataset" "gemini_enterprise_bq_dataset" {
  for_each = var.create_data_stores ? { for k, v in var.bq_data_store_configs : k => v if v.create_dataset } : {}

  project       = var.main_project_id
  dataset_id    = each.value.dataset_id
  friendly_name = "Gemini Enterprise Data Store - ${each.value.display_name}"
  description   = "Dataset for Gemini Enterprise Data Store - ${each.value.display_name}"
  location      = var.geolocation # Or a more specific region specific location if desired

  dynamic "default_encryption_configuration" {
    for_each = local.cmek_key_id != null ? [1] : []
    content {
      kms_key_name = local.cmek_key_id
    }
  }

  depends_on = [
    google_project_service.services,
    time_sleep.wait_for_services,
    google_kms_crypto_key_iam_member.bq_sa_kms_access
  ]
}

# Random suffix for BQ Data Store IDs
resource "random_string" "bq_suffix" {
  for_each = var.create_data_stores ? var.bq_data_store_configs : {}

  length  = 6
  special = false
  upper   = false
  keepers = {
    industry_vertical = local.discovery_engine_industry_vertical
    solution_types    = join(",", local.discovery_engine_solution_types)
    content_config    = local.discovery_engine_content_config
    kms_key_name      = local.cmek_key_id
    parsing_mode      = local.discovery_engine_parsing_mode
  }
}

# Empty BQ Data Store
resource "google_discovery_engine_data_store" "gemini_enterprise_bq_data_store" {
  for_each = var.create_data_stores ? var.bq_data_store_configs : {}

  project           = var.main_project_id
  location          = var.geolocation # Must match the Data Store and Engine location
  data_store_id     = "g4g-bq-data-store-${random_string.bq_suffix[each.key].result}"
  display_name      = each.value.display_name != null ? each.value.display_name : each.key
  industry_vertical = local.discovery_engine_industry_vertical
  content_config    = "NO_CONTENT"
  solution_types    = local.discovery_engine_solution_types
  kms_key_name      = var.enable_data_store_cmek ? local.cmek_key_id : null
  provider          = google-beta

  document_processing_config {
    default_parsing_config {
      dynamic "digital_parsing_config" {
        for_each = local.discovery_engine_parsing_mode == "digital_parsing_config" ? [1] : []
        content {}
      }
    }
  }

  depends_on = [
    google_kms_crypto_key_iam_member.discoveryengine_sa_kms_access,
    google_kms_crypto_key_iam_member.gcs_sa_kms_access,
    google_kms_crypto_key_iam_member.bq_sa_kms_access,
    google_project_service.services,
    time_sleep.wait_for_services,
  ]
}

# Add a delay to allow the DataStore to be created by the connector
resource "time_sleep" "wait_for_bq_datastore" {
  for_each        = var.create_data_stores ? var.bq_data_store_configs : {}
  create_duration = "30s"
  depends_on      = [google_discovery_engine_data_store.gemini_enterprise_bq_data_store]
}
