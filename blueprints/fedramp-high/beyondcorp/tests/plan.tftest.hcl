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
  target = module.beyondcorp.data.google_access_context_manager_access_policy.existing_policy
  values = {
    id = "123456789012"
  }
}

variables {
  organization_id     = "123456789012"
  main_project_id     = "my-beyondcorp-project"
  policy_title        = "policy-00"
  oauth_client_id     = "123456789012-exampleclientid.apps.googleusercontent.com"
  oauth_client_secret = "example-client-secret"
  iap_user_email      = "user:admin@example.com"
  endpoint_name       = "accessPolicies/123456789012/accessLevels/endpoint_verified"
  region              = "us-east4"
}

run "plan_beyondcorp" {
  command = plan

  assert {
    condition     = google_project_service.compute_api.service == "compute.googleapis.com"
    error_message = "Expected compute.googleapis.com to be enabled."
  }

  assert {
    condition     = google_project_service.compute_api.project == var.main_project_id
    error_message = "Expected compute.googleapis.com to be enabled on var.main_project_id."
  }

  assert {
    condition     = output.endpoint_name == var.endpoint_name
    error_message = "Expected endpoint_name output to match var.endpoint_name."
  }
}
