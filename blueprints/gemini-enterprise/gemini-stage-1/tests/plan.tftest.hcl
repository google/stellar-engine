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

override_data {
  target = data.google_compute_region_backend_service.gemini_enterprise_backend
  values = {
    id   = "projects/mock-proj-1/regions/us-east4/backendServices/g4g-backend-service"
    name = "g4g-backend-service"
  }
}

override_data {
  target = data.google_compute_network.gemini_enterprise_vpc
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/mock-proj-1/global/networks/g4g-vpc"
  }
}

override_data {
  target = data.google_compute_address.gemini_enterprise_ip
  values = {
    address = "198.51.100.10"
  }
}

override_data {
  target = data.google_compute_region_ssl_certificate.gemini_enterprise_cert
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/mock-proj-1/regions/us-east4/sslCertificates/cert-1"
  }
}

variables {
  gemini_enterprise_domain = "gemini.example.com"
  stage_0_state_bucket     = "mock-state-bucket"
  ssl_certificate_name     = "cert-1"
}

run "iap_omits_acm_condition_when_stage0_access_levels_are_null" {
  command = plan

  override_data {
    target = data.terraform_remote_state.stage_0
    values = {
      outputs = {
        main_project_id                  = "mock-proj-1"
        region                           = "us-east4"
        prefix                           = "g4g"
        deployment_type                  = "external"
        use_shared_vpc                   = false
        acl_idp_type                     = "GOOGLE_CLOUD_IDENTITY"
        gemini_apps_widget_ids           = { "app-1" = "cfg-1" }
        admin_group                      = "group:admins@example.com"
        user_groups                      = ["group:users@example.com"]
        access_policy_number             = "123456789012"
        enable_chrome_enterprise_premium = false
        iap_admin_access_level           = null
        iap_user_access_level            = null
      }
    }
  }

  assert {
    condition     = length(google_iap_web_region_backend_service_iam_member.iap_admin[0].condition) == 0
    error_message = "IAP admin binding must omit ACM condition when Stage 0 iap_admin_access_level is null."
  }

  assert {
    condition     = length(google_iap_web_region_backend_service_iam_member.iap_user["group:users@example.com"].condition) == 0
    error_message = "IAP user binding must omit ACM condition when Stage 0 iap_user_access_level is null."
  }
}

run "iap_attaches_prefixed_acm_conditions_from_stage0_outputs" {
  command = plan

  override_data {
    target = data.terraform_remote_state.stage_0
    values = {
      outputs = {
        main_project_id                  = "mock-proj-1"
        region                           = "us-east4"
        prefix                           = "my-team"
        deployment_type                  = "external"
        use_shared_vpc                   = false
        acl_idp_type                     = "GOOGLE_CLOUD_IDENTITY"
        gemini_apps_widget_ids           = { "app-1" = "cfg-1" }
        admin_group                      = "group:admins@example.com"
        user_groups                      = ["group:users@example.com"]
        access_policy_number             = "123456789012"
        enable_chrome_enterprise_premium = true
        iap_admin_access_level           = "accessPolicies/123456789012/accessLevels/my_team_strict_device"
        iap_user_access_level            = "accessPolicies/123456789012/accessLevels/my_team_moderate_device"
      }
    }
  }

  assert {
    condition     = google_iap_web_region_backend_service_iam_member.iap_admin[0].condition[0].expression == "\"accessPolicies/123456789012/accessLevels/my_team_strict_device\" in request.auth.access_levels"
    error_message = "IAP admin binding must use the resolved prefixed Stage 0 iap_admin_access_level."
  }

  assert {
    condition     = google_iap_web_region_backend_service_iam_member.iap_user["group:users@example.com"].condition[0].expression == "\"accessPolicies/123456789012/accessLevels/my_team_moderate_device\" in request.auth.access_levels"
    error_message = "IAP user binding must use the resolved prefixed Stage 0 iap_user_access_level."
  }
}
