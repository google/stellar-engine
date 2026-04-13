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
#  Gemini Enterprise - Datastore CMEK Config                                   #
# ---------------------------------------------------------------------------- #

# CMEK Configuration for Discovery Engine (Conditional)
# resource "google_discovery_engine_cmek_config" "default" {
#   count = var.create_data_stores && var.enable_data_store_cmek ? 1 : 0

#   project        = var.main_project_id
#   location       = var.geolocation # should be "US"
#   cmek_config_id = "default_cmek_config"
#   kms_key        = local.cmek_key_id
#   set_default    = true
#   provider       = google-beta

#   depends_on = [
#     google_kms_crypto_key_iam_member.discoveryengine_sa_kms_access,
#     google_kms_crypto_key_iam_member.gcs_sa_kms_access,
#     google_project_service.services,
#     time_sleep.wait_for_services,
#   ]
# }

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
#  Gemini Enterprise - Application                                             #
# ---------------------------------------------------------------------------- #

# import {
#   for_each = var.gemini_apps
#   id       = "projects/${var.main_project_id}/locations/${var.geolocation}/collections/default_collection/engines/${each.key}"
#   to       = google_discovery_engine_search_engine.gemini_enterprise_search_engine[each.key]
# }

# resource "google_discovery_engine_search_engine" "gemini_enterprise_search_engine" {
#   for_each      = var.gemini_apps
#   project       = var.main_project_id
#   engine_id     = each.key
#   collection_id = "default_collection"
#   location      = var.geolocation
#   display_name  = each.value.display_name
#   data_store_ids = each.value.data_store_id != "" ? [
#     try(
#       google_discovery_engine_data_store.gemini_enterprise_gcs_data_store[each.value.data_store_id].data_store_id,
#       google_discovery_engine_data_store.gemini_enterprise_bq_data_store[each.value.data_store_id].data_store_id,
#       each.value.data_store_id
#     )
#   ] : []
#   industry_vertical = "GENERIC"
#   app_type          = "APP_TYPE_INTRANET"
#   disable_analytics = true
#   kms_key_name      = var.enable_data_store_cmek ? local.cmek_key_id : null
#   search_engine_config {
#     search_tier = "SEARCH_TIER_ENTERPRISE"
#     search_add_ons = [
#       "SEARCH_ADD_ON_LLM"
#     ]
#   }
#   common_config {
#     company_name = each.value.company_name
#   }
#   knowledge_graph_config {}
#   features = {
#     agent-gallery                        = "FEATURE_STATE_ON"
#     no-code-agent-builder                = "FEATURE_STATE_ON"
#     prompt-gallery                       = "FEATURE_STATE_OFF"
#     model-selector                       = "FEATURE_STATE_ON"
#     notebook-lm                          = "FEATURE_STATE_OFF"
#     people-search                        = "FEATURE_STATE_OFF"
#     people-search-org-chart              = "FEATURE_STATE_OFF"
#     bi-directional-audio                 = "FEATURE_STATE_OFF"
#     feedback                             = "FEATURE_STATE_OFF"
#     session-sharing                      = "FEATURE_STATE_OFF"
#     personalization-memory               = "FEATURE_STATE_OFF"
#     personalization-suggested-highlights = "FEATURE_STATE_OFF"
#     disable-agent-sharing                = "FEATURE_STATE_ON"
#     agent-sharing-without-admin-approval = "FEATURE_STATE_OFF"
#     disable-image-generation             = "FEATURE_STATE_ON"
#     disable-video-generation             = "FEATURE_STATE_ON"
#     disable-onedrive-upload              = "FEATURE_STATE_ON"
#     disable-talk-to-content              = "FEATURE_STATE_OFF"
#     disable-google-drive-upload          = "FEATURE_STATE_ON"
#     disable-welcome-emails               = "FEATURE_STATE_OFF"
#   }
# }

# ---------------------------------------------------------------------------- #
#  Gemini Enterprise - Default Assistant                                       #
# ---------------------------------------------------------------------------- #

# import {
#   for_each = var.gemini_apps
#   id       = "projects/${var.main_project_id}/locations/${var.geolocation}/collections/default_collection/engines/${google_discovery_engine_search_engine.gemini_enterprise_search_engine[each.key].engine_id}/assistants/default_assistant"
#   to       = google_discovery_engine_assistant.gemini_enterprise_default_assistant[each.key]
# }

