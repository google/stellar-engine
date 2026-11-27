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

mock_provider "google" {}

mock_provider "google-beta" {}

variables {
  main_project_id = "my-project"
  region          = "us-east4"
}

run "default_rules_enforce_waf_before_rate_limiting_and_default_deny" {
  command = plan

  variables {
    rules_file = "rules.yaml"
  }

  assert {
    condition     = google_compute_region_security_policy_rule.policy_rule["gitlab-waf-policy-1006"].action == "throttle"
    error_message = "Expected login throttle rule at priority 1006."
  }

  assert {
    condition     = strcontains(google_compute_region_security_policy_rule.policy_rule["gitlab-waf-policy-1006"].match[0].expr[0].expression, "urlDecodeUni().lower()")
    error_message = "Login rate limit rule must normalize URL encoding and case."
  }

  assert {
    condition     = google_compute_region_security_policy_rule.policy_rule["gitlab-waf-policy-1007"].action == "throttle" && toset(google_compute_region_security_policy_rule.policy_rule["gitlab-waf-policy-1007"].match[0].config[0].src_ip_ranges) == toset(["10.0.0.0/8"])
    error_message = "General throttle rule in gitlab-waf-policy must scope src_ip_ranges rather than wildcard."
  }

  assert {
    condition     = google_compute_region_security_policy_rule.policy_rule["gitlab-waf-policy-1008"].action == "deny(403)" && toset(google_compute_region_security_policy_rule.policy_rule["gitlab-waf-policy-1008"].match[0].config[0].src_ip_ranges) == toset(["*"])
    error_message = "gitlab-waf-policy must end with a reachable Default Deny rule."
  }

  assert {
    condition     = google_compute_region_security_policy_rule.policy_rule["policy-two-1001"].action == "deny(403)" && google_compute_region_security_policy_rule.policy_rule["policy-two-1001"].match[0].expr[0].expression == "evaluatePreconfiguredWaf('nodejs-v33-stable')"
    error_message = "policy-two must evaluate nodejs-v33-stable deny rule before rate limiting."
  }

  assert {
    condition     = google_compute_region_security_policy_rule.policy_rule["policy-two-1002"].action == "rate_based_ban" && toset(google_compute_region_security_policy_rule.policy_rule["policy-two-1002"].match[0].config[0].src_ip_ranges) == toset(["10.0.0.0/16"])
    error_message = "policy-two rate_based_ban rule must be scoped to explicit src_ip_ranges."
  }

  assert {
    condition     = google_compute_region_security_policy_rule.policy_rule["policy-two-1003"].action == "deny(403)" && toset(google_compute_region_security_policy_rule.policy_rule["policy-two-1003"].match[0].config[0].src_ip_ranges) == toset(["*"])
    error_message = "policy-two must end with a reachable Default Deny rule."
  }
}

run "reject_wildcard_throttle_shadowing_default_deny" {
  command = plan

  variables {
    rules_file = "tests/fixtures/shadowing.yaml"
  }

  expect_failures = [
    google_compute_region_security_policy_rule.policy_rule,
  ]
}
