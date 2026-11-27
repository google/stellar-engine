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

override_data {
  target = module.access-context-manager.data.google_access_context_manager_access_policy.policy
  values = {
    id = "123456789012"
  }
}

variables {
  organization_id = "123456789012"
  region          = "us-east4"
  main_project_id = "my-acm-project"
  access_levels = [
    {
      name        = "accessPolicies/123456789012/accessLevels/corp_network"
      description = "Access only from the company network."
      conditions = [
        {
          ip_subnetworks = ["203.0.113.0/24"]
          members        = ["user:admin@example.com"]
          negate         = false
          device_policy = {
            require_screen_lock = true
          }
          regions = ["US"]
        }
      ]
    }
  ]
  service_perimeters = [
    {
      name        = "accessPolicies/123456789012/servicePerimeters/gcs_perimeter"
      description = "Perimeter for accessing GCS buckets."
      status = {
        restricted_services = ["storage.googleapis.com"]
        resources           = ["projects/123456789012"]
      }
    }
  ]
}

run "plan_without_unused_legacy_vars" {
  command = plan

  assert {
    condition     = contains(keys(output.access_levels), "accessPolicies/123456789012/accessLevels/corp_network")
    error_message = "Expected corp_network access level output to be keyed by its full resource name."
  }

  assert {
    condition     = output.access_levels["accessPolicies/123456789012/accessLevels/corp_network"].description == "Access only from the company network."
    error_message = "Expected access level description to match variable input."
  }

  assert {
    condition     = contains(keys(output.service_perimeters), "accessPolicies/123456789012/servicePerimeters/gcs_perimeter")
    error_message = "Expected gcs_perimeter service perimeter output to be keyed by its full resource name."
  }
}

run "plan_with_optional_device_policy_omitted" {
  command = plan

  variables {
    access_levels = [
      {
        name        = "accessPolicies/123456789012/accessLevels/corp_ip_only"
        description = "Access only from corporate IP ranges."
        conditions = [
          {
            ip_subnetworks = ["203.0.113.0/24"]
            members        = ["user:admin@example.com"]
            negate         = false
            regions        = ["US"]
          }
        ]
      }
    ]
  }

  assert {
    condition     = contains(keys(output.access_levels), "accessPolicies/123456789012/accessLevels/corp_ip_only")
    error_message = "Expected plan to succeed when optional device_policy is omitted."
  }
}
