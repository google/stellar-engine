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

mock_provider "google" {}
mock_provider "google-beta" {}

override_data {
  target = data.google_project.project
  values = {
    number     = "123456789012"
    project_id = "mock-project-1"
  }
}

variables {
  main_project_id        = "mock-project-1"
  prefix                 = "g4g"
  environment            = "dev"
  tenant                 = "tnt1"
  compliance_regime      = "FEDRAMP_HIGH"
  domain                 = "example.com"
  terraform_state_bucket = "mock-state-bucket"
  access_policy_number   = "123456789012"
  region                 = "us-east4"
  admin_group            = "group:admins@example.com"
  user_groups            = ["group:users@example.com"]
  kms_key_id             = "projects/mock-project-1/locations/us/keyRings/kr/cryptoKeys/key"
  create_data_stores     = false
}

run "default_waf_enforces_blocking_and_allows_us_without_ip_list" {
  command = plan

  assert {
    condition = alltrue([
      for r in google_compute_region_security_policy.gemini_enterprise_policy[0].rules :
      !r.preview if r.priority <= 110
    ])
    error_message = "All Cloud Armor WAF rules and body-size rule must enforce (preview = false) by default."
  }

  assert {
    condition = contains([
      for r in google_compute_region_security_policy.gemini_enterprise_policy[0].rules : r.priority
    ], 2000)
    error_message = "Priority 2000 US geo-allow rule should apply when allowed_ip_ranges is empty."
  }

  assert {
    condition = !contains([
      for r in google_compute_region_security_policy.gemini_enterprise_policy[0].rules : r.priority
    ], 1000)
    error_message = "Priority 1000 IP allow rule must not be present when allowed_ip_ranges is empty."
  }
}

run "ip_allowlist_omits_us_geo_allow_bypass" {
  command = plan

  variables {
    allowed_ip_ranges = ["203.0.113.0/24"]
  }

  assert {
    condition = contains([
      for r in google_compute_region_security_policy.gemini_enterprise_policy[0].rules : r.priority
    ], 1000)
    error_message = "Priority 1000 IP allow rule must be created when allowed_ip_ranges is set."
  }

  assert {
    condition = !contains([
      for r in google_compute_region_security_policy.gemini_enterprise_policy[0].rules : r.priority
    ], 2000)
    error_message = "Priority 2000 US geo-allow rule must be omitted when allowed_ip_ranges is configured to prevent allowlist bypass."
  }
}

run "waf_preview_override_enables_preview_across_rules" {
  command = plan

  variables {
    cloud_armor_waf_preview = true
  }

  assert {
    condition = alltrue([
      for r in google_compute_region_security_policy.gemini_enterprise_policy[0].rules :
      r.preview if r.priority <= 110
    ])
    error_message = "Setting cloud_armor_waf_preview = true must switch WAF and body-limit rules to preview mode."
  }
}

run "null_kms_and_null_state_bucket_plan_cleanly" {
  command = plan

  variables {
    kms_key_id             = null
    terraform_state_bucket = null
    enable_analytics       = false
  }

  assert {
    condition     = length(data.google_storage_bucket.terraform_state) == 0
    error_message = "Null terraform_state_bucket must skip the bucket data lookup instead of crashing."
  }

  assert {
    condition     = output.tf_state_bucket_name == null
    error_message = "tf_state_bucket_name output must be null when terraform_state_bucket is null."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.discoveryengine_sa_kms_access) == 0 && length(google_kms_crypto_key_iam_member.gcs_sa_kms_access) == 0 && length(google_kms_crypto_key_iam_member.bq_sa_kms_access) == 0
    error_message = "Null kms_key_id must skip KMS IAM bindings cleanly."
  }
}

run "analytics_wires_ar_api_regional_cmek_and_dedicated_build_sa" {
  command = plan

  variables {
    enable_analytics     = true
    analytics_kms_key_id = "projects/mock-project-1/locations/us-east4/keyRings/ar-kr/cryptoKeys/ar-key"
  }

  assert {
    condition     = contains(keys(google_project_service.services), "artifactregistry.googleapis.com")
    error_message = "enable_analytics = true must enable artifactregistry.googleapis.com."
  }

  assert {
    condition     = google_bigquery_dataset.analytics_dataset[0].default_encryption_configuration[0].kms_key_name == var.kms_key_id
    error_message = "analytics_dataset must use multi-region kms_key_id for CMEK."
  }

  assert {
    condition     = google_artifact_registry_repository.analytics_repo[0].kms_key_name == var.analytics_kms_key_id
    error_message = "analytics_repo must use regional analytics_kms_key_id for CMEK."
  }

  assert {
    condition     = google_service_account.analytics_build_sa[0].account_id == "g4g-analytics-build-sa"
    error_message = "analytics_build_sa must replace the default Compute Engine service account."
  }
}

