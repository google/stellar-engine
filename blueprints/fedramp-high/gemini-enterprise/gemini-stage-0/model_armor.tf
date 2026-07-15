# # Copyright 2026 Google LLC
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

locals {
  # Create Model Armor if any app has it enabled,
  # and the compliance regime supports it.
  create_model_armor = anytrue([for k, v in var.gemini_apps : coalesce(v.enable_model_armor, false)]) && (var.compliance_regime == "FEDRAMP_HIGH" || var.compliance_regime == "FEDRAMP_MODERATE" || var.compliance_regime == "NONE")

  # Load Model Armor safety configurations from the local YAML config
  model_armor_config = yamldecode(file("${path.module}/model_armor.yaml"))
}

resource "google_model_armor_template" "model_armor_template" {
  count       = local.create_model_armor ? 1 : 0
  project     = var.main_project_id
  location    = var.geolocation
  template_id = "${var.prefix}-model-armor-template"

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = local.model_armor_config.filter_config.pi_and_jailbreak_filter_settings.filter_enforcement
      confidence_level   = local.model_armor_config.filter_config.pi_and_jailbreak_filter_settings.confidence_level
    }

    malicious_uri_filter_settings {
      filter_enforcement = local.model_armor_config.filter_config.malicious_uri_filter_settings.filter_enforcement
    }

    rai_settings {
      dynamic "rai_filters" {
        for_each = local.model_armor_config.filter_config.rai_settings.rai_filters
        content {
          filter_type      = rai_filters.value.filter_type
          confidence_level = rai_filters.value.confidence_level
        }
      }
    }

    sdp_settings {
      dynamic "basic_config" {
        for_each = lookup(local.model_armor_config.filter_config.sdp_settings, "basic_config", null) != null ? [local.model_armor_config.filter_config.sdp_settings.basic_config] : []
        content {
          filter_enforcement = basic_config.value.filter_enforcement
        }
      }
      dynamic "advanced_config" {
        for_each = lookup(local.model_armor_config.filter_config.sdp_settings, "advanced_config", null) != null ? [local.model_armor_config.filter_config.sdp_settings.advanced_config] : []
        content {
          inspect_template    = advanced_config.value.inspect_template
          deidentify_template = advanced_config.value.deidentify_template
        }
      }
    }
  }

  template_metadata {
    ignore_partial_invocation_failures       = local.model_armor_config.template_metadata.ignore_partial_invocation_failures
    enforcement_type                         = local.model_armor_config.template_metadata.enforcement_type
    custom_prompt_safety_error_code          = local.model_armor_config.template_metadata.custom_prompt_safety_error_code
    custom_prompt_safety_error_message       = local.model_armor_config.template_metadata.custom_prompt_safety_error_message
    custom_llm_response_safety_error_code    = local.model_armor_config.template_metadata.custom_llm_response_safety_error_code
    custom_llm_response_safety_error_message = local.model_armor_config.template_metadata.custom_llm_response_safety_error_message
    log_template_operations                  = local.model_armor_config.template_metadata.log_template_operations
    log_sanitize_operations                  = local.model_armor_config.template_metadata.log_sanitize_operations

    multi_language_detection {
      enable_multi_language_detection = local.model_armor_config.template_metadata.multi_language_detection.enable_multi_language_detection
    }
  }
}
