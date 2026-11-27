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

mock_provider "local" {}

mock_provider "null" {}

mock_provider "time" {}

variables {
  alert_email = "admin@example.com"
  assured_workloads = {
    regime   = "IL5"
    location = "us-east4"
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  bootstrap_project    = "initial-bootstrap-0"
  kms_protection_level = "HSM"
  organization = {
    domain      = "example.com"
    id          = 123456789012
    customer_id = "C00000000"
  }
  prefix = "test"
  regions = {
    primary = "us-east4"
  }
}

run "generated_providers_use_automation_project_for_quota" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_assured_workloads_workload.primary
    override_during = plan
    values = {
      display_name = "StellarEngine-test"
      resources = [
        {
          resource_id   = 111111111111
          resource_type = "CONSUMER_FOLDER"
        }
      ]
    }
  }

  override_resource {
    target          = module.automation-project.google_project.project
    override_during = plan
    values = {
      project_id = "test-prod-iac-core-0"
      number     = "999999999999"
    }
  }

  assert {
    condition     = strcontains(local.providers["0-bootstrap"], "project                     = try(var.billing_override.project, \"test-prod-iac-core-0\")")
    error_message = "Expected 0-bootstrap provider to use automation project ID as quota project."
  }

  assert {
    condition     = !strcontains(local.providers["0-bootstrap"], "initial-bootstrap-0")
    error_message = "0-bootstrap provider must not keep temporary bootstrap_project as quota project."
  }

  assert {
    condition     = strcontains(local.providers["0-bootstrap-r"], "billing_project             = try(var.billing_override.billing_project, \"test-prod-iac-core-0\")")
    error_message = "Expected 0-bootstrap-r provider to use automation project ID as billing_project."
  }

  assert {
    condition     = strcontains(local.providers["1-resman"], "project                     = try(var.billing_override.project, \"test-prod-iac-core-0\")")
    error_message = "Expected 1-resman provider to use automation project ID as quota project."
  }

  assert {
    condition     = strcontains(local.providers["1-resman-r"], "billing_project             = try(var.billing_override.billing_project, \"test-prod-iac-core-0\")")
    error_message = "Expected 1-resman-r provider to use automation project ID as billing_project."
  }

  assert {
    condition     = strcontains(local.providers["0-bootstrap-tenant"], "project                     = try(var.billing_override.project, \"test-prod-iac-core-0\")")
    error_message = "Expected 0-bootstrap-tenant provider to use automation project ID as quota project."
  }

  assert {
    condition = (
      local.automation_project_iam_bindings_additive["serviceusage_bootstrap_r"].role == "roles/serviceusage.serviceUsageConsumer" &&
      local.automation_project_iam_bindings_additive["serviceusage_bootstrap_r"].member == "serviceAccount:test-prod-bootstrap-0r@test-prod-iac-core-0.iam.gserviceaccount.com"
    )
    error_message = "Expected automation project to grant roles/serviceusage.serviceUsageConsumer to bootstrap-0r."
  }

  assert {
    condition = (
      local.automation_project_iam_bindings_additive["serviceusage_resman_r"].role == "roles/serviceusage.serviceUsageConsumer" &&
      local.automation_project_iam_bindings_additive["serviceusage_resman_r"].member == "serviceAccount:test-prod-resman-0r@test-prod-iac-core-0.iam.gserviceaccount.com"
    )
    error_message = "Expected automation project to grant roles/serviceusage.serviceUsageConsumer to resman-0r."
  }
}