run "gcs_buckets_omit_default_delete_lifecycle_and_grant_unimported_iam" {
  command = plan

  variables {
    create_data_stores = true
    gcs_data_store_configs = {
      "imported" = {
        name          = "imported-docs-bucket"
        create_bucket = true
        display_name  = "Imported Docs"
      }
      "existing" = {
        name          = "existing-docs-bucket"
        create_bucket = false
        display_name  = "Existing Docs"
      }
    }
  }

  assert {
    condition     = length(google_storage_bucket.gemini_enterprise_gcs_bucket["imported"].lifecycle_rule) == 0
    error_message = "Managed or imported GCS buckets must not enable a 30-day Delete lifecycle rule by default."
  }

  assert {
    condition     = google_storage_bucket_iam_member.corpus_bucket_discovery_engine["existing"].bucket == "existing-docs-bucket" && google_storage_bucket_iam_member.corpus_bucket_discovery_engine["existing"].role == "roles/storage.objectViewer"
    error_message = "Unimported existing GCS buckets (create_bucket = false) must still grant Discovery Engine roles/storage.objectViewer."
  }
}

run "gcs_lifecycle_delete_age_days_is_opt_in" {
  command = plan

  variables {
    create_data_stores            = true
    gcs_lifecycle_delete_age_days = 30
    gcs_data_store_configs = {
      "ephemeral" = {
        name          = "ephemeral-docs-bucket"
        create_bucket = true
        display_name  = "Ephemeral Docs"
      }
    }
  }

  assert {
    condition     = one(google_storage_bucket.gemini_enterprise_gcs_bucket["ephemeral"].lifecycle_rule[0].condition).age == 30
    error_message = "Explicit gcs_lifecycle_delete_age_days must populate the bucket Delete lifecycle rule."
  }
}

run "acm_defaults_avoid_lockout_and_strict_device_uses_prefixed_levels" {
  command = plan

  assert {
    condition     = length(google_access_context_manager_access_level.lenient_device) == 0 && length(google_access_context_manager_access_level.moderate_device) == 0 && length(google_access_context_manager_access_level.strict_device) == 0
    error_message = "Empty device wrapper access level lists must not create invalid empty ACM access levels."
  }

  assert {
    condition     = output.iap_admin_access_level == null && output.iap_user_access_level == null
    error_message = "IAP access level outputs must be null when no ACM device access levels exist."
  }
}

run "acm_cep_uses_prefixed_levels_and_dynamic_strict_dependencies" {
  command = plan

  variables {
    prefix                           = "my-team"
    enable_chrome_enterprise_premium = true
    create_us_access                 = true
    create_ip_based_access           = false
    create_time_access               = false
    create_expire_access             = false
    create_moderate_device_access    = true
    moderate_device_access_levels    = ["accessPolicies/123456789012/accessLevels/my_team_us"]
  }

  assert {
    condition     = google_access_context_manager_access_level.us[0].name == "accessPolicies/123456789012/accessLevels/my_team_us"
    error_message = "Org ACM access level names must be prefixed with sanitized var.prefix."
  }

  assert {
    condition     = google_access_context_manager_access_level.strict_device[0].name == "accessPolicies/123456789012/accessLevels/my_team_strict_device"
    error_message = "strict_device access level must be prefixed with sanitized var.prefix."
  }

  assert {
    condition = (
      length(google_access_context_manager_access_level.strict_device[0].basic[0].conditions[0].required_access_levels) == 1 &&
      contains(
        google_access_context_manager_access_level.strict_device[0].basic[0].conditions[0].required_access_levels,
        "accessPolicies/123456789012/accessLevels/my_team_us",
      )
    )
    error_message = "strict_device must reference only enabled prefixed levels instead of hardcoded unprefixed us/time/expire."
  }

  assert {
    condition     = output.iap_admin_access_level == "accessPolicies/123456789012/accessLevels/my_team_strict_device"
    error_message = "iap_admin_access_level must emit the prefixed strict_device resource name."
  }
}

run "frh_disables_knowledge_graph_and_defaults_agent_sharing_approval_off" {
  command = plan

  variables {
    compliance_regime = "FEDRAMP_HIGH"
    gemini_apps = {
      "app-1" = {
        display_name = "Test App"
        company_name = "Example Agency"
      }
    }
  }

  assert {
    condition     = google_discovery_engine_search_engine.gemini_enterprise_search_engine["app-1"].features["agent-sharing-without-admin-approval"] == "FEATURE_STATE_OFF"
    error_message = "enable_agent_sharing_without_approval must default to false (FEATURE_STATE_OFF)."
  }

  assert {
    condition     = !google_discovery_engine_search_engine.gemini_enterprise_search_engine["app-1"].knowledge_graph_config[0].enable_private_knowledge_graph && !google_discovery_engine_search_engine.gemini_enterprise_search_engine["app-1"].knowledge_graph_config[0].enable_cloud_knowledge_graph
    error_message = "FedRAMP High must disable Private and Cloud Knowledge Graph on the search engine."
  }
}

run "fedramp_moderate_keeps_knowledge_graph_config_unset" {
  command = plan

  variables {
    compliance_regime = "FEDRAMP_MODERATE"
    gemini_apps = {
      "app-1" = {
        display_name = "Test App"
        company_name = "Example Agency"
      }
    }
  }

  assert {
    condition     = length(google_discovery_engine_search_engine.gemini_enterprise_search_engine["app-1"].knowledge_graph_config) == 0
    error_message = "FedRAMP Moderate must not disable Knowledge Graph."
  }
}
