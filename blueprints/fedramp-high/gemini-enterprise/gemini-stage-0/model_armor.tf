# Copyright 2026 Google LLC
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
  # Create Model Armor if any app has it enabled,
  # and the compliance regime supports it.
  create_model_armor = anytrue([for k, v in var.gemini_apps : coalesce(v.enable_model_armor, false)]) && (var.compliance_regime == "FEDRAMP_HIGH" || var.compliance_regime == "NONE")
}

# Model Armor Template Configuration
# Complete Reference: https://docs.cloud.google.com/model-armor/reference/rest/v1/projects.locations.templates
# and https://cloud.google.com/python/docs/reference/modelarmor/latest/google.cloud.modelarmor_v1.types.Template

resource "google_model_armor_template" "model_armor_template" {
  count       = local.create_model_armor ? 1 : 0
  project     = var.main_project_id
  location    = var.geolocation
  template_id = "${var.prefix}-model-armor-template"

  # Required. Filter configuration for this template.
  filter_config {
    # Prompt Injection and Jailbreak Filter Settings
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"          # Options: ENABLED, DISABLED, PI_AND_JAILBREAK_FILTER_ENFORCEMENT_UNSPECIFIED
      confidence_level   = "MEDIUM_AND_ABOVE" # Options: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH, DETECTION_CONFIDENCE_LEVEL_UNSPECIFIED
    }

    # Malicious URI Filter Settings
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED" # Options: ENABLED, DISABLED, MALICIOUS_URI_FILTER_ENFORCEMENT_UNSPECIFIED
    }

    # Responsible AI (RAI) Filter Settings
    rai_settings {
      rai_filters {
        filter_type      = "HATE_SPEECH" # Options: SEXUALLY_EXPLICIT, HATE_SPEECH, HARASSMENT, DANGEROUS, RAI_FILTER_TYPE_UNSPECIFIED
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "HARASSMENT"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "SEXUALLY_EXPLICIT"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "DANGEROUS"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
    }

    # Sensitive Data Protection (SDP) Settings
    # Note: You can use either basic_config or advanced_config (mutually exclusive).
    sdp_settings {
      # Basic inspection using a fixed set of six info-types.
      basic_config {
        filter_enforcement = "ENABLED" # Options: ENABLED, DISABLED, SDP_BASIC_CONFIG_ENFORCEMENT_UNSPECIFIED
      }

      # To use advanced SDP templates (supporting inspection and de-identification) instead of basic_config,
      # comment out basic_config above and uncomment advanced_config below:
      # advanced_config {
      #   inspect_template    = "projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/inspectTemplates/YOUR_INSPECT_TEMPLATE_ID"
      #   deidentify_template = "projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/deidentifyTemplates/YOUR_DEIDENTIFY_TEMPLATE_ID"
      # }
    }
  }

  # Optional. Metadata and operational settings for this template.
  template_metadata {
    # If true, partial detector failures should be ignored.
    ignore_partial_invocation_failures = false

    # Enforcement type for Model Armor filters.
    enforcement_type = "INSPECT_AND_BLOCK" # Options: ENFORCEMENT_TYPE_UNSPECIFIED (default, same as INSPECT_AND_BLOCK), INSPECT_ONLY, INSPECT_AND_BLOCK

    # Custom error code and message returned to the end user by service extensions if the user prompt trips filters.
    custom_prompt_safety_error_code    = 403
    custom_prompt_safety_error_message = "Your prompt was blocked by security policies."

    # Custom error code and message returned to the end user if the LLM response trips filters.
    custom_llm_response_safety_error_code    = 403
    custom_llm_response_safety_error_message = "The generated response was blocked by security policies."

    # Logging configuration for template CRUD operations and sanitization requests.
    log_template_operations = true
    log_sanitize_operations = true

    # Multi-language detection settings.
    multi_language_detection {
      enable_multi_language_detection = true
    }
  }
}
