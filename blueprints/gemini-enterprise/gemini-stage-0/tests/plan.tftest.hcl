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