# resource "google_discovery_engine_assistant" "gemini_enterprise_default_assistant" {
#   for_each      = var.gemini_apps
#   project       = var.main_project_id
#   location      = var.geolocation
#   collection_id = "default_collection"
#   engine_id     = google_discovery_engine_search_engine.gemini_enterprise_search_engine[each.key].engine_id
#   assistant_id  = "default_assistant"
#   display_name  = "Gemini Enterprise Default Assistant"
#   generation_config {
#     default_language = "en"
#   }
#   web_grounding_type = "WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH"
# }

# ---------------------------------------------------------------------------- #
#  Gemini Enterprise - Widget Config                                           #
# ---------------------------------------------------------------------------- #

# resource "google_discovery_engine_widget_config" "gemini_enterprise_widget_config" {
#   for_each  = var.gemini_apps
#   project   = var.main_project_id
#   location  = var.geolocation
#   engine_id = google_discovery_engine_search_engine.gemini_enterprise_search_engine[each.key].engine_id
#   dynamic "access_settings" {
#     for_each = var.acl_workforce_pool_name != "" && var.acl_workforce_provider_id != "" ? [1] : []
#     content {
#       enable_web_app                   = true
#       workforce_identity_pool_provider = "${var.acl_workforce_pool_name}/providers/${var.acl_workforce_provider_id}"
#     }
#   }
#   ui_settings {
#     generative_answer_config {
#       language_code = "en"
#     }
#     enable_autocomplete            = true
#     enable_quality_feedback        = false
#     disable_user_events_collection = true
#     enable_people_search           = false
#   }
# }

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
    # google_discovery_engine_cmek_config.default,
    google_kms_crypto_key_iam_member.discoveryengine_sa_kms_access,
    google_kms_crypto_key_iam_member.gcs_sa_kms_access,
    google_project_service.services,
    time_sleep.wait_for_services,
    time_sleep.wait_for_gcs_iam,
  ]
}

# Grant Storage Admin to Discovery Engine SA if GCS Data Stores are present
resource "google_project_iam_member" "discoveryengine_sa_gcs_admin" {
  count   = var.create_data_stores && length(var.gcs_data_store_configs) > 0 ? 1 : 0
  project = var.main_project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_project_service_identity.discoveryengine.email}"
}

# Wait for IAM propagation before creating Data store which triggers doc import
resource "time_sleep" "wait_for_gcs_iam" {
  count           = var.create_data_stores && length(var.gcs_data_store_configs) > 0 ? 1 : 0
  create_duration = "60s"
  depends_on      = [google_project_iam_member.discoveryengine_sa_gcs_admin]
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
    # google_discovery_engine_cmek_config.default,
    google_kms_crypto_key_iam_member.discoveryengine_sa_kms_access,
    google_kms_crypto_key_iam_member.gcs_sa_kms_access,
    google_kms_crypto_key_iam_member.bq_sa_kms_access,
    google_project_service.services,
    time_sleep.wait_for_services,
    time_sleep.wait_for_bq_iam,
  ]
}

# Add a delay to allow the DataStore to be created by the connector
resource "time_sleep" "wait_for_bq_datastore" {
  for_each        = var.create_data_stores ? var.bq_data_store_configs : {}
  create_duration = "30s"
  depends_on      = [google_discovery_engine_data_store.gemini_enterprise_bq_data_store]
}

# Grant BigQuery Admin to Discovery Engine SA if BigQuery Data Stores are present
resource "google_project_iam_member" "discoveryengine_sa_bq_admin" {
  count   = var.create_data_stores && length(var.bq_data_store_configs) > 0 ? 1 : 0
  project = var.main_project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_project_service_identity.discoveryengine.email}"
}

# Wait for IAM propagation before creating Data store which triggers schema fetch/import
resource "time_sleep" "wait_for_bq_iam" {
  count           = var.create_data_stores && length(var.bq_data_store_configs) > 0 ? 1 : 0
  create_duration = "60s"
  depends_on      = [google_project_iam_member.discoveryengine_sa_bq_admin]
}
